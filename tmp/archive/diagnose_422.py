import pytest
from httpx import AsyncClient
from datetime import date

from app.main import app
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_create_trip_missing_guzergah_id():
    from httpx import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # 1. Admin Login (Mock token is enough if we override dependency, but let's use real token logic)
        token = create_access_token(data={"sub": "admin", "rol": "admin"})
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Payload with missing guzergah_id
        payload = {
            "tarih": str(date.today()),
            "saat": "10:00",
            "arac_id": 1,
            "sofor_id": 1,
            # "guzergah_id": MISSING,
            "cikis_yeri": "Istanbul",
            "varis_yeri": "Izmir",
            "mesafe_km": 500,
            "bos_sefer": False,
            "durum": "Tamam",
        }

        response = await ac.post("/api/v1/seferler/", json=payload, headers=headers)

        print(f"\nStatus: {response.status_code}")
        print(f"Body: {response.json()}")

        # We expect 201 Created (if optional) or 422 Unprocessable Entity (if mandatory)
        # The goal is to make it optional, so if it returns 422, reproduction is successful.
        if response.status_code == 422:
            print("✅ Reproduction SUCCESS: 422 Unprocessable Entity received.")
        elif response.status_code == 201:
            print("❌ Reproduction FAILED: 201 Created received (Already optional?).")
        else:
            print(f"❌ Unexpected Status: {response.status_code}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_create_trip_missing_guzergah_id())
