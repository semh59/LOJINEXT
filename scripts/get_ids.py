import asyncio
import httpx

ADMIN_USER = "skara"
ADMIN_PASS = "!23efe25ali!"


async def get_ids():
    url = "http://localhost:8000/api/v1"
    async with httpx.AsyncClient(base_url=url, timeout=30.0) as client:
        login_res = await client.post(
            "/auth/token", data={"username": ADMIN_USER, "password": ADMIN_PASS}
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        v_res = await client.get(
            "/vehicles/", headers=headers, params={"aktif_only": True}
        )
        d_res = await client.get(
            "/drivers/", headers=headers, params={"aktif_only": True}
        )

        vehicles = v_res.json()
        drivers = d_res.json()

        v_id = vehicles[0]["id"] if vehicles else None
        d_id = drivers[0]["id"] if drivers else None

        print(f"VEHICLE_ID={v_id}")
        print(f"DRIVER_ID={d_id}")


if __name__ == "__main__":
    asyncio.run(get_ids())
