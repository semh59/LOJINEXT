from typing import List, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from app.database.unit_of_work import UnitOfWork
from app.database.models import AracBakim, BakimTipi
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class MaintenanceService:
    """Service handling vehicle maintenance logic and alerting."""

    async def create_maintenance_record(
        self,
        arac_id: int,
        bakim_tipi: BakimTipi,
        km_bilgisi: int,
        bakim_tarihi: datetime,
        maliyet: float = 0.0,
        detaylar: str = "",
    ) -> AracBakim:
        """Create a new maintenance record for a vehicle."""
        async with UnitOfWork() as uow:
            # Verify vehicle exists
            arac = await uow.arac_repo.get(arac_id)
            if not arac:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Araç bulunamadı: {arac_id}",
                )

            bakim = AracBakim(
                arac_id=arac_id,
                bakim_tipi=bakim_tipi,
                km_bilgisi=km_bilgisi,
                bakim_tarihi=bakim_tarihi,
                maliyet=maliyet,
                detaylar=detaylar,
                tamamlandi=False,
            )

            created_bakim = await uow.maintenance_repo.add(bakim)
            await uow.commit()
            logger.info(
                f"Maintenance record created for vehicle {arac_id}, Type: {bakim_tipi}"
            )
            return created_bakim

    async def get_vehicle_maintenance_history(self, arac_id: int) -> List[AracBakim]:
        """Retrieve full maintenance history for a vehicle."""
        async with UnitOfWork() as uow:
            return await uow.maintenance_repo.get_by_arac_id(arac_id)

    async def mark_as_completed(self, bakim_id: int) -> bool:
        """Mark a maintenance record as completed."""
        async with UnitOfWork() as uow:
            success = await uow.maintenance_repo.update(bakim_id, tamamlandi=True)
            if success:
                await uow.commit()
                logger.info(f"Maintenance {bakim_id} marked as completed.")
            return success

    async def get_upcoming_alerts(self) -> List[Dict[str, Any]]:
        """Fetch vehicles that are due or overdue for maintenance."""
        async with UnitOfWork() as uow:
            bakimlar = await uow.maintenance_repo.get_upcoming_maintenance()
            # Enrich with vehicle plates for UI convenience
            results = []
            for b in bakimlar:
                arac = await uow.arac_repo.get(b.arac_id)
                results.append(
                    {
                        "id": b.id,
                        "arac_id": b.arac_id,
                        "plaka": arac.plaka if arac else "N/A",
                        "bakim_tipi": b.bakim_tipi,
                        "tarih": b.bakim_tarihi,
                        "vade_durumu": "OVERDUE"
                        if b.bakim_tarihi < datetime.now()
                        else "UPCOMING",
                    }
                )
            return results
