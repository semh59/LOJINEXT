import asyncio
import httpx
from datetime import date

BASE_URL = "http://localhost:8000"


async def get_token():
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/auth/token",
            data={"username": "admin", "password": "admin123"},
        )
        if resp.status_code != 200:
            return None
        return resp.json()["access_token"]


async def test_roundtrip():
    token = await get_token()
    if not token:
        print("❌ FAILED: Could not get auth token.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Fetch references
        v_resp = await client.get(f"{BASE_URL}/api/v1/vehicles/", headers=headers)
        d_resp = await client.get(f"{BASE_URL}/api/v1/drivers/", headers=headers)

        vehicles = v_resp.json()
        if isinstance(vehicles, dict) and "items" in vehicles:
            vehicles = vehicles["items"]
        drivers = d_resp.json()
        if isinstance(drivers, dict) and "items" in drivers:
            drivers = drivers["items"]

        if not vehicles or not drivers:
            print("❌ FAILED: No vehicles or drivers found.")
            return

        v_id = vehicles[0]["id"]
        d_id = drivers[0]["id"]

        # 2. Create Round-trip with Backhaul (Loaded Return)
        sn_base = f"RT-TEST-{int(asyncio.get_event_loop().time())}"
        payload = {
            "tarih": date.today().isoformat(),
            "arac_id": v_id,
            "sofor_id": d_id,
            "cikis_yeri": "Istanbul",
            "varis_yeri": "Ankara",
            "mesafe_km": 450,
            "net_kg": 20000,
            "sefer_no": sn_base,
            "is_round_trip": True,
            "return_net_kg": 15000,  # Backhaul (Yüklü Dönüş)
            "return_sefer_no": f"{sn_base}-RET",
        }

        print(
            f"--- Creating Round-trip: Istanbul -> Ankara (20t) & Ankara -> Istanbul (15t) ---"
        )
        resp = await client.post(
            f"{BASE_URL}/api/v1/trips/", headers=headers, json=payload
        )

        if resp.status_code != 200:
            print(f"❌ FAILED: POST /trips/ returned {resp.status_code}")
            print(f"Response: {resp.text}")
            return

        outward_id = resp.json()
        print(f"Outward Trip ID: {outward_id}")

        # 3. Verify IDs and Details
        # Fetch all trips filtered by Sefer No base
        list_resp = await client.get(
            f"{BASE_URL}/api/v1/trips/?search={sn_base}", headers=headers
        )
        trips_data = list_resp.json()
        trips = (
            trips_data.get("items", []) if isinstance(trips_data, dict) else trips_data
        )

        print(f"Found {len(trips)} trips matching {sn_base}")

        for t in sorted(trips, key=lambda x: x.get("sefer_no", "")):
            print(
                f"Trip {t['sefer_no']}: {t['cikis_yeri']} -> {t['varis_yeri']} | Load: {t['net_kg']}kg | Pred: {t['tahmini_tuketim']}L"
            )

        if len(trips) >= 2:
            ret_trip = next(
                (t for t in trips if t.get("sefer_no") == f"{sn_base}-RET"), None
            )
            if ret_trip:
                print("✅ SUCCESS: Return trip created automatically.")
                if ret_trip["net_kg"] == 15000 and ret_trip["cikis_yeri"] == "Ankara":
                    print("✅ SUCCESS: Return trip details (Backhaul) are correct.")
                else:
                    print(f"❌ FAILED: Return trip details mismatch: {ret_trip}")
            else:
                print("❌ FAILED: Return trip with predicted Sefer No not found.")
        else:
            print("❌ FAILED: Round-trip did not create two records.")


if __name__ == "__main__":
    asyncio.run(test_roundtrip())
