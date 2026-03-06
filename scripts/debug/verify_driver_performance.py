import asyncio
import sys
import os

from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Sofor
from app.core.services.sofor_service import get_sofor_service


async def verify_performance():
    print("Verifying Driver Performance System...")

    async with AsyncSessionLocal() as db:
        # 1. Get a driver
        driver = await db.get(Sofor, 1)  # Try ID 1
        if not driver:
            # Try to find any driver
            result = await db.execute(text("SELECT id FROM soforler LIMIT 1"))
            driver_id = result.scalar()
            if not driver_id:
                print("No drivers found to test.")
                return
            driver = await db.get(Sofor, driver_id)

        print(f"Testing for Driver: {driver.ad_soyad} (ID: {driver.id})")

        # 2. Call Service directly
        service = get_sofor_service()
        try:
            perf = await service.get_performance_details(driver.id)
            print("Performance Data Retrieved Successfully:")
            print(f"Safety Score: {perf['safety_score']}")
            print(f"Eco Score: {perf['eco_score']}")
            print(f"Compliance Score: {perf['compliance_score']}")
            print(f"Total Score: {perf['total_score']}")
            print(f"Trend: {perf['trend']}")

            # Basic Assertions
            assert 0 <= perf["safety_score"] <= 100, "Safety score out of range"
            assert 0 <= perf["eco_score"] <= 100, "Eco score out of range"
            assert 0 <= perf["total_score"] <= 100, "Total score out of range"

            print("✅ Verification Passed!")

        except Exception as e:
            print(f"❌ Verification Failed: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(verify_performance())
