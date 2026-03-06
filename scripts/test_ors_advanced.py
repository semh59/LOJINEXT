import asyncio
import os
import httpx
import json
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()


async def get_ors_route_details():
    api_key = os.getenv("OPENROUTE_API_KEY")
    if not api_key:
        print("Error: OPENROUTE_API_KEY not found in environment variables.")
        return

    # Endpoint for JSON response (easier to read extras compared to GeoJSON sometimes, but let's try standard JSON endpoint)
    # The standard v2/directions/{profile}/json endpoint returns rich data
    profile = "driving-hgv"
    url = f"https://api.openrouteservice.org/v2/directions/{profile}/json"

    headers = {"Authorization": api_key, "Content-Type": "application/json"}

    # Istanbul to Ankara coordinates (approx)
    # Start: Gebze (40.79, 29.43)
    # End: Ankara (39.93, 32.85)
    # ORS expects [lon, lat]
    start_coord = [29.4319, 40.7669]
    end_coord = [32.8597, 39.9334]

    body = {
        "coordinates": [start_coord, end_coord],
        "elevation": "true",
        "extra_info": ["steepness", "waycategory", "waytype", "surface"],
        "units": "m",
        "instructions": "false",  # We focus on data, not turn-by-turn
        "geometry": "true",
    }

    print(f"Sending request to {url}...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=body, headers=headers, timeout=30.0)

            if response.status_code != 200:
                print(f"Error {response.status_code}: {response.text}")
                return

            data = response.json()

            # Save raw response for inspection
            with open("ors_advanced_response.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("Response saved to ors_advanced_response.json")

            process_ors_response(data)

        except Exception as e:
            print(f"Exception occurred: {e}")


def process_ors_response(data: Dict[str, Any]):
    try:
        route = data["routes"][0]
        summary = route["summary"]
        geometry = route[
            "geometry"
        ]  # decoding needed if it's encoded string, but /json usually returns encoded polyline

        # Check if extras exist
        extras = route.get("extras")
        if not extras:
            print("No 'extras' found in response!")
            return

        print("\n--- Route Summary ---")
        print(f"Total Distance: {summary.get('distance', 0) / 1000:.2f} km")
        print(f"Total Ascent: {summary.get('ascent', 0)} m")
        print(f"Total Descent: {summary.get('descent', 0)} m")

        print("\n--- Extras Found ---")
        for key in extras.keys():
            print(f"- {key}: {len(extras[key]['values'])} segments")

        # Basic analysis of segments
        # Extras format: { "road_class": { "values": [ [start_index, end_index, value_id], ... ], "summary": [...] } }

        # We need to map codes to meanings if they are IDs.
        # Usually ORS returns IDs for some (like surface) and strings for others?
        # Let's inspect the first few values.

        if "road_class" in extras:
            print("\nSample Road Classes:")
            print(extras["road_class"]["values"][:5])

        if "steepness" in extras:
            print("\nSample Steepness:")
            print(extras["steepness"]["values"][:5])

        # Logic to calculate intersection
        # We need projected distances.
        # The indices in 'values' correspond to the geometry coordinates list.
        # But 'geometry' in normal JSON response is an encoded polyline string usually.
        # Unless we asked for geojson or explicitly geometry_format.
        # By default ORS returns encoded polyline.
        # To verify this, let's look at the geometry field type.
        print(f"\nGeometry type: {type(geometry)}")

        # If we want to calculate real distances, we need to decode polyline or use segment distances.
        # ORS extras mapping is based on WayPoints indices.
        # "The `values` list contains arrays of [start_index, end_index, value]."
        # These indices refer to the coordinate array decoded from the geometry string.

    except KeyError as e:
        print(f"KeyError during processing: {e}")


if __name__ == "__main__":
    asyncio.run(get_ors_route_details())
