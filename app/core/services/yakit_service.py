"""
TIR Yakıt Takip Sistemi - Yakıt Servisi
İş mantığı katmanı: Yakıt alım işlemleri
"""

from datetime import date
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.database.repositories.yakit_repo import YakitRepository

from app.core.entities.models import YakitAlimi, YakitAlimiCreate, YakitUpdate
from app.database.repositories.yakit_repo import get_yakit_repo
from app.database.unit_of_work import UnitOfWork
from app.infrastructure.audit import audit_log
from app.infrastructure.events.event_bus import (
    Event,
    EventBus,
    EventType,
    get_event_bus,
    publishes,
)
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class YakitService:
    """
    Yakıt alım işlemleri iş mantığı.
    UI ve DB arasında köprü görevi görür.
    """

    def __init__(
        self,
        repo: Optional["YakitRepository"] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.repo = repo or get_yakit_repo()
        self.event_bus = event_bus or get_event_bus()

    async def _check_rolling_outlier(
        self, arac_id: int, current_litre: float, current_km: int
    ) -> bool:
        """
        Kısmi Dolumlar İçin Rolling Outlier Check (Son 5 Kayıt)
        Tekil kayıt yerine, son 5 kaydın ortalamasına bakar.
        """
        try:
            # Son 5 kaydı çek (Repository'de bu metod yoksa raw query kullanacağız)
            # Performans için sadece gerekli alanlar
            async with UnitOfWork() as uow:
                query = """
                    SELECT litre, km_sayac FROM yakit_alimlari 
                    WHERE arac_id = :arac_id AND aktif = TRUE 
                    ORDER BY km_sayac DESC 
                    LIMIT 5
                """
                from sqlalchemy import text

                result = await uow.session.execute(text(query), {"arac_id": arac_id})
                last_5 = result.fetchall()

            if not last_5:
                return False

            # Mevcut veriyi de listeye ekle (Hesaplamaya dahil olsun)
            # last_5 verisi DB'den geliyor, şu an eklemekte olduğumuz veri henüz DB'de yoksa commit öncesi çağrıldığı için manuel ekleriz.
            # Ancak bu metod commit öncesi çağrılıyor.

            # Veri Hazırlığı
            litres = [current_litre] + [float(r.litre) for r in last_5]
            kms = [current_km] + [int(r.km_sayac) for r in last_5]

            # En yeni ve en eski KM arasındaki fark
            # Listeler DESC order (en yeni en başta)
            total_dist = max(kms) - min(kms)
            # HAYIR: Rolling Window mantığı:
            # Camın içindeki toplam yakıt / Camın kapsadığı mesafe.
            # KM: 1000 -> 1200 -> 1500
            # Litre: 50 -> 60
            # Mesafe: 1500 - 1000 = 500. Yakıt: 50+60 = 110. Ort: (110/500)*100 = 22.
            # Yani en eski kaydın KM'si "başlangıç" kabul edilir, o kaydın litresi "o km'ye gelmek için harcanan" olduğu için DAHİL EDİLMEZ.

            if len(kms) < 2 or total_dist <= 0:
                return False

            # Penceredeki geçerli yakıt toplamı (En eski kaydın litresi hariç)
            # Çünkü en eski kaydın litresi, o kayıttan önceki sürüşe aittir.
            valid_fuel = sum(litres) - float(last_5[-1].litre)

            if valid_fuel <= 0:
                return False

            rolling_avg = (valid_fuel / total_dist) * 100

            # Smart Thresholds (TIR için 20-50 arası normal, dışı anomali)
            if rolling_avg < 18 or rolling_avg > 55:
                # Log only, don't spam events yet until tuned
                logger.warning(
                    f"Rolling Anomaly ({len(kms)} fills): Arac {arac_id}, {rolling_avg:.1f} L/100km (Dist: {total_dist})"
                )

                self.event_bus.publish(
                    Event(
                        type=EventType.ANOMALY_DETECTED,
                        data={
                            "arac_id": arac_id,
                            "tip": "rolling_consumption",
                            "deger": rolling_avg,
                            "window_size": len(kms),
                            "total_dist": total_dist,
                        },
                    )
                )
                return True

        except Exception as e:
            logger.error(f"Rolling outlier check error: {e}")

        return False

    @publishes(EventType.YAKIT_ADDED)
    async def add_yakit(self, data: YakitAlimiCreate) -> int:
        """
        Yeni yakıt alımı ekle.
        """
        try:
            async with UnitOfWork() as uow:
                # Business Rules
                arac = await uow.arac_repo.get_by_id(data.arac_id)
                if not arac or not arac.get("aktif"):
                    raise ValueError(
                        "Pasif veya geçersiz bir araç için yakıt girişi yapılamaz."
                    )

                if data.litre <= 0:
                    raise ValueError("Litre 0'dan büyük olmalıdır")

                if data.fiyat_tl <= 0:
                    raise ValueError("Fiyat 0'dan büyük olmalıdır")

                # Future date check
                entry_date = (
                    data.tarih
                    if isinstance(data.tarih, date)
                    else date.fromisoformat(data.tarih)
                )
                if entry_date > date.today():
                    raise ValueError("İleri tarihli yakıt girişi yapılamaz")

                # Duplicate Check (Elite Guard)
                is_duplicate = await uow.yakit_repo.check_duplicate(
                    data.arac_id, entry_date, float(data.litre)
                )
                if is_duplicate:
                    logger.warning(
                        f"Mükerrer yakıt girişi engellendi: Arac {data.arac_id}, Tarih {entry_date}, Litre {data.litre}"
                    )
                    raise ValueError(
                        "Bu yakıt alım kaydı zaten mevcut (Mükerrer Kayıt)."
                    )

                # Son km kontrolü
                last_km = await uow.yakit_repo.get_son_km(data.arac_id)
                if last_km and data.km_sayac < last_km:
                    raise ValueError(
                        f"KM Sayacı düşemez! (Son: {last_km}, Girilen: {data.km_sayac})"
                    )

                # Outlier Kontrolü (Rolling Average)
                if last_km:
                    await self._check_rolling_outlier(
                        data.arac_id, float(data.litre), data.km_sayac
                    )

                # DB Insert via Repository
                yakit_id = await uow.yakit_repo.add(
                    tarih=entry_date,
                    arac_id=data.arac_id,
                    istasyon=data.istasyon,
                    fiyat=float(data.fiyat_tl),
                    litre=float(data.litre),
                    km_sayac=data.km_sayac,
                    fis_no=data.fis_no,
                    depo_durumu=data.depo_durumu or "Bilinmiyor",
                    toplam_tutar=data.toplam_tutar
                    if data.toplam_tutar is not None and data.toplam_tutar > 0
                    else float(data.litre) * float(data.fiyat_tl),
                )

                # UoW commit - veriyi kalıcı kaydet
                await uow.commit()

                logger.info(f"Yakit alimi eklendi: ID {yakit_id}, Arac {data.arac_id}")
                return int(yakit_id)

        except Exception as e:
            logger.error(f"Yakit ekleme hatasi: {e}", exc_info=True)
            raise

    @audit_log("UPDATE", "yakit")
    @publishes(EventType.YAKIT_UPDATED)
    async def update_yakit(self, yakit_id: int, data: YakitUpdate) -> bool:
        """Yakıt kaydı güncelle (Atomik)"""
        try:
            async with UnitOfWork() as uow:
                # Lock record before update to prevent lost updates
                current = await uow.yakit_repo.get_by_id(yakit_id, for_update=True)
                if not current:
                    return False

                update_data = data.model_dump(exclude_unset=True)
                if not update_data:
                    return True

                success = await uow.yakit_repo.update_yakit(yakit_id, **update_data)
                if success:
                    await uow.commit()
                    logger.info(f"Yakit kaydi guncellendi: ID {yakit_id}")
                return bool(success)
        except Exception as e:
            logger.error(f"Yakit guncelleme hatasi: {e}")
            raise

    @publishes(EventType.YAKIT_DELETED)
    async def delete_yakit(self, yakit_id: int) -> bool:
        """Yakıt kaydı sil (Hard Delete - Atomik)"""
        try:
            async with UnitOfWork() as uow:
                current = await uow.yakit_repo.get_by_id(yakit_id)
                if not current:
                    return False

                # USER REQUIRED: Hard Delete (No traces left)
                success = await uow.yakit_repo.hard_delete(yakit_id)
                if success:
                    await uow.commit()
                    logger.info(f"Yakit tamamen silindi (Hard Deleted): ID {yakit_id}")
                return bool(success)

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Yakit silme hatasi: {e}")
            raise ValueError("Yakıt silinirken bir hata oluştu.")

    async def add_yakit_alimi(self, **kwargs: Any) -> int:
        """Alias for add_yakit (backward compatibility)"""
        # Convert dict to model if kwargs provided
        if kwargs:
            try:
                # kwargs içinde tarih varsa ve date objesi ise string'e çevirme (model validator halleder)
                # Pydantic model ile validasyon
                data = YakitAlimiCreate(**kwargs)
                return await self.add_yakit(data)
            except Exception as e:
                logger.error(f"Yakit ekleme hatasi (alias): {e}")
                raise
        raise ValueError("No data provided")

    async def get_yakit_by_id(self, yakit_id: int) -> Optional[YakitAlimi]:
        """Yakıt alımı detaylarını getir"""
        async with UnitOfWork() as uow:
            record = await uow.yakit_repo.get_by_id(yakit_id)
            if not record:
                return None
            return YakitAlimi.model_validate(dict(record))

    async def get_by_vehicle(self, arac_id: int, limit: int = 50) -> List[YakitAlimi]:
        """Araç yakıt geçmişini getir"""
        async with UnitOfWork() as uow:
            records = await uow.yakit_repo.get_all(arac_id=arac_id, limit=limit)
        return [YakitAlimi.model_validate(dict(r)) for r in records]

    async def get_all_paged(
        self, skip: int = 0, limit: int = 100, aktif_only: bool = True, **filters: Any
    ) -> List[YakitAlimi]:
        """
        Sayfalı ve filtreli yakıt listesi (Güvenli Katman).
        Bozuk verileri sessizce atlayarak listeyi korur.
        """
        from datetime import date

        # Tarih filtrelerini asıl tiplerine çevir (Date objesi)
        if filters.get("baslangic_tarih") and isinstance(
            filters["baslangic_tarih"], str
        ):
            try:
                filters["baslangic_tarih"] = date.fromisoformat(
                    filters["baslangic_tarih"]
                )
            except ValueError:
                pass

        if filters.get("bitis_tarih") and isinstance(filters["bitis_tarih"], str):
            try:
                filters["bitis_tarih"] = date.fromisoformat(filters["bitis_tarih"])
            except ValueError:
                pass

        async with UnitOfWork() as uow:
            paged_data = await uow.yakit_repo.get_all(
                offset=skip, limit=limit, include_inactive=not aktif_only, **filters
            )

        records = paged_data.get("items", [])
        total_count = paged_data.get("total", 0)

        results = []
        for r in records:
            try:
                results.append(YakitAlimi.model_validate(dict(r)))
            except Exception as e:
                logger.error(f"Yakit validasyon hatasi (ID {r.get('id')}): {e}")
                continue
        return {"items": results, "total": total_count}

    async def get_all(
        self, limit: int = 100, vehicle_id: Optional[int] = None
    ) -> List[YakitAlimi]:
        """Legacy support for getting all records"""
        return await self.get_all_paged(limit=limit, arac_id=vehicle_id)

    async def get_stats(
        self,
        baslangic_tarih: Optional[date] = None,
        bitis_tarih: Optional[date] = None,
    ) -> Dict:
        """Genel yakıt istatistiklerini getir (Filtreli)"""
        async with UnitOfWork() as uow:
            return await uow.yakit_repo.get_stats(
                baslangic_tarih=baslangic_tarih, bitis_tarih=bitis_tarih
            )

    async def get_monthly_summary(self) -> List[Dict]:
        """Aylık yakıt tüketim özeti"""
        from app.database.repositories.analiz_repo import get_analiz_repo

        return await get_analiz_repo().get_monthly_consumption_series()

    async def bulk_add_yakit(self, yakit_list: List[YakitAlimiCreate]) -> int:
        """Toplu yakıt alımı ekle (ELITE Performance: Pre-fetch & Bulk Insert)"""
        if not yakit_list:
            return 0

        count = 0
        async with UnitOfWork() as uow:
            try:
                # 1. Pre-fetch Data for optimization (N+1 Prevention)
                last_km_cache = {}
                active_araclar = await uow.arac_repo.get_all(sadece_aktif=True)
                for a in active_araclar:
                    last_km_cache[a["id"]] = (
                        await uow.yakit_repo.get_son_km(a["id"]) or 0
                    )

                # 2. Sort & Filter
                sorted_list = sorted(yakit_list, key=lambda x: x.tarih)
                items_to_add = []

                for data in sorted_list:
                    if data.litre <= 0:
                        continue

                    current_last_km = last_km_cache.get(data.arac_id, 0)
                    if data.km_sayac < current_last_km:
                        logger.warning(
                            f"KM hatası (Atlandı): Arac {data.arac_id}, Son KM {current_last_km}, Girilen {data.km_sayac}"
                        )
                        continue

                    # Outlier kontrolü (İçeride pre-fetch olmadığı için buraya çekildi)
                    km_farki = data.km_sayac - current_last_km
                    if current_last_km > 0 and km_farki > 0:
                        tuketim = (data.litre / km_farki) * 100
                        if tuketim < 15 or tuketim > 65:  # Hardcoded high-level guard
                            logger.info(
                                f"Yüksek sapma tespiti (Bulk): {data.arac_id} - {tuketim:.1f} L/100km"
                            )

                    items_to_add.append(
                        {
                            "tarih": data.tarih,
                            "arac_id": data.arac_id,
                            "istasyon": data.istasyon,
                            "fiyat": float(data.fiyat_tl),
                            "litre": data.litre,
                            "km_sayac": data.km_sayac,
                            "fis_no": data.fis_no,
                            "depo_durumu": data.depo_durumu,
                        }
                    )
                    last_km_cache[data.arac_id] = data.km_sayac

                # 3. True Bulk Insert (N+1 Query Elimination)
                if items_to_add:
                    await uow.yakit_repo.bulk_create(items_to_add)
                    await uow.commit()  # UoW commit - veriyi kalıcı kaydet
                    count = len(items_to_add)

            except Exception as e:
                logger.error(f"Bulk insert hatası: {e}")
                raise e

        if count > 0:
            logger.info(f"Bulk insert: {count} yakıt alımı eklendi")
        return count


def get_yakit_service() -> YakitService:
    from app.core.container import get_container

    return get_container().yakit_service
