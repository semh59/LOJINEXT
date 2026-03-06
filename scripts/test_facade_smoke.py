import asyncio
from app.core.services.sefer_service import SeferService
from app.core.entities.models import SeferCreate
from datetime import date


async def smoke_test_facade():
    print("--- Starting SeferService Facade Smoke Test ---")
    service = SeferService()

    print("\n1. Testing Sub-Service Initialization...")
    assert service.read_service is not None, "Read Service not initialized"
    assert service.write_service is not None, "Write Service not initialized"
    assert service.analiz_service is not None, "Analiz Service not initialized"
    print("✅ Sub-services initialized.")

    print("\n2. Testing Read Delegation (get_all_trips)...")
    try:
        trips = await service.get_all_trips(limit=1)
        print(f"✅ Read successful. Got {len(trips)} trips.")
    except Exception as e:
        print(f"❌ Read failed: {e}")

    print("\n--- Smoke Test Complete ---")


if __name__ == "__main__":
    asyncio.run(smoke_test_facade())
