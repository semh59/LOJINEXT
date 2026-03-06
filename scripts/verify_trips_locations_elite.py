import asyncio
import json
import httpx
import sys

BASE_URL = "http://localhost:8000"


async def get_token():
    async with httpx.AsyncClient() as client:
        # FastAPI OAuth2PasswordRequestForm expects data, not json
        resp = await client.post(
            f"{BASE_URL}/api/v1/auth/token",
            data={"username": "admin", "password": "admin123"},
        )
        if resp.status_code != 200:
            print(f"❌ AUTH FAILED: {resp.text}")
            return None
        return resp.json()["access_token"]


async def test_branding_neutrality(headers):
    print("\n--- Testing Branding Neutrality ---")
    async with httpx.AsyncClient() as client:
        # Check Locations (uses LokasyonPaginationResponse which has 'items')
        resp = await client.get(f"{BASE_URL}/api/v1/locations/", headers=headers)
        data = resp.json()

        json_str = json.dumps(data).lower()
        forbidden = ["mapbox", "openrouteservice", "elite"]

        for word in forbidden:
            if word in json_str:
                print(f"❌ FAILED: Found forbidden word '{word}' in Location sequence")
                return False

        print("✅ SUCCESS: No internal/external branding found in Location outputs")
        return True


async def test_location_normalization(headers):
    print("\n--- Testing Location Normalization ---")
    async with httpx.AsyncClient() as client:
        # 1. Add "İSTANBUL -> ANKARA"
        await client.post(
            f"{BASE_URL}/api/v1/locations/",
            headers=headers,
            json={
                "cikis_yeri": "İSTANBUL",
                "varis_yeri": "ANKARA",
                "mesafe_km": 450,
                "zorluk": "Normal",
            },
        )

        # 2. Try adding "  istanbul -> ankara  "
        r2 = await client.post(
            f"{BASE_URL}/api/v1/locations/",
            headers=headers,
            json={
                "cikis_yeri": "  istanbul  ",
                "varis_yeri": "  ankara  ",
                "mesafe_km": 450,
                "zorluk": "Normal",
            },
        )

        if r2.status_code == 400 and "zaten mevcut" in r2.text:
            print(
                "✅ SUCCESS: Duplicate detection caught normalized name 'istanbul' vs 'İSTANBUL'"
            )
            return True
        else:
            print(
                f"❌ FAILED: Duplicate detection missed. Status: {r2.status_code}, Body: {r2.text}"
            )
            return False


async def test_trip_ton_calculation(headers):
    print("\n--- Testing Trip Ton Calculation ---")
    async with httpx.AsyncClient() as client:
        # Create a trip with kg, check if ton is calculated
        # First get an active vehicle and driver
        v_resp = await client.get(f"{BASE_URL}/api/v1/vehicles/", headers=headers)
        vehicles = v_resp.json()
        if not vehicles:
            print("❌ FAILED: No vehicles found to test")
            return False
        arac_id = vehicles[0]["id"]

        d_resp = await client.get(f"{BASE_URL}/api/v1/drivers/", headers=headers)
        drivers = d_resp.json()
        if not drivers:
            print("❌ FAILED: No drivers found to test")
            return False
        sofor_id = drivers[0]["id"]

        trip_data = {
            "tarih": "2024-05-20",
            "arac_id": arac_id,
            "sofor_id": sofor_id,
            "cikis_yeri": "Gebze",
            "varis_yeri": "Düzce",
            "mesafe_km": 150,
            "net_kg": 25000,  # 25 Ton
            "durum": "Tamam",
        }

        resp = await client.post(
            f"{BASE_URL}/api/v1/trips/", headers=headers, json=trip_data
        )
        if resp.status_code not in [200, 201]:
            print(f"❌ FAILED: Trip creation failed: {resp.text}")
            return False

        trip_id = resp.json()["id"]
        get_resp = await client.get(
            f"{BASE_URL}/api/v1/trips/{trip_id}", headers=headers
        )
        saved_trip = get_resp.json()

        if saved_trip.get("ton") == 25.0:
            print("✅ SUCCESS: Ton calculation (25000kg -> 25.0t) verified")
            return True
        else:
            print(
                f"❌ FAILED: Ton calculation mismatch. Expected 25.0, got {saved_trip.get('ton')}"
            )
            return False


async def main():
    token = await get_token()
    if not token:
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    s1 = await test_branding_neutrality(headers)
    s2 = await test_location_normalization(headers)
    s3 = await test_trip_ton_calculation(headers)

    if all([s1, s2, s3]):
        print("\n🏆 ALL ELITE AUDIT TESTS PASSED 100%")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
