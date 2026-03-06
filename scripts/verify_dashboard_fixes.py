import asyncio
import os
import sys
import traceback

# Set path to project root
sys.path.append(os.getcwd())

from app.database.unit_of_work import get_uow
from app.database.models import Anomaly, Base, YakitAlimi
from app.database.repositories.analiz_repo import get_analiz_repo
from sqlalchemy import select, func, text, create_engine


async def verify():
    print("--- 0. Database Schema Sync ---")
    try:
        engine = create_engine("sqlite:///loji.db")
        # Ensure Anomaly is registered
        import app.database.models

        Base.metadata.create_all(engine)
        print("SUCCESS: Schema sync completed.")
    except Exception:
        print("FAILED: Schema sync failed")
        traceback.print_exc()

    print("\n--- 1. Anomaly Model Verification ---")
    async with get_uow() as uow:
        try:
            stmt = select(Anomaly).limit(1)
            await uow.session.execute(stmt)
            print("SUCCESS: Anomaly model is queryable.")
        except Exception:
            print("FAILED: Anomaly model query failed")
            traceback.print_exc()

    print("\n--- 2. Dashboard Stats Verification ---")
    repo = get_analiz_repo()
    try:
        stats = await repo.get_dashboard_stats()
        print(f"SUCCESS: Dashboard stats fetched: {list(stats.keys())}")
    except Exception:
        print("FAILED: Dashboard stats repo call failed")
        traceback.print_exc()

    print("\n--- 3. Consumption Trend (reports.py Logic) Verification ---")
    async with get_uow() as uow:
        try:
            dialect = uow.session.bind.dialect.name
            if dialect == "sqlite":
                month_col = func.strftime("%Y-%m", YakitAlimi.tarih)
            else:
                month_col = func.to_char(YakitAlimi.tarih, "YYYY-MM")

            stmt = (
                select(
                    month_col.label("month"),
                    func.sum(YakitAlimi.litre).label("consumption"),
                )
                .group_by(month_col)
                .order_by(month_col)
                .limit(6)
            )
            result = await uow.session.execute(stmt)
            print(f"SUCCESS: Consumption trend logic works on {dialect}.")
            print(f"Data: {result.all()}")
        except Exception:
            print("FAILED: Consumption trend logic failed")
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(verify())
