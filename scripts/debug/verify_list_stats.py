import asyncio
import httpx


async def verify_list_stats():
    base_url = "http://localhost:8000/api/v1"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Login
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

        print("Fetching vehicle list...")
        res = await client.get(f"{base_url}/vehicles/", headers=headers)

        if res.status_code != 200:
            print(f"Failed: {res.status_code} - {res.text}")
            return

        vehicles = res.json()
        print(f"Fetched {len(vehicles)} vehicles.")

        if vehicles:
            v = vehicles[0]
            print(f"Vehicle: {v['plaka']}")
            print(f"  Total KM: {v.get('toplam_km')}")
            print(f"  Avg Cons: {v.get('ort_tuketim')}")
            print(f"  target Cons: {v.get('hedef_tuketim')}")

            if "toplam_km" in v and "ort_tuketim" in v:
                print("✅ New fields present.")
            else:
                print("❌ New fields MISSING.")


if __name__ == "__main__":
    asyncio.run(verify_list_stats())
