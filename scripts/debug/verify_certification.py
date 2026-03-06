import asyncio
import sys
from httpx import AsyncClient, ASGITransport
from datetime import date
from decimal import Decimal

from app.main import app
from app.core.security import create_access_token


async def verify_certification():
    print("🚀 Starting Final Zero-Defect Certification (v4)...")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # 1. Admin Auth
        token = create_access_token(data={"sub": "skara", "rol": "admin"})
        headers = {"Authorization": f"Bearer {token}"}

        print("\n--- [SEEDING] Ensuring Test Data Exists ---")
        # Find or create vehicles
        v_list_resp = await ac.get("/api/v1/vehicles/", headers=headers)
        vehicles = v_list_resp.json()
        if not vehicles:
            print("🌱 Seeding Vehicle...")
            seed_v = await ac.post(
                "/api/v1/vehicles/",
                json={
                    "plaka": "34CERT01",
                    "marka": "Mercedes",
                    "model": "Actros",
                    "yil": 2022,
                    "aktif": True,
                },
                headers=headers,
            )
            v_id = seed_v.json()["id"]
        else:
            v_id = vehicles[0]["id"]
            if not vehicles[0].get("aktif"):
                await ac.put(
                    f"/api/v1/vehicles/{v_id}", json={"aktif": True}, headers=headers
                )

        # Find or create drivers
        d_list_resp = await ac.get("/api/v1/drivers/", headers=headers)
        drivers = d_list_resp.json()
        if not drivers:
            print("🌱 Seeding Driver...")
            seed_d = await ac.post(
                "/api/v1/drivers/",
                json={
                    "ad_soyad": "Zahit Sertifika",
                    "telefon": "5550001122",
                    "aktif": True,
                },
                headers=headers,
            )
            d_id = seed_d.json()["id"]
        else:
            d_id = drivers[0]["id"]
            if not drivers[0].get("aktif"):
                await ac.put(
                    f"/api/v1/drivers/{d_id}", json={"aktif": True}, headers=headers
                )

        print(f"Using Vehicle ID: {v_id}, Driver ID: {d_id}")

        print("\n--- [TEST 1] Sefer Creation (Missing optional guzergah_id) ---")
        trip_payload = {
            "tarih": str(date.today()),
            "saat": "12:00",
            "arac_id": v_id,
            "sofor_id": d_id,
            "cikis_yeri": "Ankara",
            "varis_yeri": "Bursa",
            "mesafe_km": 400.0,
            "bos_sefer": False,
            "durum": "Tamam",
        }

        response = await ac.post("/api/v1/trips/", json=trip_payload, headers=headers)
        if response.status_code == 201:
            print("✅ SUCCESS: Trip created without guzergah_id (422 Resolved).")
            new_trip_id = response.json()["id"]
        else:
            print(f"❌ FAILURE: Trip creation received status {response.status_code}")
            print(f"Body: {response.json()}")
            new_trip_id = None

        if new_trip_id:
            print("\n--- [TEST 2] Sefer Update (Partial Update via Service) ---")
            update_payload = {"notlar": "Phase 5 Verified Note"}
            update_resp = await ac.put(
                f"/api/v1/trips/{new_trip_id}", json=update_payload, headers=headers
            )

            if update_resp.status_code == 200:
                body = update_resp.json()
                if body.get("notlar") == "Phase 5 Verified Note":
                    print("✅ SUCCESS: Partial update verified via Service Layer.")
                else:
                    print(f"❌ FAILURE: Data mismatch. Got notes: {body.get('notlar')}")
            else:
                print(f"❌ FAILURE: Update failed status {update_resp.status_code}")
                print(f"Body: {update_resp.json()}")

        print("\n--- [TEST 3] Fuel Stats with Filters (Corrected Raw SQL) ---")
        stats_resp = await ac.get(
            "/api/v1/fuel/stats?baslangic_tarih=2024-01-01", headers=headers
        )
        if stats_resp.status_code == 200:
            print("✅ SUCCESS: Fuel stats retrieved via purified Service Layer.")
            print(f"Stats: {stats_resp.json()}")
        else:
            print(f"❌ FAILURE: Stats endpoint status {stats_resp.status_code}")
            print(f"Body: {stats_resp.json()}")

        print("\n--- [TEST 4] Fuel Creation & Update (Consistency Check) ---")
        fuel_payload = {
            "tarih": str(date.today()),
            "arac_id": v_id,
            "fiyat_tl": 41.50,
            "litre": 200.0,
            "toplam_tutar": 8300.0,
            "km_sayac": 150000,
            "depo_durumu": "Doldu",
        }
        f_create_resp = await ac.post(
            "/api/v1/fuel/", json=fuel_payload, headers=headers
        )
        if f_create_resp.status_code == 201:
            f_id = f_create_resp.json()["id"]
            print(f"🌱 Fuel record {f_id} created.")

            fuel_update = {"fis_no": "CERT-V-004"}
            fuel_resp = await ac.put(
                f"/api/v1/fuel/{f_id}", json=fuel_update, headers=headers
            )
            if fuel_resp.status_code == 200:
                print("✅ SUCCESS: Fuel record update verified (UoW + Service).")
            else:
                print(f"❌ FAILURE: Fuel update status {fuel_resp.status_code}")
                print(f"Body: {fuel_resp.json()}")
        else:
            print(f"❌ FAILURE: Fuel creation status {f_create_resp.status_code}")
            print(f"Body: {f_create_resp.json()}")

    print("\n🏁 Certification Process Complete.")


if __name__ == "__main__":
    asyncio.run(verify_certification())
