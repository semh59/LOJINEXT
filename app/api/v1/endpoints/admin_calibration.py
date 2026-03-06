from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.services.route_calibration_service import RouteCalibrationService
from app.database.unit_of_work import UnitOfWork
from app.infrastructure.security.permission_checker import require_yetki

router = APIRouter()


@router.post(
    "/calibrate/{sefer_id}",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_yetki("kalibrasyon_goruntule"))],
)
async def calibrate_route_from_trip(
    sefer_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Update a route's 'Golden Path' using a specific trip's GPS data.
    """
    uow = UnitOfWork(db)
    service = RouteCalibrationService(uow)

    success = await service.calibrate_route_from_trip(sefer_id)
    if success:
        return {"status": "success", "message": "Güzergah kalibrasyonu tamamlandı."}

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Kalibrasyon yapılamadı (Veri eksik veya yetersiz).",
    )


@router.get(
    "/match/{sefer_id}",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_yetki("kalibrasyon_goruntule"))],
)
async def match_trip_to_path(
    sefer_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Verify if a trip matches the calibrated target path.
    """
    uow = UnitOfWork(db)
    service = RouteCalibrationService(uow)
    return await service.match_sefer_to_path(sefer_id)
