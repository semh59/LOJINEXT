import asyncio
import os
from dotenv import load_dotenv
from app.services.route_service import RouteService


async def debug_ors():
    load_dotenv()
    print(f"API Key present: {bool(os.getenv('OPENROUTE_API_KEY'))}")

    service = RouteService()
    # Ankara to Istanbul
    start = (32.8597, 39.9334)
    end = (28.9784, 41.0082)

    print("Fetching route details...")
    result = await service.get_route_details(start, end, use_cache=False)

    if "error" in result:
        print(f"FAILED: {result['error']}")
    else:
        print("SUCCESS!")
        print(f"Distance: {result['distance_km']} km")
        print(f"Ascent: {result['ascent_m']} m")
        print(f"Difficulty: {result['difficulty']}")


if __name__ == "__main__":
    asyncio.run(debug_ors())
