"""
TIR Yakıt Takip Sistemi - Sefer Servisi
İş mantığı katmanı: Sefer işlemleri
"""

from datetime import date
from typing import List

from app.core.entities.models import Sefer, SeferCreate
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.repositories.sefer_repo import SeferRepository

# from app.database.repositories.sefer_repo import get_sefer_repo
from app.database.unit_of_work import get_uow
from app.infrastructure.events.event_bus import EventType, get_event_bus, publishes
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.audit import audit_log

logger = get_logger(__name__)


class SeferService:
    """
    Sefer işlemleri iş mantığı.
    """

    def __init__(self, repo, event_bus=None):
        self.repo = repo
        self.event_bus = event_bus or get_event_bus()

    @audit_log("CREATE", "sefer")
    @publishes(EventType.SEFER_ADDED)
    async def add_sefer(self, data: SeferCreate) -> int:
        """
        Yeni sefer ekle.
        """
        try:
            async with get_uow() as uow:
                # 1. Validation Logic (Ensuring vehicle is active)
                arac = await uow.arac_repo.get_by_id(data.arac_id)
                if not arac:
                    raise ValueError(f"Geçersiz araç ID: {data.arac_id}")
                if not arac.get("aktif"):
                    raise ValueError(
                        f"Pasif araç ile sefer oluşturulamaz: {arac.get('plaka', data.arac_id)}"
                    )

                if data.guzergah_id:
                    from app.database.models import Guzergah

                    guzergah = await uow.session.get(Guzergah, data.guzergah_id)
                    if not guzergah:
                        raise ValueError("Seçilen güzergah bulunamadı.")

                if data.mesafe_km <= 0:
                    raise ValueError("Mesafe 0'dan büyük olmalıdır")

                if data.net_kg < 0:
                    raise ValueError("Yük miktarı negatif olamaz")

                # Future date check (sanity limit: 1 year)
                trip_date = (
                    data.tarih
                    if isinstance(data.tarih, date)
                    else date.fromisoformat(data.tarih)
                )
                if (trip_date - date.today()).days > 365:
                    raise ValueError(
                        "Sefer tarihi 1 yıldan daha ileri bir tarih olamaz"
                    )

                # 2. DB Insert (Using UoW Repository)
                sefer_id = await uow.sefer_repo.add(
                    tarih=data.tarih,
                    saat=data.saat or "",
                    arac_id=data.arac_id,
                    sofor_id=data.sofor_id,
                    guzergah_id=data.guzergah_id,
                    net_kg=data.net_kg,
                    bos_agirlik_kg=data.bos_agirlik_kg,
                    dolu_agirlik_kg=data.dolu_agirlik_kg,
                    cikis_yeri=data.cikis_yeri,
                    varis_yeri=data.varis_yeri,
                    mesafe_km=data.mesafe_km,
                    bos_sefer=1 if data.bos_sefer else 0,
                    durum=data.durum,
                    ascent_m=data.ascent_m,
                    descent_m=data.descent_m,
                    notlar=data.notlar,
                )

                await uow.commit()
                logger.info(f"Sefer eklendi: ID {sefer_id}, Arac {data.arac_id}")
                return sefer_id

        except Exception as e:
            logger.error(f"Sefer ekleme hatasi: {e}")
            raise

    async def get_sefer_by_id(self, sefer_id: int) -> dict:
        """ID ile sefer getir (Detaylı)"""
        return await self.repo.get_by_id_with_details(sefer_id)

    @audit_log("UPDATE", "sefer")
    @publishes(EventType.SEFER_UPDATED)
    async def update_sefer(self, sefer_id: int, data: SeferCreate) -> bool:
        """Sefer güncelle"""
        try:
            success = await self.repo.update_sefer(
                id=sefer_id,
                tarih=data.tarih,
                saat=data.saat or "",
                arac_id=data.arac_id,
                sofor_id=data.sofor_id,
                guzergah_id=data.guzergah_id,
                net_kg=data.net_kg,
                bos_agirlik_kg=data.bos_agirlik_kg,
                dolu_agirlik_kg=data.dolu_agirlik_kg,
                cikis_yeri=data.cikis_yeri,
                varis_yeri=data.varis_yeri,
                mesafe_km=data.mesafe_km,
                bos_sefer=1 if data.bos_sefer else 0,
                notlar=data.notlar,
            )

            if success:
                logger.info(f"Sefer güncellendi: ID {sefer_id}")

            return success

        except Exception as e:
            logger.error(f"Sefer guncelleme hatasi: {e}")
            raise

    @audit_log("DELETE", "sefer")
    @publishes(EventType.SEFER_DELETED)
    async def delete_sefer(self, sefer_id: int) -> bool:
        """Sefer sil (Hard Delete)"""
        try:
            # Hard Delete directly
            success = await self.repo.delete_permanently(sefer_id)
            if success:
                logger.info(f"Sefer tamamen silindi (Hard Deleted): ID {sefer_id}")
            return success

        except Exception as e:
            logger.error(f"Sefer silme hatasi: {e}")
            raise ValueError(f"Sefer silinirken bir hata oluştu: {str(e)}")

    async def get_by_vehicle(self, arac_id: int, limit: int = 50) -> List[Sefer]:
        """Araç sefer geçmişini getir"""
        records = await self.repo.get_all(arac_id=arac_id, limit=limit)
        return [Sefer.model_validate(dict(r)) for r in records]

    async def get_all_paged(
        self, skip: int = 0, limit: int = 100, aktif_only: bool = True, **filters
    ) -> List[Sefer]:
        """
        Sayfalı ve filtreli sefer listesi (Güvenli Katman).
        Pydantic validasyon hatalarını yakalar, tüm listeyi çökertmez.
        """
        records = await self.repo.get_all(
            offset=skip, limit=limit, include_inactive=not aktif_only, **filters
        )

        results = []
        for r in records:
            try:
                # dict(r) conversion for safe pydantic validation
                results.append(Sefer.model_validate(dict(r)))
            except Exception as e:
                logger.error(f"Sefer validasyon hatasi (ID {r.get('id')}): {e}")
                continue
        return results

    async def get_all_trips(
        self,
        start_date: date = None,
        end_date: date = None,
        sofor_id: int = None,
        arac_id: int = None,
        status: str = None,
        limit: int = 100,
    ) -> List[Sefer]:
        """Filtreli sefer listesi (Legacy support, redirected to paged)"""
        return await self.get_all_paged(limit=limit, arac_id=arac_id, sofor_id=sofor_id)

    @audit_log("BULK_CREATE", "sefer", log_params=True)
    async def bulk_add_sefer(self, sefer_list: List[SeferCreate]) -> int:
        """Toplu sefer ekle (ELITE Performance: Batch Insert & Smart Logic)"""
        if not sefer_list:
            return 0

        count = 0
        async with get_uow() as uow:
            try:
                # 1. Pre-fetch Logic (N+1 Prevention)
                sorted_list = sorted(sefer_list, key=lambda x: (x.tarih, x.saat or ""))
                all_loc_names = await uow.lokasyon_repo.get_benzersiz_lokasyonlar()

                last_location = {}
                items_to_add = []

                for data in sorted_list:
                    if data.mesafe_km <= 0:
                        continue

                # 2. Lokasyon Eşleme ve Hazırlık (CPU Bound kısmı thread'e alıyoruz)

                # Eğer find_closest_match async ve DB kullanıyorsa, thread'e almak zordur.
                # Ancak 'all_loc_names' zaten elimizde.
                # Optimization: find_closest_match eğer sadece string distance ise, onu senkron helper yapıp threadde çalıştırmak lazım.
                # Ama repo methodu olduğu için dokunmuyoruz.
                # Sadece listeyi sort etme kısmını thread'e alabiliriz eğer liste çok büyükse.
                # sorted_list'i zaten yaptık.

                for data in sorted_list:
                    if data.mesafe_km <= 0:
                        continue

                    # Lokasyon Eşleme (İçeride pre-fetch kullanıyoruz - Hızlı)
                    matched_cikis = await uow.lokasyon_repo.find_closest_match(
                        data.cikis_yeri, pre_fetched_names=all_loc_names
                    )
                    if matched_cikis:
                        data.cikis_yeri = matched_cikis

                    matched_varis = await uow.lokasyon_repo.find_closest_match(
                        data.varis_yeri, pre_fetched_names=all_loc_names
                    )
                    if matched_varis:
                        data.varis_yeri = matched_varis

                    if data.cikis_yeri.lower() == data.varis_yeri.lower():
                        logger.warning(f"Hata: Çıkış/Varış aynı ({data.cikis_yeri})")
                        continue

                    items_to_add.append(
                        {
                            "tarih": data.tarih,
                            "saat": data.saat or "",
                            "arac_id": data.arac_id,
                            "sofor_id": data.sofor_id,
                            "net_kg": data.net_kg,
                            "cikis_yeri": data.cikis_yeri,
                            "varis_yeri": data.varis_yeri,
                            "mesafe_km": data.mesafe_km,
                            "bos_sefer": 1 if data.bos_sefer else 0,
                            "ascent_m": data.ascent_m or 0,
                            "descent_m": data.descent_m or 0,
                        }
                    )
                    last_location[data.arac_id] = data.varis_yeri

                # 3. Batch Insert (N+1 insert point)
                if items_to_add:
                    await uow.sefer_repo.bulk_create(items_to_add)
                    count = len(items_to_add)

            except Exception as e:
                logger.error(f"Bulk insert hatası (Sefer): {e}")
                raise e

        if count > 0:
            logger.info(f"Bulk insert: {count} sefer eklendi")
        return count


def get_sefer_service(db: AsyncSession = Depends(get_db)) -> SeferService:
    repo = SeferRepository(session=db)
    return SeferService(repo=repo)
