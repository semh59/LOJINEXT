import logging
import sys
import os

sys.path.append(os.getcwd())

from dotenv import load_dotenv

load_dotenv()

from app.infrastructure.routing.openroute_client import get_route_client

# Configure logging to see details
logging.basicConfig(level=logging.DEBUG)


def test_integration():
    client = get_route_client()

    # Gebze -> Ankara
    origin = (40.7669, 29.4319)
    destination = (39.9334, 32.8597)

    print("Fetching route with details...")
    result = client.get_distance(
        origin, destination, include_details=True, use_cache=False
    )

    if result:
        print("\n--- Result ---")
        print(f"Distance: {result['distance_km']} km")
        print(f"Ascent: {result['ascent_m']} m")

        if "details" in result:
            print("\n--- Details ---")
            import json

            print(json.dumps(result["details"], indent=2))
        else:
            print("FAILED: 'details' key missing in result.")
    else:
        print("FAILED: No result returned.")


if __name__ == "__main__":
    test_integration()
