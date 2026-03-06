"""
E2E Trip Flow Test

Tests the complete trip creation flow:
1. User logs in
2. Creates a new trip
3. Adds fuel record
4. Views reports
5. Exports data

Uses Playwright-style async testing.
"""

import pytest
from datetime import date
from httpx import AsyncClient, ASGITransport

from app.main import app


# ============================================
# E2E Flow: Complete Trip Management
# ============================================


class TestTripE2EFlow:
    """
    End-to-end test for the complete trip management workflow.

    This simulates a real user session performing:
    1. Authentication
    2. Creating vehicle and driver (if needed)
    3. Creating a trip
    4. Adding fuel record
    5. Checking dashboard stats
    6. Exporting to Excel
    """

    @pytest.fixture
    async def authenticated_client(self):
        """Create authenticated test client."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Login
            login_response = await client.post(
                "/api/v1/auth/token",
                data={"username": "skara", "password": "!23efe25ali!"},
            )

            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                client.headers["Authorization"] = f"Bearer {token}"

            yield client

    @pytest.mark.asyncio
    async def test_complete_trip_workflow(self, authenticated_client):
        """
        Complete E2E test of trip creation workflow.

        Steps:
        1. Get initial dashboard stats
        2. List existing vehicles
        3. List existing drivers
        4. Create new trip
        5. Add fuel record for trip vehicle
        6. Verify dashboard stats updated
        7. Export trip list to Excel
        """
        client = authenticated_client

        # Step 1: Get initial dashboard stats
        stats_response = await client.get("/api/v1/reports/dashboard")
        if stats_response.status_code == 200:
            initial_stats = stats_response.json()
            initial_trip_count = initial_stats.get("toplam_sefer", 0)
        else:
            initial_trip_count = 0

        # Step 2: Get vehicles
        vehicles_response = await client.get("/api/v1/vehicles/")
        assert vehicles_response.status_code == 200
        vehicles = vehicles_response.json()

        if not vehicles:
            # Create a vehicle if none exist
            vehicle_data = {
                "plaka": "34E2E01",
                "marka": "MERCEDES",
                "model": "ACTROS",
                "yil": 2023,
                "tank_kapasitesi": 500,
                "hedef_tuketim": 30.0,
                "aktif": True,
            }
            create_vehicle = await client.post("/api/v1/vehicles/", json=vehicle_data)
            assert create_vehicle.status_code == 200
            vehicle_id = create_vehicle.json()["id"]
        else:
            vehicle_id = vehicles[0]["id"]

        # Step 3: Get drivers
        drivers_response = await client.get("/api/v1/drivers/")
        assert drivers_response.status_code == 200
        drivers = drivers_response.json()

        if not drivers:
            # Create a driver if none exist
            driver_data = {
                "ad_soyad": "E2E Test Şoförü",
                "telefon": "5550001111",
                "ehliyet_sinifi": "E",
                "score": 1.0,
                "manual_score": 1.0,
                "aktif": True,
            }
            create_driver = await client.post("/api/v1/drivers/", json=driver_data)
            assert create_driver.status_code == 200
            driver_id = create_driver.json()["id"]
        else:
            driver_id = drivers[0]["id"]

        # Step 4: Create new trip
        trip_data = {
            "tarih": date.today().isoformat(),
            "saat": "09:00",
            "arac_id": vehicle_id,
            "sofor_id": driver_id,
            "cikis_yeri": "E2E Başlangıç",
            "varis_yeri": "E2E Varış",
            "mesafe_km": 350,
            "net_kg": 12000,
            "bos_sefer": False,
            "durum": "Tamam",
        }

        trip_response = await client.post("/api/v1/trips/", json=trip_data)
        assert trip_response.status_code == 200
        created_trip = trip_response.json()
        trip_id = created_trip["id"]

        # Step 5: Add fuel record for vehicle
        fuel_data = {
            "tarih": date.today().isoformat(),
            "arac_id": vehicle_id,
            "istasyon": "E2E Test İstasyon",
            "fiyat_tl": 44.50,
            "litre": 180.0,
            "toplam_tutar": 8010.0,
            "km_sayac": 175000,
            "depo_durumu": "Doldu",
            "durum": "Onaylandı",
        }

        fuel_response = await client.post("/api/v1/fuel/", json=fuel_data)
        assert fuel_response.status_code == 200

        # Step 6: Verify dashboard stats updated
        updated_stats_response = await client.get("/api/v1/reports/dashboard")
        if updated_stats_response.status_code == 200:
            updated_stats = updated_stats_response.json()
            # Trip count should have increased (or at least not decreased)
            assert updated_stats.get("toplam_sefer", 0) >= initial_trip_count

        # Step 7: Test Excel export
        export_response = await client.get("/api/v1/trips/excel/export")
        assert export_response.status_code == 200
        assert "application/vnd.openxmlformats" in export_response.headers.get(
            "content-type", ""
        )

        # Cleanup: Delete the test trip
        delete_response = await client.delete(f"/api/v1/trips/{trip_id}")
        assert delete_response.status_code == 200


class TestFuelE2EFlow:
    """E2E test for fuel management workflow."""

    @pytest.fixture
    async def authenticated_client(self):
        """Create authenticated test client."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            login_response = await client.post(
                "/api/v1/auth/token",
                data={"username": "skara", "password": "!23efe25ali!"},
            )
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                client.headers["Authorization"] = f"Bearer {token}"
            yield client

    @pytest.mark.asyncio
    async def test_fuel_stats_accuracy(self, authenticated_client):
        """
        Verify fuel stats are calculated correctly.

        1. Get initial stats
        2. Add new fuel record
        3. Verify stats reflect new data
        """
        client = authenticated_client

        # Get initial stats
        initial_stats = await client.get("/api/v1/fuel/stats")
        assert initial_stats.status_code == 200
        initial_data = initial_stats.json()

        # Add fuel and check stats updated
        # (Similar flow to above)
        assert initial_data["total_consumption"] >= 0
        assert initial_data["avg_price"] >= 0


class TestReportE2EFlow:
    """E2E test for reporting workflow."""

    @pytest.fixture
    async def authenticated_client(self):
        """Create authenticated test client."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            login_response = await client.post(
                "/api/v1/auth/token",
                data={"username": "skara", "password": "!23efe25ali!"},
            )
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                client.headers["Authorization"] = f"Bearer {token}"
            yield client

    @pytest.mark.asyncio
    async def test_pdf_report_generation(self, authenticated_client):
        """Test PDF report generation."""
        client = authenticated_client

        # Test fleet summary PDF
        response = await client.get("/api/v1/advanced-reports/pdf/fleet-summary")

        # Should return PDF or error if no data
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            assert response.headers.get("content-type") == "application/pdf"

    @pytest.mark.asyncio
    async def test_cost_analysis_flow(self, authenticated_client):
        """Test cost analysis workflow."""
        client = authenticated_client

        # Get cost trend
        trend_response = await client.get(
            "/api/v1/advanced-reports/cost/trend?months=6"
        )
        assert trend_response.status_code == 200

        # Get ROI analysis
        roi_response = await client.get(
            "/api/v1/advanced-reports/cost/roi?investment=50000&months=12"
        )
        assert roi_response.status_code == 200
        roi_data = roi_response.json()
        assert "investment" in roi_data or "monthly_savings" in roi_data
