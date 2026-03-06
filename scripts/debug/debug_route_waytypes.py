import asyncio
import os
from dotenv import load_dotenv
from app.services.route_service import get_route_service

load_dotenv()


async def debug_waytypes():
    print("Testing RouteService with real ORS API (waytypes extra)...")
    service = get_route_service()

    # Istanbul to Ankara coordinates
    start = (28.9784, 41.0082)
    end = (32.8597, 39.9334)

    try:
        result = await service.get_route_details(start, end, use_cache=False)
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Success!")
            print(f"Total Distance: {result['distance_km']} km")
            print(f"Highway Distance: {result['otoban_mesafe_km']} km")
            print(f"Urban/Rural Distance: {result['sehir_ici_mesafe_km']} km")
            print(f"Flat Distance: {result['flat_distance_km']} km")
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_waytypes())
