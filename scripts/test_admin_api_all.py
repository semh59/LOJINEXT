import asyncio
import httpx
from httpx import ASGITransport
import traceback

from app.main import app
from app.infrastructure.security.jwt_handler import create_access_token


async def test_endpoint():
    token = create_access_token({"sub": "skara"})
    headers = {"Authorization": f"Bearer {token}"}

    endpoints = [
        "/admin/users/",
        "/admin/health/",
        "/admin/config/",
        "/admin/stats",
        "/admin/system/logs",
        "/admin/system/metrics",
        "/admin/roles/",
        "/admin/audit-logs",
        "/admin/usage",
    ]

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testServer/api/v1"
    ) as client:
        for ep in endpoints:
            try:
                print(f"--- Testing {ep} ---")
                resp = await client.get(ep, headers=headers)
                print(f"Status: {resp.status_code}")
                # Print response only if not 200, or just first 100 chars
                print(f"Response: {resp.text[:100]}...\n")
            except Exception as e:
                print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_endpoint())
