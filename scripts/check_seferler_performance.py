import asyncio
import os
import sys
import tracemalloc
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.services.sefer_read_service import SeferReadService
from app.database.connection import AsyncSessionLocal
from app.database.repositories.sefer_repo import get_sefer_repo


async def test_export_memory():
    async with AsyncSessionLocal() as session:
        repo = get_sefer_repo(session=session)
        service = SeferReadService(repo=repo)

        # Start tracing
        tracemalloc.start()
        start_time = time.time()

        # Fetch 5000 items (simulation of MAX_EXPORT_LIMIT)
        print("Fetching 5000 items from read service...")
        try:
            result = await service.get_all_paged(skip=0, limit=5000, aktif_only=False)
            items = result.get("items", [])
            print(f"Fetched {len(items)} items")
        except Exception as e:
            print(f"Error: {e}")

        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"Time Taken: {end_time - start_time:.2f} seconds")
        print(f"Current Memory: {current / 10**6:.2f} MB")
        print(f"Peak Memory: {peak / 10**6:.2f} MB")


if __name__ == "__main__":
    asyncio.run(test_export_memory())
