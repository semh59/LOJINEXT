import sys
import os
import asyncio
import json
from datetime import date

sys.path.append(os.getcwd())

from app.database.unit_of_work import UnitOfWork
from app.database.models import Sefer
from sqlalchemy import select, or_, func


async def verify_backend():
    print("--- BACKEND VERIFICATION ---")

    async with UnitOfWork() as uow:
        # 1. Verify Search Logic
        print("\n1. SEARCH TEST:")
        # Get an old trip number first
        stmt = (
            select(Sefer.sefer_no)
            .where(Sefer.sefer_no != None)
            .order_by(Sefer.tarih.asc())
            .limit(1)
        )
        old_trip = (await uow.session.execute(stmt)).scalar_one_or_none()

        if old_trip:
            print(f"Target Old Trip No: {old_trip}")
            # Try searching for it via repo
            search_res = await uow.sefer_repo.get_all(
                search=old_trip, limit=100
            )  # Explicit limit
            found = any(r["sefer_no"] == old_trip for r in search_res)
            print(f"Search found match? {found} (Count: {len(search_res)})")
        else:
            print("No trips with sefer_no found to test.")

        # 2. Verify Predictions (Real Prediction Data)
        print("\n2. PREDICTION DATA CHECK:")
        stmt = select(func.count(Sefer.id)).where(Sefer.tahmini_tuketim != None)
        count_pred = (await uow.session.execute(stmt)).scalar()

        stmt_total = select(func.count(Sefer.id))
        count_total = (await uow.session.execute(stmt_total)).scalar()

        print(f"Total Trips: {count_total}")
        print(
            f"Trips with Prediction: {count_pred} ({(count_pred / count_total) * 100:.1f}%)"
        )

        # Check a sample
        stmt_sample = select(Sefer).where(Sefer.tahmini_tuketim != None).limit(1)
        sample = (await uow.session.execute(stmt_sample)).scalar_one_or_none()
        if sample:
            print(f"Sample Prediction: Trip {sample.id} -> {sample.tahmini_tuketim} L")

        # 3. Verify Highway Data
        print("\n3. HIGHWAY DATA CHECK:")
        stmt_hwy = select(func.count(Sefer.id)).where(Sefer.otoban_mesafe_km > 0)
        count_hwy = (await uow.session.execute(stmt_hwy)).scalar()
        print(f"Trips with Highway Data > 0: {count_hwy}")


if __name__ == "__main__":
    asyncio.run(verify_backend())
