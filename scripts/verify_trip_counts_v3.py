import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())


async def verify_trip_counts_v3():
    print("Initializing Database Connection...")
    try:
        from app.database.connection import AsyncSessionLocal
        from app.database.repositories.sefer_repo import SeferRepository
        from app.core.services.sefer_service import SeferService
    except ImportError as e:
        print(f"Import Error: {e}")
        return

    # 1. Test Repository Directly
    async with AsyncSessionLocal() as session:
        repo = SeferRepository(session)
        print("--- REPOSITORY TEST ---")
        count = await repo.count_all()
        print(f"TOTAL TRIPS IN DATABASE: {count}")

        paged_data = await repo.get_all(offset=0, limit=100)
        print(f"RETRIEVED ROWS (LIMIT 100): {len(paged_data)}")

    # 2. Test Service Layer (The one used by API)
    print("\n--- SERVICE LAYER TEST ---")
    service = SeferService(repo)  # We can inject the repo or use get_sefer_service

    # Using get_sefer_service to be more realistic as it uses dependency injection
    from app.core.services.sefer_service import get_sefer_service

    service = get_sefer_service()

    result = await service.get_all_paged(skip=0, limit=100)

    print(f"Result structure keys: {list(result.keys())}")

    if "meta" in result and "items" in result:
        print("✅ SUCCESS: Found 'meta' and 'items' in response.")
        print(f"Total in meta: {result['meta']['total']}")
        print(f"Items count: {len(result['items'])}")

        if result["meta"]["total"] == 20000 and len(result["items"]) == 100:
            print("\n🎉 VERIFIED: Discrepancy resolved and schema synchronized!")
        else:
            print(f"\n❌ FAILURE: Stats mismatch. Total: {result['meta']['total']}")
    else:
        print("❌ FAILURE: Missing 'meta' or 'items' keys in service response.")


if __name__ == "__main__":
    asyncio.run(verify_trip_counts_v3())
