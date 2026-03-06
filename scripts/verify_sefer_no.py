import asyncio
import httpx

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


async def test_sefer_no():
    token = await get_token()
    if not token:
        print("❌ Auth failed")
        return

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        # 1. Get references
        v_resp = await client.get(f"{BASE_URL}/api/v1/vehicles/", headers=headers)
        d_resp = await client.get(f"{BASE_URL}/api/v1/drivers/", headers=headers)

        v_id = v_resp.json()[0]["id"]
        d_id = d_resp.json()[0]["id"]

        # 2. Create Trip with Sefer No
        test_no = f"TEST-SEF-{int(asyncio.get_event_loop().time())}"
        trip_data = {
            "tarih": "2024-05-21",
            "saat": "10:00",
            "arac_id": v_id,
            "sofor_id": d_id,
            "cikis_yeri": "Istanbul",
            "varis_yeri": "Ankara",
            "mesafe_km": 450,
            "net_kg": 20000,
            "sefer_no": test_no,
        }

        print(f"--- Testing Sefer No: {test_no} ---")
        resp = await client.post(
            f"{BASE_URL}/api/v1/trips/", headers=headers, json=trip_data
        )
        if resp.status_code in [200, 201]:
            print("✅ SUCCESS: Trip with Sefer No created.")
            print(f"DEBUG: POST Response: {resp.json()}")
        else:
            print(f"❌ FAILED: {resp.text}")
            return

        # 3. Test Duplicate Sefer No
        print("--- Testing Duplicate Sefer No ---")
        resp = await client.post(
            f"{BASE_URL}/api/v1/trips/", headers=headers, json=trip_data
        )
        if resp.status_code == 400 and "zaten kullanımda" in resp.text:
            print("✅ SUCCESS: Duplicate Sefer No blocked.")
        else:
            print(
                f"❌ FAILED: Duplicate not blocked or wrong error: {resp.status_code} {resp.text}"
            )

        # 4. Verify in GET List
        print("--- Verifying in GET /api/v1/trips/ ---")
        resp = await client.get(f"{BASE_URL}/api/v1/trips/", headers=headers)
        if resp.status_code == 200:
            trips = resp.json()
            # Find our created trip
            found = False
            for t in trips:
                if t.get("sefer_no") == test_no:
                    found = True
                    print(f"✅ SUCCESS: Sefer No '{test_no}' found in LIST response.")
                    break
            if not found:
                print(
                    f"❌ FAILED: Sefer No '{test_no}' NOT FOUND in list response or is null."
                )
                # Print the first trip for debugging
                if trips:
                    print(f"DEBUG: First trip keys: {list(trips[0].keys())}")
                    print(f"DEBUG: First trip sefer_no: {trips[0].get('sefer_no')}")
        else:
            print(f"❌ FAILED to get trips: {resp.status_code}")


if __name__ == "__main__":
    asyncio.run(test_sefer_no())
