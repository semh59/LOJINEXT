import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.core.services.weather_service import WeatherService


async def check_weather():
    service = WeatherService()

    # Tekirdag -> Istanbul coords
    cikis = (40.994169, 27.492975)
    varis = (40.915053, 29.165409)

    print("Fetching weather impact for Tekirdag -> Istanbul...")
    try:
        res = await service.get_trip_impact_analysis(
            cikis_lat=cikis[0],
            cikis_lon=cikis[1],
            varis_lat=varis[0],
            varis_lon=varis[1],
        )
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_weather())
