import asyncio
import httpx
from datetime import date

BASE_URL = "http://localhost:8000"


async def get_token():
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/auth/token",
            data={"username": "admin", "password": "admin123"},
        )
        if resp.status_code != 200:
            return None
        return resp.json()["access_token"]


async def test_reprediction():
    token = await get_token()
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        # 1. Fetch references
        v_resp = await client.get(f"{BASE_URL}/api/v1/vehicles/", headers=headers)
        d_resp = await client.get(f"{BASE_URL}/api/v1/drivers/", headers=headers)
        l_resp = await client.get(f"{BASE_URL}/api/v1/locations/", headers=headers)

        vehicles = v_resp.json()
        if isinstance(vehicles, dict) and "items" in vehicles:
            vehicles = vehicles["items"]

        drivers = d_resp.json()
        if isinstance(drivers, dict) and "items" in drivers:
            drivers = drivers["items"]

        locations = l_resp.json()
        if isinstance(locations, dict) and "items" in locations:
            locations = locations["items"]

        print(f"DEBUG: Vehicles count: {len(vehicles)}")
        print(f"DEBUG: Drivers count: {len(drivers)}")
        print(f"DEBUG: Locations count: {len(locations)}")

        if not vehicles or not drivers:
            print("❌ Error: Need at least one vehicle and one driver to test.")
            return

        v_id = vehicles[0]["id"]
        d_id = drivers[0]["id"]

        l_id = None
        l_name = "N/A"
        if locations:
            l_id = locations[0]["id"]
            l_name = (
                locations[0].get("ad")
                or f"{locations[0].get('cikis_yeri')} - {locations[0].get('varis_yeri')}"
            )

        # 2. Create Initial Trip (Loaded)
        payload = {
            "tarih": date.today().isoformat(),
            "arac_id": v_id,
            "sofor_id": d_id,
            "cikis_yeri": "Test Local",
            "varis_yeri": "Test Dest",
            "mesafe_km": 100,
            "net_kg": 20000,
            "sefer_no": f"PRED-TEST-{int(asyncio.get_event_loop().time())}",
        }

        print(f"--- Creating Loaded Trip (20 tons) ---")
        resp = await client.post(
            f"{BASE_URL}/api/v1/trips/", headers=headers, json=payload
        )
        trip = resp.json()
        trip_id = trip["id"]
        initial_pred = trip.get("tahmini_tuketim")
        print(f"Initial Prediction: {initial_pred} L")

        # 3. Update Ton (Lighter)
        print(f"--- Updating Trip to 5 tons ---")
        update_payload = {"net_kg": 5000}
        resp = await client.put(
            f"{BASE_URL}/api/v1/trips/{trip_id}", headers=headers, json=update_payload
        )
        updated_trip = resp.json()
        new_pred = updated_trip.get("tahmini_tuketim")
        print(f"Updated Prediction: {new_pred} L")

        if initial_pred and new_pred and new_pred < initial_pred:
            print("✅ SUCCESS: Prediction decreased with lighter load.")
        elif not initial_pred:
            print("⚠️ WARNING: Initial prediction was null.")
        else:
            print(
                f"❌ FAILED: Prediction did not decrease ({initial_pred} -> {new_pred})."
            )

        # 4. Set Empty Return (bos_sefer=True)
        print(f"--- Setting bos_sefer=True ---")
        update_payload = {"bos_sefer": True}
        resp = await client.put(
            f"{BASE_URL}/api/v1/trips/{trip_id}", headers=headers, json=update_payload
        )
        empty_trip = resp.json()
        empty_pred = empty_trip.get("tahmini_tuketim")
        print(f"Empty Return Prediction: {empty_pred} L")

        if empty_pred is not None and (new_pred is None or empty_pred < new_pred):
            print("✅ SUCCESS: Prediction decreased significantly for empty return.")
        else:
            print(
                f"❌ FAILED: Empty return prediction mismatch ({new_pred} -> {empty_pred})."
            )

        # 5. Change Route (Should use route metadata)
        if l_id:
            print(f"--- Changing Route to '{l_name}' ---")
            update_payload = {"guzergah_id": l_id, "bos_sefer": False}
            resp = await client.put(
                f"{BASE_URL}/api/v1/trips/{trip_id}",
                headers=headers,
                json=update_payload,
            )
            route_trip = resp.json()
            route_pred = route_trip.get("tahmini_tuketim")
            print(f"New Route Prediction: {route_pred} L")
            print(f"Metadata used: Mesafe={route_trip.get('mesafe_km')}km")
        else:
            print("⏭️ Skipping route change test (no locations available).")


if __name__ == "__main__":
    asyncio.run(test_reprediction())
