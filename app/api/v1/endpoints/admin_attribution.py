from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.services.attribution_service import AttributionService
from app.database.unit_of_work import UnitOfWork
from app.database.models import Kullanici
from app.schemas.attribution import (
    AttributionOverrideRequest,
    AttributionOverrideResponse,
)
from app.infrastructure.security.permission_checker import require_yetki

router = APIRouter()


@router.post(
    "/override",
    response_model=AttributionOverrideResponse,
    dependencies=[Depends(require_yetki("attribution_goruntule"))],
)
async def override_trip_attribution(
    request: AttributionOverrideRequest,
    current_user: Kullanici = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Manually override the vehicle or driver for a specific trip.
    """
    uow = UnitOfWork(db)
    attribution_service = AttributionService(uow)

    try:
        success = await attribution_service.override_attribution(
            sefer_id=request.sefer_id,
            arac_id=request.new_arac_id,
            sofor_id=request.new_sofor_id,
            reason=request.reason,
        )

        return AttributionOverrideResponse(
            sefer_id=request.sefer_id,
            success=success,
            message="Atanmış araç/şoför başarıyla güncellendi."
            if success
            else "Güncelleme yapılamadı.",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Atama güncellenemedi: {str(e)}",
        )


@router.post(
    "/bulk-override",
    response_model=List[AttributionOverrideResponse],
    dependencies=[Depends(require_yetki("attribution_goruntule"))],
)
async def bulk_override_trip_attribution(
    requests: List[AttributionOverrideRequest],
    current_user: Kullanici = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Bulk override trip attributions.
    """
    uow = UnitOfWork(db)
    attribution_service = AttributionService(uow)
    results = []

    for req in requests:
        try:
            success = await attribution_service.override_attribution(
                sefer_id=req.sefer_id,
                arac_id=req.new_arac_id,
                sofor_id=req.new_sofor_id,
                reason=req.reason,
            )
            results.append(
                AttributionOverrideResponse(
                    sefer_id=req.sefer_id,
                    success=success,
                    message="Başarılı" if success else "Hata",
                )
            )
        except Exception as e:
            results.append(
                AttributionOverrideResponse(
                    sefer_id=req.sefer_id, success=False, message=str(e)
                )
            )

    return results
