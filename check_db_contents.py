import asyncio
import os
import sys

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Sofor, Arac
from sqlalchemy import select

async def check_db():
    print("Checking database contents...")
    try:
        async with AsyncSessionLocal() as db:
            sofor_result = await db.execute(select(Sofor))
            soforler = sofor_result.scalars().all()
            
            arac_result = await db.execute(select(Arac))
            araclar = arac_result.scalars().all()
            
            print(f"TOTAL DRIVERS found: {len(soforler)}")
            for s in soforler[:3]:
                print(f" - Driver: {s.ad_soyad} (Active: {s.aktif})")
                
            print(f"TOTAL VEHICLES found: {len(araclar)}")
            for a in araclar[:3]:
                print(f" - Vehicle: {a.plaka} (Active: {a.aktif})")
                
    except Exception as e:
        print(f"DATABASE ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
