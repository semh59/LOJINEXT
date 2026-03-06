import asyncio
from app.database.connection import AsyncSessionLocal
from app.database.models import Kullanici, Rol
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Kullanici)
            .options(selectinload(Kullanici.rol))
            .where(Kullanici.email == "skara")
        )
        user = result.scalar_one_or_none()
        if user:
            print(f"User: {user.email}")
            if user.rol:
                print(f"Role Name: '{user.rol.ad}'")
                print(f"Role Permissions: {user.rol.yetkiler}")
            else:
                print("No role")
        else:
            print("skara not found")


if __name__ == "__main__":
    asyncio.run(check())
