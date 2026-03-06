import asyncio
import os
import httpx
from dotenv import load_dotenv


async def debug_ors_full():
    load_dotenv()
    api_key = os.getenv("OPENROUTE_API_KEY")
    print(f"API Key present: {bool(api_key)}")

    url = "https://api.openrouteservice.org/v2/directions/driving-hgv/geojson"
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    body = {"coordinates": [[32.8597, 39.9334], [28.9784, 41.0082]], "elevation": True}

    print(f"Calling: {url}")
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=body, headers=headers)

        print(f"Status: {response.status_code}")
        print("Headers:")
        for k, v in response.headers.items():
            if "ratelimit" in k.lower():
                print(f"  {k}: {v}")

        print(f"Body: {response.text}")

        if response.status_code == 403:
            print("\nTrying driving-car as fallback...")
            url_car = (
                "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
            )
            body_car = {
                "coordinates": [[32.8597, 39.9334], [28.9784, 41.0082]],
                "elevation": True,
            }
            response_car = await client.post(url_car, json=body_car, headers=headers)
            print(f"Car Status: {response_car.status_code}")
            print(f"Car Body: {response_car.text}")


if __name__ == "__main__":
    asyncio.run(debug_ors_full())
