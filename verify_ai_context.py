import asyncio
import os
import sys

# Add project root to path
sys.path.append("/app")

from app.core.services.ai_service import get_ai_service
from app.database.session import async_session
from app.database.models import Kullanici
from sqlalchemy import select


async def test_ai_context():
    ai = get_ai_service()
    async with async_session() as session:
        # Find skara user
        res = await session.execute(
            select(Kullanici).where(Kullanici.kullanici_adi == "skara")
        )
        user = res.scalars().first()

        if not user:
            print("ERROR: User 'skara' not found in database.")
            return

        print(f"DEBUG: Found user {user.kullanici_adi} with role {user.rol}")

        # Build context
        ctx = await ai._build_context(user_id=user.id)

        print("\n--- AI CONTEXT PREVIEW ---")
        print(ctx)
        print("--- END PREVIEW ---\n")

        if "AKTİF KULLANICI BİLGİSİ" in ctx and "SUPERADMIN" in ctx:
            print("SUCCESS: AI context correctly identifies Super Admin.")
        else:
            print("FAILURE: AI context missing Super Admin info.")


if __name__ == "__main__":
    try:
        asyncio.run(test_ai_context())
    except Exception as e:
        import traceback

        traceback.print_exc()
