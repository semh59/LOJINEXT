import asyncio
import httpx


async def check():
    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
        # 1. Login
        resp = await client.post(
            "/auth/token", data={"username": "skara", "password": "!23efe25ali!"}
        )
        if resp.status_code != 200:
            print("Login failed:", resp.text)
            return

        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Test Admin Users
        resp2 = await client.get("/admin/users/", headers=headers)
        print("Admin users status:", resp2.status_code)
        print("Admin users response:", resp2.text[:200])

        # 3. Test Admin Stats
        resp3 = await client.get("/admin/health/", headers=headers)
        print("Admin health status:", resp3.status_code)
        print("Admin health response:", resp3.text[:200])


if __name__ == "__main__":
    asyncio.run(check())
