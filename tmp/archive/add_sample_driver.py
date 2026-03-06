import asyncio
import os
import sys

sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Sofor

async def add_sample():
    async with AsyncSessionLocal() as db:
        s = Sofor(
            ad_soyad='Ahmet Örnek', 
            telefon='0555 111 22 33', 
            ehliyet_sinifi='E', 
            aktif=True, 
            score=1.8,
            ise_baslama='2024-01-01'
        )
        db.add(s)
        await db.commit()
        print("Sample driver 'Ahmet Örnek' added to database.")

if __name__ == "__main__":
    asyncio.run(add_sample())
