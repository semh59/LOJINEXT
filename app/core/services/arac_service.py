"""
TIR Yakıt Takip Sistemi - Araç Servisi
İş mantığı katmanı: Araç yönetimi ve validasyonlar
"""

from typing import Any, List, Optional

from app.core.entities.models import Arac, AracCreate, AracUpdate, VehicleStats
from app.database.repositories.arac_repo import get_arac_repo
from app.infrastructure.events.event_bus import EventType, get_event_bus, publishes
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

class AracService:
    """Araç iş mantığı servisi"""

    def __init__(self, repo=None, event_bus=None):
        import asyncio
        self.repo = repo or get_arac_repo()
        self.event_bus = event_bus or get_event_bus()
        self._lock = asyncio.Lock()

    @publishes(EventType.ARAC_ADDED)
    async def create_arac(self, data: AracCreate) -> int:
        """Yeni araç oluştur (Atomic Check)"""
        async with self._lock:  # Race Condition Guard (TOCTOU)
            # Business logic: Plaka benzersiz mi?
            existing = await self.repo.get_by_plaka(data.plaka)
            if existing:
                if existing.get('aktif') is False:
                    # Pasif araç varsa aktifleştir ve güncelle
                    logger.info(f"Pasif araç tekrar aktifleştiriliyor: {data.plaka}")
                    await self.repo.update(
                        existing['id'],
                        aktif=True,
                        marka=data.marka,
                        model=data.model or "",
                        yil=data.yil,
                        tank_kapasitesi=data.tank_kapasitesi,
                        hedef_tuketim=data.hedef_tuketim,
                        notlar=data.notlar or ""
                    )
                    return existing['id']
                else:
                    raise ValueError(f"Bu plaka ile kayıtlı araç zaten var: {data.plaka}")

            arac_id = await self.repo.add(
                plaka=data.plaka,
                marka=data.marka,
                model=data.model or "",
                yil=data.yil,
                tank_kapasitesi=data.tank_kapasitesi,
                hedef_tuketim=data.hedef_tuketim,
                notlar=data.notlar or ""
            )
            logger.info(f"Yeni araç eklendi: {data.plaka} (ID: {arac_id})")
            return arac_id

    @publishes(EventType.ARAC_UPDATED)
    async def update_arac(self, arac_id: int, data: AracUpdate) -> bool:
        """Araç güncelle (Safe Plate Change)"""
        if data.plaka:
            async with self._lock:
                existing = await self.repo.get_by_plaka(data.plaka)
                if existing and existing['id'] != arac_id:
                    raise ValueError(f"Bu plaka başka bir araca ait: {data.plaka}")

        # Update
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return False

        success = await self.repo.update(arac_id, **update_data)
        if success:
            logger.info(f"Araç güncellendi: ID {arac_id}")
        return success

    @publishes(EventType.ARAC_DELETED)
    async def delete_arac(self, arac_id: int) -> bool:
        """Araç sil (Smart Delete: Aktif->Pasif, Pasif->Sil)"""
        try:
            current = await self.repo.get_by_id(arac_id)
            if not current:
                return False

            if current.get('aktif'):
                 # Soft Delete
                 success = await self.repo.update(arac_id, aktif=False)
                 if success:
                     logger.info(f"Araç pasife alındı (Soft Deleted): ID {arac_id}")
                 return success
            else:
                 # Hard Delete
                try:
                    success = await self.repo.hard_delete(arac_id)
                    if success:
                        logger.info(f"Araç tamamen silindi (Hard Deleted): ID {arac_id}")
                    return success
                except Exception as e:
                    logger.warning(f"Hard delete engellendi (Bağımlı veri): {e}")
                    raise ValueError("Bu araca ait aktif/arşivlenmiş sefer kayıtları veya yakıt alımları bulunduğu için tamamen silinemez. Pasif durumda kalması güvenlidir.")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Araç silinemedi: {e}")
            raise ValueError("Araç silinirken bir hata oluştu.")


    async def delete_all_vehicles(self) -> int:
        """Tüm araçları temizle (Admin Only - Powerful)"""
        try:
            count = await self.repo.hard_delete_all()
            logger.info(f"Tüm araçlar temizlendi: {count} adet")
            return count
        except Exception as e:
            logger.error(f"Toplu silme hatası: {e}")
            raise ValueError("Bazı araçlar (bağımlı sefer/yakıt kayıtları nedeniyle) silinemedi. Lütfen önce o kayıtları temizleyin.")

    async def get_all_paged(
        self,
        skip: int = 0,
        limit: int = 100,
        aktif_only: bool = True,
        search: Optional[str] = None,
        marka: Optional[str] = None,
        model: Optional[str] = None,
        min_yil: Optional[int] = None,
        max_yil: Optional[int] = None
    ) -> List[Any]:
        """
        Sayfalı ve filtreli araç listesi (Güvenli Katman).
        """
        filters = {}
        if marka: filters["marka"] = marka
        if model: filters["model"] = model
        if min_yil is not None: filters["yil_ge"] = min_yil
        if max_yil is not None: filters["yil_le"] = max_yil

        rows = await self.repo.get_all(
            offset=skip,
            limit=limit,
            sadece_aktif=aktif_only,
            search=search,
            filters=filters
        )
        
        vehicles = []
        for r in rows:
            try:
                vehicles.append(Arac.model_validate(dict(r)))
            except Exception as e:
                logger.warning(f"Skipping invalid vehicle record ID {r.get('id')}: {e}")
                continue
        return vehicles

    async def get_all_vehicles(self, only_active: bool = True) -> List[Arac]:
        """Tüm araçları listele (Legacy support)"""
        return await self.get_all_paged(aktif_only=only_active)

    async def get_vehicle_stats(self, arac_id: int) -> Optional[VehicleStats]:
        """Araç detay ve istatistikleri"""
        row = await self.repo.get_arac_with_stats(arac_id)
        if not row:
            return None
        return VehicleStats.model_validate(dict(row))

    async def get_by_id(self, arac_id: int) -> Optional[Arac]:
        """ID ile araç getir"""
        row = await self.repo.get_by_id(arac_id)
        if not row:
            return None
        return Arac.model_validate(dict(row))


    async def bulk_add_arac(self, data_list: List[AracCreate]) -> int:
        """Toplu araç oluştur (N+1 çözüm)"""
        if not data_list:
            return 0

        # Mevcut plakaları çek
        existing_plakalar = await self.repo.get_aktif_plakalar()
        existing_set = set(existing_plakalar)

        to_add = []
        for data in data_list:
            if data.plaka in existing_set:
                continue
            
            to_add.append({
                "plaka": data.plaka,
                "marka": data.marka,
                "model": data.model or "",
                "yil": data.yil,
                "tank_kapasitesi": data.tank_kapasitesi,
                "hedef_tuketim": data.hedef_tuketim,
                "bos_agirlik_kg": data.bos_agirlik_kg,
                "motor_verimliligi": data.motor_verimliligi,
                "lastik_direnc_katsayisi": data.lastik_direnc_katsayisi,
                "on_kesit_alani_m2": data.on_kesit_alani_m2,
                "hava_direnc_katsayisi": data.hava_direnc_katsayisi,
                "maks_yuk_kapasitesi_kg": data.maks_yuk_kapasitesi_kg,
                "notlar": data.notlar or "",
                "aktif": True
            })

        if to_add:
            ids = await self.repo.bulk_create(to_add)
            logger.info(f"Toplu araç eklendi: {len(ids)} adet")
            return len(ids)
        
        return 0


def get_arac_service() -> AracService:
    from app.core.container import get_container
    return get_container().arac_service
