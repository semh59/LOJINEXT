import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())


async def verify_trip_counts():
    print("Initializing Database Connection...")
    from app.database.connection import get_db_session
    from app.database.repositories.sefer_repo import SeferRepository

    async with get_db_session() as session:
        repo = SeferRepository(session)
        print("Fetching Total Trip Count from Repository...")
        count = await repo.count_all()
        print(f"TOTAL TRIPS IN DATABASE: {count}")

        print("Testing Paginated Retrieval...")
        paged_data = await repo.get_all(offset=0, limit=100)
        print(f"RETRIEVED ROWS (LIMIT 100): {len(paged_data)}")

        if count == 20000:
            print("\n✅ SUCCESS: Repository correctly reports 20,000 trips.")
        else:
            print(
                f"\n❌ FAILURE: Expected 20,000 trips, but repository returned {count}."
            )


if __name__ == "__main__":
    asyncio.run(verify_trip_counts())
