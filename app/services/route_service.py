"""
Route Service - Rota detayları ve yakıt tahmin entegrasyonu
ELITE: Cache-aside pattern, async external API, config-driven
"""

import asyncio
import math
import os
from typing import Dict, Tuple


from app.config import settings
from app.database.unit_of_work import get_uow
from app.infrastructure.logging.logger import get_logger
from app.services.prediction_service import get_prediction_service

logger = get_logger(__name__)


class RouteService:
    """
    Rota detayları ve yakıt tahmin servisi.
    OpenRouteService API entegrasyonu ile çalışır.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENROUTE_API_KEY") or os.getenv("OPENROUTESERVICE_API_KEY")
        self.base_url = "https://api.openrouteservice.org/v2"

    async def get_route_details(
        self,
        start_coords: Tuple[float, float],
        end_coords: Tuple[float, float],
        use_cache: bool = True,
    ) -> Dict:
        """
        Get route details (Async + Cache-Aside).

        Args:
            start_coords: (lon, lat) tuple
            end_coords: (lon, lat) tuple
            use_cache: Cache kullanılsın mı

        Returns:
            Dict: Rota bilgileri (distance, duration, elevation, geometry)
        """
        lon1, lat1 = start_coords
        lon2, lat2 = end_coords

        # Cache kontrolü
        if use_cache:
            async with get_uow() as uow:
                cached = await uow.route_repo.get_by_coords(lat1, lon1, lat2, lon2)
                if cached:
                    logger.info("Route cache hit.")
                    return {
                        "distance_km": cached["distance_km"],
                        "duration_min": cached["duration_min"],
                        "ascent_m": cached["ascent_m"],
                        "descent_m": cached["descent_m"],
                        "geometry": cached["geometry"],
                        "fuel_estimate": cached.get("fuel_estimate_cache"),
                        "source": "cache",
                    }

        # API key kontrolü
        if not self.api_key:
            logger.warning("OpenRouteService API key missing")
            return {"error": "API Key missing"}

        try:
            from app.services.external_service import get_external_service

            ext_service = get_external_service()
            client = await ext_service._get_client()

            url = f"{self.base_url}/directions/driving-hgv/geojson"
            headers = {"Authorization": self.api_key, "Content-Type": "application/json"}

            # Config-driven HGV parametreleri (hardcoded değil!)
            body = {
                "coordinates": [[lon1, lat1], [lon2, lat2]],
                "elevation": True,
                "profile": "driving-hgv",
                "preference": "recommended",
                "options": {
                    "vehicle_type": "heavy_truck",
                    "hgv_type": "articulated",
                    "axle_load": settings.HGV_AXLE_LOAD,
                    "gross_weight": settings.HGV_GROSS_WEIGHT,
                },
            }

            response = await client.post(url, json=body, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.error(f"ORS API Error: {response.text}")
                return {"error": f"API Error: {response.status_code}"}

            data = response.json()
            feature = data["features"][0]
            props = feature["properties"]
            geometry = feature["geometry"]
            summary = props["summary"]

            ascent = props.get("ascent", 0.0)
            descent = props.get("descent", 0.0)

            result = {
                "distance_km": round(summary.get("distance", 0) / 1000, 2),
                "duration_min": round(summary.get("duration", 0) / 60, 0),
                "ascent_m": round(ascent, 1),
                "descent_m": round(descent, 1),
                "geometry": geometry,
                "source": "api",
            }

            # FAZ 2.1: Ağır CPU-bound analizleri thread pool'a al
            result["profile"] = await asyncio.to_thread(self._analyze_elevation_profile, geometry)
            result["difficulty"] = self._get_route_difficulty(
                result["ascent_m"], result["descent_m"], result["distance_km"]
            )

            # Elite Fuel Prediction
            pred_service = get_prediction_service()
            fuel_estimate = await pred_service.predict_consumption(
                arac_id=0,
                mesafe_km=result["distance_km"],
                ton=settings.DEFAULT_LOAD_TON,
                ascent_m=result["ascent_m"],
                descent_m=result["descent_m"],
            )

            result["fuel_estimate"] = fuel_estimate

            # Cache'e kaydet
            async with get_uow() as uow:
                await uow.route_repo.save_route(
                    {
                        "origin_lat": lat1,
                        "origin_lon": lon1,
                        "dest_lat": lat2,
                        "dest_lon": lon2,
                        "distance_km": result["distance_km"],
                        "duration_min": result["duration_min"],
                        "ascent_m": result["ascent_m"],
                        "descent_m": result["descent_m"],
                        "geometry": geometry,
                        "fuel_estimate_cache": result["fuel_estimate"],
                    }
                )

            return result

        except Exception as e:
            logger.exception("ORS Async Error")
            return {"error": str(e)}

    async def get_base_location(self) -> str:
        """Sistemin ana merkez lokasyonunu getirir"""
        async with get_uow() as uow:
            return await uow.config_repo.get_value("default_base_location", "FABRİKA")

    def _analyze_elevation_profile(self, geometry: Dict) -> Dict:
        """
        GeoJSON koordinatlarından eğim profilini çıkarır.

        Args:
            geometry: GeoJSON geometry objesi

        Returns:
            Dict: flat_pct, ramp_pct, total_dist_m
        """
        coords = geometry.get("coordinates", [])
        if len(coords) < 2:
            return {"flat_pct": 100, "ramp_pct": 0}

        def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
            """İki nokta arası mesafe (metre)"""
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlamb = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlamb / 2) ** 2
            return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        flat_dist = 0.0
        ramp_dist = 0.0

        for i in range(1, len(coords)):
            p1 = coords[i - 1]
            p2 = coords[i]

            d_horiz = haversine(p1[0], p1[1], p2[0], p2[1])
            if d_horiz < 1:
                continue  # Çok küçük değişimleri atla

            d_vert = p2[2] - p1[2]
            gradient = (d_vert / d_horiz) * 100

            # Config-driven threshold: 1% gradient
            if abs(gradient) < 1.0:
                flat_dist += d_horiz
            else:
                ramp_dist += d_horiz

        total = flat_dist + ramp_dist
        if total == 0:
            return {"flat_pct": 100, "ramp_pct": 0}

        return {
            "flat_pct": round((flat_dist / total) * 100, 1),
            "ramp_pct": round((ramp_dist / total) * 100, 1),
            "total_dist_m": round(total, 0),
        }

    def _get_route_difficulty(self, ascent: float, descent: float, distance_km: float) -> str:
        """
        Rota zorluğunu hesapla.

        Args:
            ascent: Toplam tırmanış (m)
            descent: Toplam iniş (m)
            distance_km: Toplam mesafe (km)

        Returns:
            str: Zorluk seviyesi
        """
        if distance_km == 0:
            return "Bilinmiyor"

        gradient_factor = (ascent / (distance_km * 1000)) * 100

        # Thresholds (config'e taşınabilir)
        if gradient_factor < 0.5:
            return "Düz"
        elif gradient_factor < 1.5:
            return "Hafif Eğimli"
        else:
            return "Dik/Dağlık"


def get_route_service() -> RouteService:
    """Thread-safe singleton getter via DI container"""
    from app.core.container import get_container

    return get_container().route_service
