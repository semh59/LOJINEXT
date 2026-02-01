
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Sofor
from app.schemas.sofor import SoforResponse
from sqlalchemy import select

async def diagnose():
    async with AsyncSessionLocal() as session:
        print("--- DUMPING ALL DRIVERS ---")
        stmt = select(Sofor).order_by(Sofor.id)
        result = await session.execute(stmt)
        drivers = result.scalars().all()
        
        valid_count = 0
        error_count = 0
        
        for d in drivers:
            status = "AKTIF" if d.aktif else "PASIF"
            name_repr = repr(d.ad_soyad)
            
            try:
                SoforResponse.model_validate(d)
                validation = "OK"
                valid_count += 1
            except Exception as e:
                validation = f"ERROR: {e}"
                error_count += 1
                
            print(f"ID: {d.id} | Name: {name_repr} | Status: {status} | VALIDATION: {validation}")

        print(f"Total: {len(drivers)} | Valid: {valid_count} | Errors: {error_count}")

if __name__ == "__main__":
    asyncio.run(diagnose())
