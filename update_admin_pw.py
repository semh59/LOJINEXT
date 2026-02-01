
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from app.database.connection import AsyncSessionLocal
from app.database.models import Kullanici
from app.core.security import get_password_hash
from sqlalchemy import select

async def reset_password():
    print("Connecting to DB...")
    async with AsyncSessionLocal() as session:
        print("Searching for admin user...")
        # Check for both 'skara' and 'admin' just in case
        stmt = select(Kullanici).where(Kullanici.kullanici_adi.in_(['skara', 'admin']))
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        if not users:
            print("No admin user found to update!")
            return

        new_password = "!23efe25ali!"
        hashed = get_password_hash(new_password)

        for user in users:
            print(f"Updating password for user: {user.kullanici_adi}")
            user.sifre_hash = hashed
            session.add(user)
        
        await session.commit()
        print(f"SUCCESS: Password updated to '{new_password}' for users: {[u.kullanici_adi for u in users]}")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(reset_password())
    except Exception as e:
        print(f"ERROR: {e}")
