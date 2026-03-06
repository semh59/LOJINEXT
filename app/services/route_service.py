"""
Route Service - Rota detayları ve yakıt tahmin entegrasyonu
Gelişmiş: Cache-aside pattern, async external API, config-driven
"""

import math
import os
from typing import Dict, Tuple

from app.config import settings
from app.core.services.route_validator import RouteValidator
from app.database.unit_of_work import UnitOfWork
from app.infrastructure.logging.logger import get_logger
from app.services.prediction_service import get_prediction_service

logger = get_logger(__name__)


class RouteService:
    """
    Rota detayları ve yakıt tahmin servisi.
    OpenRouteService API entegrasyonu ile çalışır.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENROUTE_API_KEY") or os.getenv(
            "OPENROUTESERVICE_API_KEY"
        )
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
            async with UnitOfWork() as uow:
                cached = await uow.route_repo.get_by_coords(lat1, lon1, lat2, lon2)
                if cached:
                    logger.info("Route cache hit.")

                    data = {
                        "distance_km": cached["distance_km"],
                        "duration_min": cached["duration_min"],
                        "ascent_m": cached["ascent_m"],
                        "descent_m": cached["descent_m"],
                        "otoban_mesafe_km": cached.get("otoban_mesafe_km", 0.0),
                        "sehir_ici_mesafe_km": cached.get("sehir_ici_mesafe_km", 0.0),
                        "flat_distance_km": cached.get("flat_distance_km", 0.0),
                        "geometry": cached["geometry"],
                        "fuel_estimate": cached.get("fuel_estimate_cache"),
                        "source": "cache",
                    }

                    # Sanity Check for Cached Data
                    data = RouteValidator.validate_and_correct(data)
                    return data

        # API key kontrolü
        if not self.api_key:
            logger.warning("OpenRouteService API key missing")
            return {"error": "API Key missing"}

        try:
            from app.services.external_service import get_external_service

            ext_service = get_external_service()
            client = await ext_service._get_client()

            url = f"{self.base_url}/directions/driving-hgv/geojson"
            headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json",
            }

            # Simplified ORS parameters to ensure stability
            body = {
                "coordinates": [[lon1, lat1], [lon2, lat2]],
                "elevation": True,
                "extra_info": ["waycategory", "waytype", "steepness"],
                "preference": "recommended",
            }

            response = await client.post(url, json=body, headers=headers, timeout=15)

            if response.status_code == 403:
                logger.warning(
                    "ORS: driving-hgv disallowed, falling back to driving-car"
                )
                url = f"{self.base_url}/directions/driving-car/geojson"
                # Remove hgv specific options for driving-car
                body.pop("options", None)
                response = await client.post(
                    url, json=body, headers=headers, timeout=15
                )

            if response.status_code != 200:
                logger.error(f"Routing API Error: {response.text}")
                # FALLBACK: Offline estimation
                logger.info("Using offline fallback for route estimation.")
                dist_km = self.haversine(lon1, lat1, lon2, lat2) / 1000
                dist_km *= 1.25  # Road curvature factor

                return {
                    "distance_km": round(dist_km, 1),
                    "duration_min": round(dist_km / 70 * 60, 0),
                    "ascent_m": round(dist_km * 4.5, 0),  # Estimated 4.5m per km
                    "descent_m": round(dist_km * 4.0, 0),
                    "otoban_mesafe_km": 0.0,
                    "sehir_ici_mesafe_km": round(dist_km, 1),
                    "flat_distance_km": 0.0,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[lon1, lat1, 0], [lon2, lat2, 0]],
                    },
                    "source": "offline_fallback",
                    "route_analysis": None,
                }

            data = response.json()
            feature = data["features"][0]
            props = feature["properties"]
            geometry = feature["geometry"]
            summary = props["summary"]

            # ORS Elevation Smoothing Factor (Phase 9 Calibration)
            # Digital Elevation Models (DEM) often overcount micro-changes.
            # 0.6 smoothing factor reduces noise in cumulative elevation data.
            SMOOTHING_FACTOR = 0.6
            ascent = props.get("ascent", 0.0) * SMOOTHING_FACTOR
            descent = props.get("descent", 0.0) * SMOOTHING_FACTOR

            # Use Domain Service for Analysis
            from app.domain.services.route_analyzer import route_analyzer

            # Analyzer expects [[lon, lat, elev], ...]
            # GeoJSON geometry["coordinates"] already has this format

            analysis_result = route_analyzer.analyze_segments(
                geometry["coordinates"],
                props.get("extras", {}),
                reference_distance_m=summary.get("distance", 0),
            )

            # Extract totals from analysis
            otoban_stats = analysis_result.get(
                "highway", {"flat": 0, "up": 0, "down": 0}
            )
            other_stats = analysis_result.get("other", {"flat": 0, "up": 0, "down": 0})

            # Sum up flat/up/down to get total km
            otoban_km = sum(otoban_stats.values())
            sehir_ici_mesafe_km = sum(other_stats.values())

            # Flat distance is sum of all flat segments
            # Or use profile analysis fallback? Analyzer is more accurate if steepness data exists
            flat_km = otoban_stats["flat"] + other_stats["flat"]

            result = {
                "distance_km": round(summary.get("distance", 0) / 1000, 2),
                "duration_min": round(summary.get("duration", 0) / 60, 0),
                "ascent_m": round(ascent, 1),
                "descent_m": round(descent, 1),
                "otoban_mesafe_km": round(otoban_km, 2),
                "sehir_ici_mesafe_km": round(sehir_ici_mesafe_km, 2),
                "flat_distance_km": round(flat_km, 2),
                "geometry": geometry,
                "source": "api",
                "route_analysis": analysis_result,
            }

            # Sanity Check for New API Data
            result = RouteValidator.validate_and_correct(result)

            # HYBRID ROUTING ENGINE (Phase 5)
            # If ORS data was "corrected" due to high anomaly, try Mapbox for ground truth.
            if result.get("is_corrected") and settings.MAPBOX_API_KEY:
                logger.warning(
                    f"ORS Anomaly Detected ({result.get('correction_reason')}). Attempting Mapbox fallback..."
                )

                from app.infrastructure.routing.mapbox_client import MapboxClient

                mapbox_client = MapboxClient()
                mb_result = await mapbox_client.get_route((lon1, lat1), (lon2, lat2))

                if mb_result:
                    # Mapbox successfully returned a route.
                    # Since Mapbox doesn't provide elevation by default, it returns 0 for ascent.
                    # This is safer than 2146m ascent for a flat road.
                    logger.info("Switched to Mapbox Provider for this route.")

                    # Merge Mapbox data (dist/duration) with our result structure
                    result["distance_km"] = mb_result["distance_km"]
                    result["duration_min"] = mb_result["duration_min"]
                    result["ascent_m"] = mb_result["ascent_m"]  # 0.0 or reliable
                    result["descent_m"] = mb_result["descent_m"]
                    result["geometry"] = mb_result["geometry"]
                    result["source"] = "mapbox_hybrid"

                    # Re-run validator just in case (though likely clean)
                    result = RouteValidator.validate_and_correct(result)

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
                flat_distance_km=result["flat_distance_km"],
                descent_m=result["descent_m"],
                route_analysis=result,
            )

            result["fuel_estimate"] = fuel_estimate

            # Cache'e kaydet
            async with UnitOfWork() as uow:
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
                        "otoban_mesafe_km": result["otoban_mesafe_km"],
                        "sehir_ici_mesafe_km": result["sehir_ici_mesafe_km"],
                        "flat_distance_km": result["flat_distance_km"],
                        "geometry": geometry,
                        "fuel_estimate_cache": result["fuel_estimate"],
                    }
                )

            logger.info(f"Route calculated via {result['source']}.")
            return result

        except Exception:
            logger.exception("Routing Service Error")
            raise

    async def get_base_location(self) -> str:
        """Sistemin ana merkez lokasyonunu getirir"""
        async with UnitOfWork() as uow:
            return await uow.config_repo.get_value("default_base_location", "FABRİKA")

    def haversine(self, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """İki nokta arası mesafe (metre)"""
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlamb = math.radians(lon2 - lon1)
        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlamb / 2) ** 2
        )
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _get_segment_distance(
        self, coordinates: list, start_idx: int, end_idx: int
    ) -> float:
        """Belirli bir segmentin (indis aralığı) toplam mesafesini hesaplar (metre)"""
        total = 0.0
        for i in range(start_idx, end_idx):
            if i + 1 >= len(coordinates):
                break
            p1 = coordinates[i]
            p2 = coordinates[i + 1]
            total += self.haversine(p1[0], p1[1], p2[0], p2[1])
        return total

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

        flat_dist = 0.0
        ramp_dist = 0.0

        for i in range(1, len(coords)):
            p1 = coords[i - 1]
            p2 = coords[i]

            d_horiz = self.haversine(p1[0], p1[1], p2[0], p2[1])
            if d_horiz < 5:  # 1m yerine 5m - Çok küçük değişimleri ve gürültüyü atla
                continue

            # Elevation verisi var mı kontrol et (GeoJSON coords: [lon, lat, elev])
            if len(p1) < 3 or len(p2) < 3:
                # Yükseklik verisi yoksa düz yol kabul et
                flat_dist += d_horiz
                continue

            d_vert = p2[2] - p1[2]
            gradient = (d_vert / d_horiz) * 100

            # Kamyonlar için %1.5 altı "düz" kabul edilebilir (Gürültü toleransı)
            if abs(gradient) < 1.5:
                flat_dist += d_horiz
            else:
                ramp_dist += d_horiz

        total = flat_dist + ramp_dist
        if total == 0:
            return {"flat_pct": 100, "ramp_pct": 0}

        return {
            "flat_pct": round((flat_dist / total) * 100, 1),
            "ramp_pct": round((ramp_dist / total) * 100, 1),
            "flat_dist_m": round(flat_dist, 0),
            "total_dist_m": round(total, 0),
        }

    def _get_route_difficulty(
        self, ascent: float, descent: float, distance_km: float
    ) -> str:
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
