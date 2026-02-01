import sys
import os
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Kullanici
from app.core.security import get_password_hash
import asyncio
from sqlalchemy import select

async def create_user():
    async with AsyncSessionLocal() as db:
        username = "skara"
        password = "!23efe25ali!"
        
        result = await db.execute(select(Kullanici).where(Kullanici.kullanici_adi == username))
        user = result.scalars().first()
        
        if user:
            print(f"User {username} exists. Updating password...")
            user.sifre_hash = get_password_hash(password)
            user.aktif = True
            user.rol = "admin"
        else:
            print(f"User {username} not found. Creating...")
            user = Kullanici(
                kullanici_adi=username,
                sifre_hash=get_password_hash(password),
                ad_soyad="Admin User",
                aktif=True,
                rol="admin"
            )
            db.add(user)
        
        await db.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(create_user())
