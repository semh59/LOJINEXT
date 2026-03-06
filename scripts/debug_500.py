import asyncio
import httpx
from httpx import ASGITransport
import traceback

from app.main import app
from app.infrastructure.security.jwt_handler import create_access_token


async def test_endpoint():
    token = create_access_token({"sub": "skara"})
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testServer/api/v1"
    ) as client:
        try:
            print("--- Testing /admin/health/ ---")
            resp = await client.get("/admin/health/", headers=headers)
            print("Status:", resp.status_code)
            print("Response:", resp.text[:300])
        except Exception as e:
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_endpoint())
