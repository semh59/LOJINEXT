import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.repositories.guzergah_repo import GuzergahRepository


async def test_repo():
    print("Testing GuzergahRepository redirection to Lokasyonlar...")
    async with AsyncSessionLocal() as session:
        repo = GuzergahRepository(session=session)
        # We manually call the method we updated
        results = await repo.get_all_active()
        print(f"Found {len(results)} active routes.")
        for r in results:
            print(
                f"- ID: {r.get('id')}, Ad: {r.get('ad')}, Mesafe: {r.get('mesafe_km')}"
            )
    print("Test complete.")


if __name__ == "__main__":
    asyncio.run(test_repo())
