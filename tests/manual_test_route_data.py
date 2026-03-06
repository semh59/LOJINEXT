import asyncio
import httpx
from datetime import date

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "skara"
PASSWORD = "!23efe25ali!"


async def get_token(client):
    response = await client.post(
        f"{BASE_URL}/auth/token",
        data={"username": USERNAME, "password": PASSWORD},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return None
    return response.json()["access_token"]


async def test_route_integration():
    async with httpx.AsyncClient(timeout=60.0) as client:
        token = await get_token(client)
        if not token:
            return

        headers = {"Authorization": f"Bearer {token}"}

        print("\n--- 1. Testing Route Creation with OpenRoute Data ---")
        # Istanbul (approx) -> Ankara (approx)
        # Using real coordinates to trigger OpenRouteService
        route_data = {
            "cikis_yeri": "Test Istanbul",
            "varis_yeri": "Test Ankara",
            "mesafe_km": 450,  # Initial guess, API should update/augment
            "tahmini_sure_saat": 5,
            "zorluk": "Normal",
            # Coordinates for OpenRouteService
            "cikis_lat": 41.0082,
            "cikis_lon": 28.9784,
            "varis_lat": 39.9334,
            "varis_lon": 32.8597,
            "notlar": "Test route for integration verification",
        }

        response = await client.post(
            f"{BASE_URL}/locations/", json=route_data, headers=headers
        )

        if response.status_code not in [200, 201]:
            print(f"Route creation failed: {response.text}")
            return

        route = response.json()
        route_id = route["id"]
        print(f"Route created: ID {route_id}")

        # Verify OpenRoute data
        print(f"Flat Distance: {route.get('flat_distance_km')}")
        print(f"Ascent: {route.get('ascent_m')}")
        print(f"API Distance: {route.get('api_mesafe_km')}")

        if route.get("flat_distance_km", 0) > 0:
            print("SUCCESS: Flat distance populated from OpenRouteService.")
        else:
            print("WARNING: Flat distance is 0. service might be down or mocking.")

        print("\n--- 2. Testing Trip Creation with Route Data Inheritance ---")
        # Create a Trip using this route
        # Need an active Vehicle and Driver first.
        # Assuming ID 1 exists for both for simplicity, or we fetch them.

        # Fetch a vehicle
        v_resp = await client.get(f"{BASE_URL}/vehicles/", headers=headers)
        vehicles = v_resp.json()
        if not vehicles:
            print("No vehicles found to test trip.")
            return
        vehicle_id = vehicles[0]["id"]

        # Fetch a driver
        d_resp = await client.get(f"{BASE_URL}/drivers/", headers=headers)
        drivers = d_resp.json()
        if not drivers:
            print("No drivers found to test trip.")
            return
        driver_id = drivers[0]["id"]

        trip_data = {
            "tarih": str(date.today()),
            "arac_id": vehicle_id,
            "sofor_id": driver_id,
            "guzergah_id": route_id,
            "cikis_yeri": "Test Istanbul",  # Should be overwritten or matched
            "varis_yeri": "Test Ankara",
            "mesafe_km": 450,
            "durum": "Planlandı",
        }

        t_resp = await client.post(
            f"{BASE_URL}/trips/", json=trip_data, headers=headers
        )
        if t_resp.status_code not in [200, 201]:
            print(f"Trip creation failed: {t_resp.text}")
            # Cleanup route
            await client.delete(f"{BASE_URL}/locations/{route_id}", headers=headers)
            return

        trip_resp = t_resp.json()
        if isinstance(trip_resp, dict):
            trip_id = trip_resp.get("id")
        else:
            trip_id = trip_resp
        print(f"Trip created: ID {trip_id}")

        # Fetch Trip Details to verify data copy
        # Note: Endpoints might vary, assuming /trips/{id}
        # If creates returns int, we need to fetch.

        trip_detail_resp = await client.get(
            f"{BASE_URL}/trips/{trip_id}", headers=headers
        )
        if trip_detail_resp.status_code == 200:
            trip = trip_detail_resp.json()
            print(f"Trip Flat Distance: {trip.get('flat_distance_km')}")

            if trip.get("flat_distance_km") == route.get("flat_distance_km"):
                print("SUCCESS: Trip inherited flat_distance_km from Route.")
            else:
                print(
                    f"FAILURE: Data mismatch. Route: {route.get('flat_distance_km')}, Trip: {trip.get('flat_distance_km')}"
                )
        else:
            print(f"Could not fetch trip details: {trip_detail_resp.text}")

        # Cleanup
        print("\n--- 3. Cleanup ---")
        await client.delete(f"{BASE_URL}/trips/{trip_id}", headers=headers)
        print("Trip deleted.")
        await client.delete(f"{BASE_URL}/locations/{route_id}", headers=headers)
        print("Route deleted.")


if __name__ == "__main__":
    asyncio.run(test_route_integration())
