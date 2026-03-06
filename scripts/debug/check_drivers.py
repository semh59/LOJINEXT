import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Sofor

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Sofor))
        drivers = res.scalars().all()
        print(f"Total drivers in DB: {len(drivers)}")
        for d in drivers:
            print(f"ID: {d.id}, Name: {d.ad_soyad}, Manual: {d.manual_score}, Score: {d.score}, Active: {d.aktif}")

if __name__ == "__main__":
    asyncio.run(check())
