import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import engine
from app.database.models import Kullanici
from app.core.security import get_password_hash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

async def create_admin():
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user exists
        stmt = select(Kullanici).where(Kullanici.kullanici_adi == "admin")
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        hashed_pw = get_password_hash("admin123")
        
        if user:
            print("Updating existing admin user...")
            user.sifre_hash = hashed_pw
            user.aktif = True
            user.rol = "admin"
        else:
            print("Creating new admin user...")
            user = Kullanici(
                kullanici_adi="admin",
                sifre_hash=hashed_pw,
                ad_soyad="Sistem Yöneticisi",
                rol="admin",
                aktif=True
            )
            session.add(user)
            
        await session.commit()
        print("SUCCESS: Admin user 'admin' with password 'admin123' is ready.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_admin())
