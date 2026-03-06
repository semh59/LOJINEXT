import asyncio
import httpx
import sys
import os

sys.path.append(os.getcwd())

from app.core.security import create_access_token


async def verify_forecast():
    # Mock admin token
    token = create_access_token({"sub": "admin", "id": 1, "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(
        base_url="http://localhost:8000/api/v1", timeout=30.0
    ) as client:
        print("Testing /predictions/forecast...")
        response = await client.get("/predictions/forecast", headers=headers)

        if response.status_code == 200:
            data = response.json()
            print("Status: SUCCESS")
            print(f"Summary: {data.get('summary')}")
            print(f"Trend: {data.get('trend')}")
            print(f"Series Count: {len(data.get('series', []))}")
            if data["series"]:
                print(f"Sample Point: {data['series'][0]}")
        else:
            print(f"Status: FAILED ({response.status_code})")
            print(response.text)


if __name__ == "__main__":
    asyncio.run(verify_forecast())
