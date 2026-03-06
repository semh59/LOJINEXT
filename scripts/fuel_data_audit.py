import asyncio
import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import select, func, and_
from app.database.connection import AsyncSessionLocal
from app.database.models import Sefer, YakitAlimi


async def audit():
    async with AsyncSessionLocal() as db:
        # 1. Sefer Sayıları
        all_sefer_count = await db.scalar(select(func.count(Sefer.id)))
        real_sefer_count = await db.scalar(
            select(func.count(Sefer.id)).where(Sefer.is_real)
        )
        comparison_sefer_count = await db.scalar(
            select(func.count(Sefer.id)).where(
                and_(
                    Sefer.tahmini_tuketim.isnot(None),
                    Sefer.tuketim.isnot(None),
                    Sefer.tuketim > 0,
                    Sefer.is_real,
                )
            )
        )

        # 2. Yakıt Verileri
        yakit_count = await db.scalar(select(func.count(YakitAlimi.id)))
        yakit_stats = await db.execute(
            select(func.sum(YakitAlimi.litre), func.avg(YakitAlimi.litre)).where(
                YakitAlimi.aktif
            )
        )
        y_row = yakit_stats.first()
        total_fuel_liters = y_row[0] or 0
        avg_fuel_liters = y_row[1] or 0

        print("-" * 50)
        print("YAKIT VERİ DENETİMİ RAPORU")
        print(f"Total Sefer: {all_sefer_count}")
        print(f"Real Sefer: {real_sefer_count}")
        print(f"Sefer with Comparison Data: {comparison_sefer_count}")
        # The probable bug in Repo.get_stats():
        # It returns avg_fuel_liters and the UI labels it L/100km.
        # 641.2 matches that profile for a truck fill-up.

        print("-" * 50)


if __name__ == "__main__":
    import asyncio

    asyncio.run(audit())
