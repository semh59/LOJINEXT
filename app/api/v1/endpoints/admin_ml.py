from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.services.ml_service import MLService
from app.database.unit_of_work import UnitOfWork
from app.database.models import Kullanici
from app.schemas.ml_schemas import MLTaskRead, ModelVersionRead
from app.infrastructure.security.permission_checker import require_yetki
from app.api.middleware.rate_limiter import limiter

router = APIRouter()


@router.post(
    "/train/{arac_id}",
    response_model=MLTaskRead,
    dependencies=[Depends(require_yetki(["model_egit", "all", "*"]))],
)
@limiter.limit("3/hour")
async def trigger_training(
    arac_id: int,
    request: Request,
    current_user: Kullanici = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Manually trigger model training for a specific vehicle.
    Calculates next version automatically.
    """
    uow = UnitOfWork(db)
    ml_service = MLService(uow)

    try:
        task = await ml_service.schedule_training(
            arac_id=arac_id, user_id=current_user.id
        )
        return task
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Eğitim başlatılamadı: {str(e)}",
        )


@router.get(
    "/queue",
    response_model=List[MLTaskRead],
    dependencies=[Depends(require_yetki("model_goruntule"))],
)
async def get_training_queue(
    limit: int = 50,
    db: AsyncSession = Depends(deps.get_db),
):
    """Get recent and pending training tasks."""
    uow = UnitOfWork(db)
    ml_service = MLService(uow)
    return await ml_service.get_training_queue(limit=limit)


@router.get(
    "/versions/{arac_id}",
    response_model=List[ModelVersionRead],
    dependencies=[Depends(require_yetki("model_goruntule"))],
)
async def get_model_versions(
    arac_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """Get all model versions for a vehicle."""
    uow = UnitOfWork(db)
    # Note: We need to add this method to MLService or just use repo here for simple GET
    # Elite standard prefers Service
    async with uow:
        return await uow.model_versiyon_repo.get_all_for_vehicle(arac_id)
