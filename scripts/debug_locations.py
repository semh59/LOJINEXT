import asyncio
import os
import sys
from sqlalchemy import select

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Lokasyon


async def debug_locations():
    async with AsyncSessionLocal() as db:
        stmt = select(Lokasyon)
        result = await db.execute(stmt)
        locations = result.scalars().all()

        print("\n--- LOCATIONS IN DB ---")
        for loc in locations:
            print(f"ID: {loc.id} | {loc.cikis_yeri} -> {loc.varis_yeri}")


if __name__ == "__main__":
    asyncio.run(debug_locations())
