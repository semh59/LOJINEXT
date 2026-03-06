from sqlalchemy import text
from app.infrastructure.events.event_bus import Event, EventType, get_event_bus
from app.infrastructure.logging.logger import get_logger
from app.database.unit_of_work import UnitOfWork

logger = get_logger(__name__)


async def handle_fuel_added_for_period(event: Event) -> None:
    """
    YAKIT_ADDED olayını yakala ve Full-to-Full periyot hesapla.
    """
    data = event.data
    yakit_id = data.get("id")
    arac_id = data.get("arac_id")

    if not yakit_id or not arac_id:
        return

    logger.info(f"Yakıt Periyodu Hesaplanıyor: Yakit {yakit_id}, Arac {arac_id}")

    try:
        async with UnitOfWork() as uow:
            # 1. Mevcut yakıt kaydını getir
            query_curr = "SELECT * FROM yakit_alimlari WHERE id = :id"
            row_curr = await uow.session.execute(text(query_curr), {"id": yakit_id})
            curr = row_curr.fetchone()

            if not curr:
                return

            # EĞER DEPO FULL DEĞİLSE PERİYOT KAPATILAMAZ
            # Partial fill sisteminde tüketim sadece Full -> Full arasında hesaplanır.
            # "Full" veya "Dolu" ibaresi aranır.
            depo_durumu = str(curr.depo_durumu or "").lower()
            if "full" not in depo_durumu and "dolu" not in depo_durumu:
                logger.info(
                    f"Kısmi Dolum ({curr.litre} L) - Periyot hesaplanmadı. (Depo: {curr.depo_durumu})"
                )
                return

            # 2. Bir önceki "FULL" kaydı bul
            query_prev_full = """
                SELECT * FROM yakit_alimlari 
                WHERE arac_id = :arac_id 
                  AND id < :curr_id 
                  AND aktif = TRUE
                  AND (LOWER(depo_durumu) LIKE '%full%' OR LOWER(depo_durumu) LIKE '%dolu%')
                ORDER BY km_sayac DESC
                LIMIT 1
            """
            row_prev = await uow.session.execute(
                text(query_prev_full), {"arac_id": arac_id, "curr_id": yakit_id}
            )
            prev = row_prev.fetchone()

            if not prev:
                logger.info(
                    f"Önceki Full dolum bulunamadı. Döngü başlatıldı: {curr.km_sayac}"
                )
                return

            # 3. Aradaki tüm yakıtları topla (Prev < x <= Curr)
            # Bu döngüdeki toplam tüketilen yakıt = (Ara alımlar) + (Şu anki Full dolum)
            # Çünkü "Full"lediğimizde depoya giren yakıt, son "Full"den bu yana harcanan yakıttır.
            query_sum = """
                SELECT SUM(litre) as total_litres 
                FROM yakit_alimlari 
                WHERE arac_id = :arac_id 
                  AND id > :prev_id 
                  AND id <= :curr_id
                  AND aktif = TRUE
            """
            row_sum = await uow.session.execute(
                text(query_sum),
                {"arac_id": arac_id, "prev_id": prev.id, "curr_id": yakit_id},
            )
            total_litres = float(row_sum.scalar() or 0.0)

            # 4. Mesafe ve Tüketim Hesapla
            mesafe = curr.km_sayac - prev.km_sayac
            if mesafe <= 0:
                logger.warning(f"Geçersiz KM farkı ({mesafe}) - Period atlandı")
                return

            if total_litres <= 0:
                return

            tuketim = (total_litres / mesafe) * 100

            # 5. YakitPeriyodu Kaydet (Cycle)
            insert_query = """
                INSERT INTO yakit_periyotlari 
                (arac_id, alim1_id, alim2_id, alim1_tarih, alim1_km, alim1_litre, 
                 alim2_tarih, alim2_km, ara_mesafe, toplam_yakit, ort_tuketim, durum)
                VALUES 
                (:arac_id, :a1, :a2, :t1, :k1, :l1, :t2, :k2, :dist, :total, :avg, :status)
                ON CONFLICT (arac_id, alim1_id, alim2_id) DO NOTHING
            """
            params = {
                "arac_id": arac_id,
                "a1": prev.id,
                "a2": curr.id,
                "t1": prev.tarih,
                "k1": prev.km_sayac,
                "l1": float(prev.litre),
                "t2": curr.tarih,
                "k2": curr.km_sayac,
                "dist": mesafe,
                "total": total_litres,
                "avg": round(tuketim, 2),
                "status": "Full-to-Full",
            }

            await uow.session.execute(text(insert_query), params)
            await uow.commit()

            logger.info(
                f"Full-to-Full Cycle Kaydedildi: {tuketim:.2f} L/100km ({mesafe} km, {total_litres} L)"
            )

    except Exception as e:
        logger.error(f"Periyot hesaplama hatası: {e}", exc_info=True)


def register_period_handlers():
    """Handler'ı EventBus'a kaydet"""
    bus = get_event_bus()
    bus.subscribe(EventType.YAKIT_ADDED, handle_fuel_added_for_period)
    logger.info("Period handlers registered")
