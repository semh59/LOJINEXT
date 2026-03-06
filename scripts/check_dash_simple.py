import asyncio
import httpx
import sys
import os

sys.path.append(os.getcwd())
base_url = "http://127.0.0.1:8000/api/v1"


async def check():
    async with httpx.AsyncClient() as client:
        # Auth
        resp = await client.post(
            f"{base_url}/auth/token",
            data={"username": "skara", "password": "!23efe25ali!"},
        )
        if resp.status_code != 200:
            print("Auth Fail")
            return
        token = resp.json()["access_token"]

        # Dash
        resp = await client.get(
            f"{base_url}/reports/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = resp.json()
        print(f"Aktif Arac: {data.get('aktif_arac')}")
        print(f"Toplam Arac: {data.get('toplam_arac')}")


if __name__ == "__main__":
    asyncio.run(check())
