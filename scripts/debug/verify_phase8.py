import asyncio
import os
import sys

sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Sofor, Sefer
from app.core.services.sofor_service import get_sofor_service

async def verify():
    service = get_sofor_service()
    async with AsyncSessionLocal() as db:
        # 1. Create a test driver
        print("Test 1: Create Driver with Manual Score")
        s_id = await service.add_sofor(ad_soyad="Final Test Sürücü", manual_score=1.5)
        s = await db.get(Sofor, s_id)
        print(f"Driver created. Manual: {s.manual_score}, Total: {s.score} (Expected 1.5 since no trips yet)")
        
        # 2. Add a trip to trigger performance calculation
        print("\nTest 2: Hybrid Score Calculation")
        from datetime import date
        sefer = Sefer(
            sofor_id=s_id,
            arac_id=1, # Assume 1 exists
            tarih=date.fromisoformat("2024-01-28"),
            cikis_yeri="A",
            varis_yeri="B",
            mesafe_km=100,
            net_kg=10000, # 10 ton
            tuketim=40.0 # High consumption (Target 30) -> Factor 0.75
        )
        db.add(sefer)
        await db.commit()
        
        # Performance Factor = 30 / 40 = 0.75
        # Hybrid = (0.75 * 0.6) + (1.5 * 0.4) = 0.45 + 0.6 = 1.05
        
        # Trigger update of manual score to force recalculation
        await service.update_score(s_id, 1.5)
        await db.refresh(s)
        print(f"Hybrid Score after trip: {s.score} (Expected ~1.05)")

        # 3. Smart Delete Test
        print("\nTest 3: Smart Delete Logic")
        print(f"Current Status: Incremental (Active: {s.aktif})")
        await service.delete_sofor(s_id)
        await db.refresh(s)
        print(f"After First Delete: Incremental (Active: {s.aktif}) (Expected False)")
        
        try:
            print("Trying Hard Delete (Should fail due to trip)...")
            await service.delete_sofor(s_id)
        except ValueError as e:
            print(f"Expected failure caught: {e}")

        # Cleanup trip to test hard delete
        print("Cleaning up trip for hard delete test...")
        await db.delete(sefer)
        await db.commit()
        
        success = await service.delete_sofor(s_id)
        print(f"Second Delete success: {success} (Expected True - Hard Deleted)")

if __name__ == "__main__":
    asyncio.run(verify())
