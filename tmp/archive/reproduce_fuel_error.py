import asyncio
import os
import sys
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from app.database.repositories.yakit_repo import get_yakit_repo
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


async def reproduce():
    repo = get_yakit_repo()
    try:
        print("Testing get_all with date objects...")
        results = await repo.get_all(
            baslangic_tarih=date(2020, 1, 1),
            bitis_tarih=date(2026, 12, 31),
            limit=10,
            offset=0,
        )
        print(f"Success! Found {len(results)} records.")
        for r in results[:2]:
            print(f"Record: {r}")

    except Exception as e:
        print(f"FAILED with error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(reproduce())
