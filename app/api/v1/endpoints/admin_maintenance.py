from fastapi import APIRouter, Depends
from app.core.services.maintenance_service import MaintenanceService
from app.infrastructure.security.permission_checker import require_yetki
from app.database.models import BakimTipi
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class MaintenanceCreateSchema(BaseModel):
    arac_id: int
    bakim_tipi: BakimTipi
    km_bilgisi: int
    bakim_tarihi: datetime
    maliyet: float = 0.0
    detaylar: str = ""


@router.post("/", dependencies=[Depends(require_yetki(["bakim_ekle", "all", "*"]))])
async def create_maintenance(data: MaintenanceCreateSchema):
    """Admin: Create a new maintenance record."""
    service = MaintenanceService()
    return await service.create_maintenance_record(
        arac_id=data.arac_id,
        bakim_tipi=data.bakim_tipi,
        km_bilgisi=data.km_bilgisi,
        bakim_tarihi=data.bakim_tarihi,
        maliyet=data.maliyet,
        detaylar=data.detaylar,
    )


@router.get(
    "/alerts",
    dependencies=[Depends(require_yetki(["admin", "super_admin", "fleet_manager"]))],
)
async def get_upcoming_alerts():
    """Get list of urgent/upcoming maintenance tasks."""
    service = MaintenanceService()
    return await service.get_upcoming_alerts()


@router.get(
    "/{arac_id}",
    dependencies=[Depends(require_yetki(["admin", "super_admin", "fleet_manager"]))],
)
async def get_vehicle_history(arac_id: int):
    """Get full history for a specific vehicle."""
    service = MaintenanceService()
    return await service.get_vehicle_maintenance_history(arac_id)


@router.patch(
    "/{bakim_id}/complete",
    dependencies=[Depends(require_yetki(["bakim_duzenle", "all", "*"]))],
)
async def mark_complete(bakim_id: int):
    """Mark maintenance as completed."""
    service = MaintenanceService()
    return {"success": await service.mark_as_completed(bakim_id)}
