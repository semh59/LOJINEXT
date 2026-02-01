"""
UI Backend Verification Script
Mimics the calls made by Dashboard and Vehicle Pages to ensure backend readiness.
"""
import os
import sys
import traceback

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.entities.models import AracCreate, AracUpdate
from app.core.services.arac_service import get_arac_service
from app.core.services.report_service import get_report_service
from app.database.db_manager import get_db


def test_dashboard_flow():
    print("\n--- Testing Dashboard Flow ---")
    report_service = get_report_service()

    try:
        # 1. Dashboard Summary
        summary = report_service.get_dashboard_summary()
        print(f"✅ Dashboard Summary Retrieved: {summary.keys()}")
        assert 'aktif_arac' in summary
        assert 'filo_ortalama' in summary

        # 2. Daily Trend (Chart Data)
        trend = report_service.get_daily_consumption_trend(days=7)
        print(f"✅ Daily Trend Retrieved: {len(trend)} days")

        # 3. Recent Trips (Table Data)
        db = get_db()
        recent = db.get_bugunun_seferleri()
        print(f"✅ Recent Trips Retrieved: {len(recent)} trips")

    except Exception as e:
        print(f"❌ Dashboard Flow Failed: {e}")
        traceback.print_exc()
        raise

def test_vehicles_page_flow():
    print("\n--- Testing Vehicles Page Flow ---")
    arac_service = get_arac_service()

    test_plaka = "34 UI 9876"

    try:
        # 1. List Vehicles (Grid View)
        vehicles = arac_service.get_all_vehicles()
        print(f"✅ Vehicle List Retrieved: {len(vehicles)} vehicles")

        # 2. Create Vehicle (Wizard Flow)
        # Cleanup if exists
        existing = arac_service.repo.get_by_plaka(test_plaka)
        if existing:
            arac_service.delete_arac(existing['id'])

        new_vehicle = AracCreate(
            plaka=test_plaka,
            marka="TestCar",
            model="UI Tester",
            yil=2024,
            tank_kapasitesi=500,
            hedef_tuketim=28.5
        )

        arac_id = arac_service.create_arac(new_vehicle)
        print(f"✅ Vehicle Created via Wizard Logic: ID {arac_id}")

        # 3. Get Vehicle Stats (Card Detail)
        stats = arac_service.get_vehicle_stats(arac_id)
        print(f"✅ Vehicle Stats Retrieved: {stats}")

        # 4. Update Vehicle
        update_data = AracUpdate(notlar="Updated via UI Test")
        arac_service.update_arac(arac_id, update_data)
        updated_vehicle = arac_service.get_by_id(arac_id)
        assert updated_vehicle.notlar == "Updated via UI Test"
        print("✅ Vehicle Updated Successfully")

        # Cleanup
        arac_service.delete_arac(arac_id)
        print("✅ Cleanup Done")

    except Exception as e:
        print(f"❌ Vehicles Page Flow Failed: {e}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    try:
        test_dashboard_flow()
        test_vehicles_page_flow()
        print("\n🎉 ALL UI BACKEND TESTS PASSED!")
    except Exception as e:
        print(f"\n💥 TESTS FAILED: {e}")
        sys.exit(1)
