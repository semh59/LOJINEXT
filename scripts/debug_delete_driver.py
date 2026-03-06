
import asyncio
import sys
import os

# Set up path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Sofor, Sefer
from sqlalchemy import select

async def debug_driver_deletion(driver_name_fragment: str):
    async with AsyncSessionLocal() as db:
        print(f"--- Searching for driver containing '{driver_name_fragment}' ---")
        stmt = select(Sofor).where(Sofor.ad_soyad.ilike(f"%{driver_name_fragment}%"))
        result = await db.execute(stmt)
        drivers = result.scalars().all()
        
        if not drivers:
            print("No driver found!")
            return

        for driver in drivers:
            print(f"Found Driver: ID={driver.id}, Name={driver.ad_soyad}, Active={driver.aktif}")
            
            # Check Sefer relations
            stmt_sefer = select(Sefer).where(Sefer.sofor_id == driver.id)
            result_sefer = await db.execute(stmt_sefer)
            seferler = result_sefer.scalars().all()
            print(f"  -> Associated Sefer (Trips) Count: {len(seferler)}")
            
            # Attempt Hard Delete
            print(f"  -> Attempting HARD DELETE on ID {driver.id}...")
            try:
                await db.delete(driver)
                await db.commit()
                print("  -> SUCCESS: Driver deleted.")
            except Exception as e:
                await db.rollback()
                print(f"  -> FAILED: {type(e).__name__}: {str(e)}")
                # Check for other potential FKs?

async def check_excel_routes():
    # Simple check if we can import the router structure or similar? 
    # Actually, let's just use requests/curl in the next step. 
    # This script focuses on the DB logic.
    pass

if __name__ == "__main__":
    name = "Mehmet Can" # The passive driver mentioned previously
    asyncio.run(debug_driver_deletion(name))
