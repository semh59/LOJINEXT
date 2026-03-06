import asyncio
import os
import sys

# Add app to path
sys.path.append(os.path.abspath(os.curdir))

from app.core.services.lokasyon_service import LokasyonService
from app.database.repositories.lokasyon_repo import get_lokasyon_repo
from app.schemas.lokasyon import LokasyonCreate

async def test_locations_logic():
    print("🚀 Starting Locations Logic Integration Test...")
    
    repo = get_lokasyon_repo()
    service = LokasyonService(repo=repo)
    
    # 1. Test Listing
    print("\n[1] Testing List Locations...")
    locations = await service.get_all_paged(limit=5)
    print(f"✅ Found {len(locations)} locations.")
    for loc in locations:
        print(f"   - {loc.cikis_yeri} -> {loc.varis_yeri} ({loc.mesafe_km} km)")

    # 2. Test Unique Names
    print("\n[2] Testing Unique Names...")
    names = await repo.get_benzersiz_lokasyonlar()
    print(f"✅ Found {len(names)} unique names.")
    if names:
        print(f"   - Sample: {names[:3]}")

    # 3. Test Create (Duplicate Check)
    print("\n[3] Testing Create/Duplicate Check...")
    test_data = LokasyonCreate(
        cikis_yeri="TEST_CITY_A",
        varis_yeri="TEST_CITY_B",
        mesafe_km=100,
        zorluk="Normal"
    )
    
    try:
        loc_id = await service.add_lokasyon(test_data)
        print(f"✅ Created new location: ID {loc_id}")
        
        # Try to duplicate
        try:
            await service.add_lokasyon(test_data)
            print("❌ Duplicate test FAILED (should have raised ValueError)")
        except ValueError as e:
            print(f"✅ Duplicate check PASSED: {e}")
            
        # Clean up (Soft Delete)
        print("\n[4] Testing Soft Delete...")
        await service.delete_lokasyon(loc_id)
        
        # Verify inactive
        check = await repo.get_by_id(loc_id)
        print(f"✅ Soft delete verification: aktif={check.get('aktif')}")
        
        # Test Reactivation
        print("\n[5] Testing Reactivation...")
        new_id = await service.add_lokasyon(test_data)
        print(f"✅ Reactivation test: ID matched? {loc_id == new_id}")
        
        # Hard delete for cleanup
        print("\n[6] Testing Hard Delete...")
        await service.delete_lokasyon(new_id) # Soft delete first
        await service.delete_lokasyon(new_id) # Hard delete second
        print("✅ Hard delete completed.")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_locations_logic())
