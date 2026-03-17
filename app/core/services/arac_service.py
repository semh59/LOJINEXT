"""
TIR Yakıt Takip Sistemi - Araç Servisi
İş mantığı katmanı: Araç yönetimi ve validasyonlar
"""

from typing import Any, Dict, List, Optional

from app.core.entities.models import Arac, AracCreate, AracUpdate, VehicleStats
from app.database.repositories.arac_repo import AracRepository, get_arac_repo
from app.infrastructure.events.event_bus import (
    EventBus,
    EventType,
    get_event_bus,
    publishes,
)
from app.infrastructure.logging.logger import get_logger
from app.database.unit_of_work import UnitOfWork

logger = get_logger(__name__)


class AracService:
    """Araç iş mantığı servisi"""

    def __init__(
        self,
        repo: Optional["AracRepository"] = None,
        event_bus: Optional[EventBus] = None,
    ):
        import asyncio

        self.repo = repo or get_arac_repo()
        self.event_bus = event_bus or get_event_bus()
        self._lock = asyncio.Lock()

    async def _log_vehicle_event(
        self,
        arac_id: int,
        event_type: str,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        details: Optional[str] = None,
        uow: Optional[Any] = None,
        triggered_by: Optional[str] = "SYSTEM",
    ):
        """Vehicle event log kaydı at (UoW Uyumlu / Atomic)"""
        try:
            from app.database.models import VehicleEventLog

            log = VehicleEventLog(
                arac_id=arac_id,
                event_type=event_type,
                old_status=old_status,
                new_status=new_status,
                triggered_by=triggered_by,
                details=details,
            )

            if uow:
                # Use existing session from UnitOfWork
                uow.session.add(log)
            else:
                # Fallback only if absolutely necessary, but preferred to always pass UoW
                from app.database.unit_of_work import UnitOfWork

                async with UnitOfWork() as uow_internal:
                    uow_internal.session.add(log)
                    await uow_internal.commit()
        except Exception as e:
            logger.error(f"Vehicle event log hatası: {e}")

    @publishes(EventType.ARAC_ADDED)
    async def create_arac(
        self, data: AracCreate, uow: Optional[UnitOfWork] = None
    ) -> int:
        """Yeni araç oluştur (Duplicate Check + Reactivation)"""
        if uow is None:
            async with UnitOfWork() as new_uow:
                return await self._create_arac_impl(data, new_uow)
        else:
            return await self._create_arac_impl(data, uow)

    async def _create_arac_impl(self, data: AracCreate, uow: UnitOfWork) -> int:
        async with self._lock:  # Race Condition Guard (TOCTOU)
            # Business logic: Plaka benzersiz mi?
            existing = await uow.arac_repo.get_by_plaka(data.plaka, for_update=True)
            if existing:
                if existing.get("aktif") is False:
                    # Pasif araç varsa aktifleştir ve güncelle
                    logger.info(f"Pasif araç tekrar aktifleştiriliyor: {data.plaka}")
                    await uow.arac_repo.update(
                        existing["id"],
                        aktif=True,
                        marka=data.marka,
                        model=data.model or "",
                        yil=data.yil,
                        tank_kapasitesi=data.tank_kapasitesi,
                        hedef_tuketim=data.hedef_tuketim,
                        notlar=data.notlar or "",
                    )
                    await self._log_vehicle_event(
                        existing["id"],
                        "RE_ACTIVATED",
                        details=f"Pasif araç aktifleştirildi: {data.plaka}",
                        uow=uow,
                    )
                    await uow.commit()
                    return existing["id"]
                else:
                    raise ValueError(
                        f"Bu plaka ile kayıtlı araç zaten var: {data.plaka}"
                    )

            # 1. Create Arac (Repository now returns the object)
            logger.debug(f"[_create_arac_impl] Using UOW session {id(uow.session)}")
            new_arac = await uow.arac_repo.add(
                plaka=data.plaka,
                marka=data.marka,
                model=data.model or "",
                yil=data.yil,
                tank_kapasitesi=data.tank_kapasitesi,
                hedef_tuketim=data.hedef_tuketim,
                notlar=data.notlar or "",
            )
            logger.info(f"Yeni araç eklendi: {data.plaka}")

            # 2. Add event log entry (Manually to ensure it's in the same transaction)
            from datetime import datetime, timezone
            from app.database.models import VehicleEventLog

            log = VehicleEventLog(
                arac_id=new_arac.id,
                event_type="CREATED",
                created_at=datetime.now(timezone.utc),
                triggered_by="SYSTEM",
                details=f"Yeni araç eklendi: {data.plaka}",
            )
            uow.session.add(log)
            # Flush to ensure ID is generated and visible
            await uow.session.flush()

            await uow.commit()
            return int(new_arac.id)

    @publishes(EventType.ARAC_UPDATED)
    async def update_arac(
        self, arac_id: int, data: AracUpdate, uow: Optional[UnitOfWork] = None
    ) -> bool:
        """Araç güncelle (Safe Plate Change)"""
        if uow is None:
            async with UnitOfWork() as new_uow:
                return await self._update_arac_impl(arac_id, data, new_uow)
        else:
            return await self._update_arac_impl(arac_id, data, uow)

    async def _update_arac_impl(
        self, arac_id: int, data: AracUpdate, uow: UnitOfWork
    ) -> bool:
        if data.plaka:
            async with self._lock:  # Local Lock (Secondary Guard)
                existing = await uow.arac_repo.get_by_plaka(data.plaka, for_update=True)
                if existing and existing["id"] != arac_id:
                    raise ValueError(f"Bu plaka başka bir araca ait: {data.plaka}")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return False

        # Check for status change logging
        old_status = None
        if "aktif" in update_data:
            current = await uow.arac_repo.get_by_id(arac_id)
            if current:
                old_status = "ACTIVE" if current.get("aktif") else "PASSIVE"

        success = await uow.arac_repo.update(arac_id, **update_data)
        if success:
            logger.info(f"Araç güncellendi: ID {arac_id}")
            if "aktif" in update_data:
                new_status = "ACTIVE" if update_data["aktif"] else "PASSIVE"
                if old_status != new_status:
                    await self._log_vehicle_event(
                        arac_id,
                        "STATUS_CHANGE",
                        old_status=old_status,
                        new_status=new_status,
                        details="Status updated via update_arac",
                        uow=uow,
                    )
            await uow.commit()
        return success

    @publishes(EventType.ARAC_DELETED)
    async def delete_arac(self, arac_id: int) -> bool:
        """Araç sil (Smart Delete: Aktif->Pasif, Pasif->Sil)"""
        async with UnitOfWork() as uow:
            current = await uow.arac_repo.get_by_id(arac_id)
            if not current:
                return False

            if current.get("aktif"):
                # Soft Delete
                success = await uow.arac_repo.update(arac_id, aktif=False)
                if success:
                    logger.info(f"Araç pasife alındı (Soft Deleted): ID {arac_id}")
                    await self._log_vehicle_event(
                        arac_id,
                        "STATUS_CHANGE",
                        old_status="ACTIVE",
                        new_status="PASSIVE",
                        details="Soft deleted via delete_arac",
                        uow=uow,
                    )
                    await uow.commit()
                return success
            else:
                # Hard Delete
                try:
                    success = await uow.arac_repo.hard_delete(arac_id)
                    if success:
                        logger.info(
                            f"Araç tamamen silindi (Hard Deleted): ID {arac_id}"
                        )
                        # Not adding vehicle_event_log for hard delete as the vehicle record is gone
                        await uow.commit()
                    return success
                except Exception as e:
                    logger.warning(f"Hard delete engellendi (Bağımlı veri): {e}")
                    raise ValueError(
                        "Bu araca ait aktif/arşivlenmiş sefer kayıtları veya yakıt alımları bulunduğu için tamamen silinemez. Pasif durumda kalması güvenlidir."
                    )

    async def delete_all_vehicles(self) -> int:
        """Tüm araçları temizle (Admin Only - UoW)"""
        async with UnitOfWork() as uow:
            try:
                count = await uow.arac_repo.hard_delete_all()
                logger.info(f"Tüm araçlar temizlendi: {count} adet")
                await uow.commit()
                return count
            except Exception as e:
                logger.error(f"Toplu silme hatası: {e}")
                raise ValueError(
                    "Bazı araçlar (bağımlı sefer/yakıt kayıtları nedeniyle) silinemedi. Lütfen önce o kayıtları temizleyin."
                )

    async def get_all_paged(
        self,
        skip: int = 0,
        limit: int = 100,
        aktif_only: bool = True,
        search: Optional[str] = None,
        marka: Optional[str] = None,
        model: Optional[str] = None,
        min_yil: Optional[int] = None,
        max_yil: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Sayfalı ve filtreli araç listesi (Güvenli Katman).
        """
        filters: Dict[str, Any] = {}
        if marka:
            filters["marka"] = marka
        if model:
            filters["model"] = model
        if min_yil is not None:
            filters["yil_ge"] = min_yil
        if max_yil is not None:
            filters["yil_le"] = max_yil

        async with UnitOfWork() as uow:
            rows = await uow.arac_repo.get_all(
                offset=skip,
                limit=limit,
                sadece_aktif=aktif_only,
                search=search,
                filters=filters,
            )
            total = await uow.arac_repo.count_all(
                sadece_aktif=aktif_only,
                search=search,
                filters=filters,
            )

        vehicles: List[Arac] = []
        for r in rows:
            try:
                vehicles.append(Arac.model_validate(dict(r)))
            except Exception as e:
                logger.warning(f"Skipping invalid vehicle record ID {r.get('id')}: {e}")
                continue
        return {"items": vehicles, "total": total}

    async def get_all_vehicles(self, only_active: bool = True) -> List[Arac]:
        """Tüm araçları listele (Legacy support)"""
        return await self.get_all_paged(aktif_only=only_active)

    async def get_vehicle_stats(self, arac_id: int) -> Optional[VehicleStats]:
        """Araç detay ve istatistikleri"""
        async with UnitOfWork() as uow:
            row = await uow.arac_repo.get_arac_with_stats(arac_id)
        if not row:
            return None
        return VehicleStats.model_validate(dict(row))

    async def get_by_id(self, arac_id: int) -> Optional[Arac]:
        """ID ile araç getir"""
        async with UnitOfWork() as uow:
            row = await uow.arac_repo.get_by_id(arac_id)
        if not row:
            return None
        return Arac.model_validate(dict(row))

    async def bulk_add_arac(self, data_list: List[AracCreate]) -> int:
        """Toplu araç oluştur (UoW & Event Log Uyumlu)"""
        if not data_list:
            return 0

        async with UnitOfWork() as uow:
            # Mevcut plakaları çek
            existing_plakalar = await uow.arac_repo.get_aktif_plakalar()
            existing_set = set(existing_plakalar)

            to_add = []
            for data in data_list:
                if data.plaka in existing_set:
                    continue

                to_add.append(
                    {
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
                        "aktif": True,
                    }
                )

            if to_add:
                ids = await uow.arac_repo.bulk_create(to_add)
                logger.info(f"Toplu araç eklendi: {len(ids)} adet")

                # Event log records for batch
                for arac_id in ids:
                    await self._log_vehicle_event(
                        arac_id,
                        "CREATED",
                        details="Bulk created",
                        uow=uow,
                    )

                await uow.commit()
                return len(ids)

        return 0


def get_arac_service() -> AracService:
    from app.core.container import get_container

    return get_container().arac_service
