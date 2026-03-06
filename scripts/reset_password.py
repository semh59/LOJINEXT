import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.database.connection import AsyncSessionLocal
from app.database.models import Kullanici
from app.core.security import get_password_hash

USERNAME = "skara"
NEW_PASSWORD = "!23efe25ali!"


async def reset_password():
    print(f"Resetting password for {USERNAME}...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Kullanici).where(Kullanici.kullanici_adi == USERNAME)
        )
        user = result.scalar_one_or_none()

        if user:
            print(f"User found: {user.kullanici_adi}")
            hashed_pw = get_password_hash(NEW_PASSWORD)
            user.sifre_hash = hashed_pw
            await session.commit()
            print("Password updated successfully.")
        else:
            print("User NOT found!")


if __name__ == "__main__":
    asyncio.run(reset_password())
