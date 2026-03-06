import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.repositories.sefer_repo import SeferRepository


async def check_trips():
    print("Checking last 5 trips in DB...")
    async with AsyncSessionLocal() as session:
        repo = SeferRepository(session=session)
        trips = await repo.get_all(limit=5)

        print(f"Found {len(trips)} trips.")
        for t in trips:
            print(
                f"ID: {t['id']}, Tarih: {t['tarih']}, Guzergah ID: {t['guzergah_id']}, Cikis: {t['cikis_yeri']}, Varis: {t['varis_yeri']}"
            )


if __name__ == "__main__":
    asyncio.run(check_trips())
