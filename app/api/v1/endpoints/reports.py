from typing import Annotated
from app.api.deps import SessionDep, get_current_user
from app.database.models import Arac, Sefer, Sofor, YakitAlimi, Kullanici
from fastapi import APIRouter, Depends
from sqlalchemy import func, select

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Dashboard istatistiklerini getir (Elite Dashboard).
    """
    from app.database.repositories.analiz_repo import get_analiz_repo
    analiz_repo = get_analiz_repo()
    
    # 1. Core Stats
    stats = await analiz_repo.get_dashboard_stats()
    
    # 2. Monthly Comparison (Trends)
    comparison = await analiz_repo.get_monthly_comparison_stats()
    
    return {
        **stats,
        "trends": {
            "sefer": comparison.get("sefer_degisim", 0),
            "km": comparison.get("km_degisim", 0),
            "tuketim": comparison.get("tuketim_degisim", 0)
        }
    }

@router.get("/consumption-trend")
async def get_consumption_trend(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Aylık tüketim trendi.
    """
    # PostgreSQL date_trunc kullanımı
    stmt = (
        select(
            func.to_char(YakitAlimi.tarih, 'YYYY-MM').label("month"),
            func.sum(YakitAlimi.litre).label("consumption")
        )
        .group_by("month")
        .order_by("month")
        .limit(6)
    )

    result = await db.execute(stmt)
    return [
        {"month": row.month, "consumption": float(row.consumption)}
        for row in result.all()
    ]
