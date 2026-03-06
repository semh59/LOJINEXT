import asyncio
import httpx

# Removed app import to run standalone


async def verify_stats():
    base_url = "http://localhost:8000/api/v1"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Login to get token
        login_res = await client.post(
            f"{base_url}/auth/token",
            data={"username": "skara", "password": "!23efe25ali!"},
            headers={"content-type": "application/x-www-form-urlencoded"},
        )

        if login_res.status_code != 200:
            print(f"Login failed: {login_res.text}")
            return

        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get list of vehicles to find an ID
        print("Fetching vehicles...")
        vehicles_res = await client.get(f"{base_url}/vehicles/", headers=headers)
        if vehicles_res.status_code != 200:
            print(f"Failed to list vehicles: {vehicles_res.text}")
            return

        vehicles = vehicles_res.json()
        if not vehicles:
            print("No vehicles found to test.")
            return

        target_vehicle = vehicles[0]
        v_id = target_vehicle["id"]
        print(f"Testing stats for Vehicle ID: {v_id} ({target_vehicle['plaka']})")

        # Call new stats endpoint
        stats_res = await client.get(
            f"{base_url}/vehicles/{v_id}/stats", headers=headers
        )

        if stats_res.status_code == 200:
            stats = stats_res.json()
            print("✅ Stats retrieved successfully!")
            print(f"Total Trips: {stats.get('toplam_sefer')}")
            print(f"Total KM: {stats.get('toplam_km')}")
            print(f"Avg Consumption: {stats.get('ort_tuketim')}")
        else:
            print(f"❌ Failed to get stats: {stats_res.status_code} - {stats_res.text}")


if __name__ == "__main__":
    asyncio.run(verify_stats())
