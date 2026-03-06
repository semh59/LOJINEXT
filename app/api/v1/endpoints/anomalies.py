from typing import Any, Dict
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_user
from app.database.unit_of_work import UnitOfWork

router = APIRouter()


@router.get("/fleet/insights", response_model=Dict[str, Any])
async def get_fleet_insights(
    days: int = Query(30, ge=2, le=90),
    current_user: Any = Depends(get_current_user),
):
    """
    Filo analiz dashboard verilerini getirir.
    Maliyet kaçağı ve bakım adaylarını içerir.
    """
    async with UnitOfWork() as uow:
        # 1. Maliyet Kaçağı (Leakage)
        leakage = await uow.sefer_repo.get_cost_leakage_stats(days=days)

        # 2. Bakım Adayları (Maintenance)
        maintenance = await uow.arac_repo.get_maintenance_candidates()

        return {
            "status": "success",
            "data": {"leakage": leakage, "maintenance": maintenance},
        }
