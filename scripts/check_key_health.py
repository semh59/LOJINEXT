import asyncio
import os
import httpx
from dotenv import load_dotenv


async def check_key_health():
    load_dotenv()
    api_key = os.getenv("OPENROUTE_API_KEY")
    print(f"API Key: [{api_key}]")

    async with httpx.AsyncClient() as client:
        # Test Geocode
        print("\nTesting Geocode...")
        geo_url = "https://api.openrouteservice.org/geocode/search"
        params = {"api_key": api_key, "text": "Ankara"}
        resp = await client.get(geo_url, params=params)
        print(f"Geocode Status: {resp.status_code}")
        print(f"Geocode Body: {resp.text}")


if __name__ == "__main__":
    asyncio.run(check_key_health())
