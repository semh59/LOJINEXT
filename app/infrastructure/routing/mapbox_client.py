"""
Mapbox Routing Client (Primary Provider)
Provides accurate routing data with road type classification via maxspeed annotations.
"""

from typing import Dict, List, Optional, Tuple

import httpx

from app.config import settings
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class MapboxClient:
    """
    Mapbox Directions API Client.
    Profile: driving-traffic (Real-time traffic)
    Uses maxspeed annotations for road type classification.
    """

    def __init__(self) -> None:
        self.api_key = settings.MAPBOX_API_KEY
        self.base_url = "https://api.mapbox.com/directions/v5/mapbox/driving-traffic"

    async def get_route(
        self,
        start_coords: Tuple[float, float],
        end_coords: Tuple[float, float],
    ) -> Optional[Dict]:
        """
        Fetch route from Mapbox with road type classification.

        Args:
            start_coords: (lon, lat)
            end_coords: (lon, lat)

        Returns:
            Dict with standardized route structure including road analysis, or None if failed.
        """
        if not self.api_key:
            logger.warning("Mapbox API Key missing. Skipping fallback.")
            return None

        lon1, lat1 = start_coords
        lon2, lat2 = end_coords

        # Format: {lon},{lat};{lon},{lat}
        coordinates_str = f"{lon1},{lat1};{lon2},{lat2}"
        url = f"{self.base_url}/{coordinates_str}"

        params = {
            "access_token": self.api_key,
            "geometries": "geojson",
            "overview": "full",
            "annotations": "distance,duration,maxspeed,road_class",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=15.0)

                if response.status_code != 200:
                    logger.error(f"Mapbox API Error: {response.text}")
                    return None

                data = response.json()
                if not data.get("routes"):
                    logger.warning("Mapbox returned no routes.")
                    return None

                route = data["routes"][0]
                geometry = route["geometry"]

                # Standardize Result
                dist_km = round(route["distance"] / 1000.0, 2)
                duration_min = round(route["duration"] / 60.0, 0)

                # Road Classification from maxspeed annotations
                road_analysis = self._classify_road_segments(route)
                otoban_km = road_analysis.get("otoban_km", 0.0)
                sehir_ici_km = road_analysis.get("sehir_ici_km", 0.0)
                trunk_km = road_analysis.get("trunk_km", 0.0)

                result = {
                    "distance_km": dist_km,
                    "duration_min": duration_min,
                    "ascent_m": 0.0,  # Mapbox Directions API doesn't provide elevation
                    "descent_m": 0.0,
                    "otoban_mesafe_km": round(otoban_km, 2),
                    "sehir_ici_mesafe_km": round(sehir_ici_km, 2),
                    "flat_distance_km": round(dist_km, 2),
                    "geometry": geometry,
                    "source": "mapbox",
                    "route_analysis": road_analysis.get("detailed", None),
                }

                logger.info(
                    f"Mapbox Route: {dist_km}km "
                    f"(otoban: {otoban_km:.1f}km, şehir içi: {sehir_ici_km:.1f}km, "
                    f"trunk: {trunk_km:.1f}km)"
                )
                return result

        except Exception as e:
            logger.exception(f"Mapbox Async Error: {e}")
            return None

    def _classify_road_segments(self, route: Dict) -> Dict:
        """
        Classify road segments using maxspeed annotations from Mapbox.

        Speed thresholds (Turkey):
            >= 110 km/h → Motorway/Otoyol
            >= 80 km/h  → Trunk/Primary (high-speed rural)
            >= 50 km/h  → Secondary/Urban arterial
            < 50 km/h   → City/Residential

        Returns:
            Dict with otoban_km, trunk_km, sehir_ici_km, and detailed analysis.
        """
        legs = route.get("legs", [])
        if not legs:
            dist_km = route.get("distance", 0) / 1000.0
            return {
                "otoban_km": 0.0,
                "trunk_km": 0.0,
                "sehir_ici_km": dist_km,
                "detailed": None,
            }

        motorway_m = 0.0
        trunk_m = 0.0
        primary_m = 0.0
        secondary_m = 0.0
        city_m = 0.0

        for leg in legs:
            annotation = leg.get("annotation", {})
            distances: List[float] = annotation.get("distance", [])
            maxspeeds: List[Dict] = annotation.get("maxspeed", [])
            road_classes: List[str] = annotation.get("road_class", [])

            if not distances or not road_classes:
                # No granular data — fallback to average speed
                leg_dist = leg.get("distance", 0)
                leg_dur = leg.get("duration", 1)
                avg_speed_kmh = (leg_dist / leg_dur) * 3.6 if leg_dur > 0 else 0

                if avg_speed_kmh >= 100:
                    motorway_m += leg_dist
                elif avg_speed_kmh >= 70:
                    trunk_m += leg_dist
                elif avg_speed_kmh >= 45:
                    primary_m += leg_dist
                else:
                    city_m += leg_dist
                continue

            for i, seg_dist in enumerate(distances):
                r_class = road_classes[i] if i < len(road_classes) else "street"
                
                # Primary Classification via Road Class
                if r_class == "motorway":
                    motorway_m += seg_dist
                elif r_class in ("trunk", "primary"):
                    # Turkey Distinction: Trunk roads are usually high-speed D-roads
                    trunk_m += seg_dist
                elif r_class in ("secondary", "tertiary"):
                    primary_m += seg_dist
                elif r_class in ("street", "residential", "service"):
                    city_m += seg_dist
                else:
                    # Fallback to speed if class is vague
                    speed_info = maxspeeds[i] if i < len(maxspeeds) else None
                    speed_kmh = self._extract_speed_kmh(speed_info)
                    
                    if speed_kmh and speed_kmh >= 110:
                        motorway_m += seg_dist
                    elif speed_kmh and speed_kmh >= 80:
                        trunk_m += seg_dist
                    elif speed_kmh and speed_kmh >= 50:
                        primary_m += seg_dist
                    else:
                        city_m += seg_dist

        # Convert to km
        motorway_km = motorway_m / 1000.0
        trunk_km = trunk_m / 1000.0
        primary_km = primary_m / 1000.0
        secondary_km = secondary_m / 1000.0
        city_km = city_m / 1000.0

        total_km = motorway_km + trunk_km + primary_km + secondary_km + city_km

        # User requested 3 categories: Otoyol, Devlet Yolu, Şehir İçi
        otoyol_ratio = motorway_km / total_km if total_km > 0 else 0
        devlet_ratio = (trunk_km + primary_km) / total_km if total_km > 0 else 0
        sehir_ratio = (secondary_km + city_km) / total_km if total_km > 0 else 1.0

        detailed = {
            "motorway": {"flat": round(motorway_km, 3), "up": 0, "down": 0},
            "trunk": {"flat": round(trunk_km, 3), "up": 0, "down": 0},
            "primary": {"flat": round(primary_km, 3), "up": 0, "down": 0},
            "secondary": {"flat": round(secondary_km, 3), "up": 0, "down": 0},
            "residential": {"flat": round(city_km, 3), "up": 0, "down": 0},
        }

        return {
            "otoban_km": round(
                (motorway_km + trunk_km + primary_km), 2
            ),  # Keep for legacy
            "sehir_ici_km": round(city_km + secondary_km, 2),  # Keep for legacy
            "ratios": {
                "otoyol": round(otoyol_ratio, 2),
                "devlet_yolu": round(devlet_ratio, 2),
                "sehir_ici": round(sehir_ratio, 2),
            },
            "detailed": detailed,
        }

    @staticmethod
    def _extract_speed_kmh(speed_info: Dict) -> Optional[float]:
        """
        Extract speed in km/h from Mapbox maxspeed annotation.

        Formats:
            {"speed": 120, "unit": "km/h"}
            {"speed": 55, "unit": "mph"}
            {"unknown": true}
            {"none": true}
        """
        if not isinstance(speed_info, dict):
            return None

        if speed_info.get("unknown") or speed_info.get("none"):
            return None

        speed = speed_info.get("speed")
        if speed is None:
            return None

        unit = speed_info.get("unit", "km/h")
        if unit == "mph":
            return speed * 1.60934
        return float(speed)
