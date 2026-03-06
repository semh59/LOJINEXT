import asyncio
from app.database.connection import AsyncSessionLocal
from app.database.models import Kullanici
from sqlalchemy import select


async def check_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Kullanici))
        users = result.scalars().all()
        print(f"DATABASE USERS FOUND: {len(users)}")
        for u in users:
            print(f" - {u.kullanici_adi} (Role: {u.rol}, Active: {u.aktif})")


if __name__ == "__main__":
    asyncio.run(check_users())
