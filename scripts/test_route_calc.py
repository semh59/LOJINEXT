import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.route_service import RouteService


async def main():
    service = RouteService()

    # Test Coordinates: Ankara -> Istanbul (Approx)
    start = (32.8597, 39.9334)  # Lon, Lat
    end = (28.9784, 41.0082)  # Lon, Lat

    print(f"Testing Route: Ankara {start} -> Istanbul {end}")

    # Mocking API Key if needed or relying on offline fallback if key is missing/invalid
    # For this test, we want to see what the service returns structure-wise

    # Force use_cache=False to trigger calculation logic
    try:
        result = await service.get_route_details(start, end, use_cache=False)
        print("\n--- Route Calculation Result ---")
        for key, value in result.items():
            if key == "geometry":
                print(f"{key}: <Geometry Data>")
            else:
                print(f"{key}: {value}")

        print("\n--- Compatibility Check ---")
        difficulty = result.get("difficulty")
        print(f"Backend Difficulty: '{difficulty}'")

        frontend_options = ["Normal", "Orta", "Zor"]
        if difficulty not in frontend_options:
            print(
                f"❌ MISMATCH: Backend '{difficulty}' is NOT in Frontend options {frontend_options}"
            )
            print(
                "   -> Mapping required: 'Düz'->'Normal', 'Hafif Eğimli'->'Orta', 'Dik/Dağlık'->'Zor'"
            )
        else:
            print(f"✅ MATCH: Backend '{difficulty}' is compatible.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
