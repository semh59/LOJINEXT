import asyncio
import httpx
import sys
import os

sys.path.append(os.getcwd())

from app.core.security import create_access_token


async def verify_anomalies():
    # Mock admin token
    token = create_access_token({"sub": "admin", "id": 1, "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(
        base_url="http://localhost:8000/api/v1", timeout=30.0
    ) as client:
        print("Testing /anomalies/recent...")
        response = await client.get("/anomalies/recent?days=30", headers=headers)

        if response.status_code == 200:
            data = response.json()
            print("Status: SUCCESS")
            print(f"Count: {len(data)}")
            if len(data) > 0:
                sample = data[0]
                print(f"Sample Type: {sample.get('tip')}")
                print(f"Sample Severity: {sample.get('severity')}")
                print(f"Root Cause: {sample.get('root_cause')}")
                print(f"Action: {sample.get('suggested_action')}")
            else:
                print("No anomalies found (might be expected if DB empty)")
        else:
            print(f"Status: FAILED ({response.status_code})")
            print(response.text)


if __name__ == "__main__":
    asyncio.run(verify_anomalies())
