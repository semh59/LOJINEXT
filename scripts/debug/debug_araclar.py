import asyncio
import httpx

ADMIN_USER = "skara"
ADMIN_PASS = "!23efe25ali!"


async def debug_araclar():
    url = "http://localhost:8000/api/v1"
    async with httpx.AsyncClient(base_url=url, timeout=30.0) as client:
        # Login
        login_res = await client.post(
            "/auth/token", data={"username": ADMIN_USER, "password": ADMIN_PASS}
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get Vehicles - Correct Endpoint
        res = await client.get(
            "/vehicles/", headers=headers, params={"aktif_only": True}
        )
        print(f"Status: {res.status_code}")
        try:
            data = res.json()
            print(f"Type: {type(data)}")
            if isinstance(data, list):
                print(f"Count: {len(data)}")
                if len(data) > 0:
                    print(f"First item keys: {data[0].keys()}")
                    # print(f"First item: {data[0]}")
            else:
                print(f"Data: {data}")
        except Exception as e:
            print(f"Parse Error: {e}")
            print(f"Raw: {res.text}")


if __name__ == "__main__":
    asyncio.run(debug_araclar())
