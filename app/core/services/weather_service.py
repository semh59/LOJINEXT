"""
LojiNext AI - Weather Service
Hava durumu verilerini işleme ve yakıt etkisini hesaplama mantığını içerir.
"""

import threading
from typing import Any, Dict, List, Optional

from app.config import settings
from app.infrastructure.logging.logger import get_logger
from app.services.external_service import ExternalService

logger = get_logger(__name__)


class WeatherService:
    """Hava durumu tabanlı analiz ve tahmin servisi."""

    def __init__(self, external_service: Optional[ExternalService] = None):
        self.external_service = external_service or ExternalService()

    async def get_forecast_analysis(self, lat: float, lon: float) -> Dict[str, Any]:
        """Koordinatlar için hava durumu tahmini ve yakıt etkisi analizi yapar."""
        result = await self.external_service.get_weather_forecast(lat, lon)

        if "error" in result:
            logger.warning(f"Weather forecast error, falling back to offline: {result['error']}")
            return self.get_forecast_analysis_offline()

        daily_data = result.get("daily", {})
        dates = daily_data.get("time", [])
        temps = daily_data.get("temperature_2m_max", [])
        precips = daily_data.get("precipitation_sum", [])
        winds = daily_data.get("wind_speed_10m_max", [])

        forecasts = []
        total_impact = 0

        for i, d in enumerate(dates[:7]):
            temp = temps[i] if i < len(temps) else 15
            precip = precips[i] if i < len(precips) else 0
            wind = winds[i] if i < len(winds) else 10

            impact = self.calculate_weather_fuel_impact(temp, precip, wind)
            total_impact += impact

            forecasts.append(
                {
                    "date": d,
                    "temperature_max": temp,
                    "precipitation_sum": precip,
                    "wind_speed_max": wind,
                    "impact_factor": round(impact, 3),
                }
            )

        avg_impact = total_impact / len(forecasts) if forecasts else 1.0
        recommendation = self.generate_weather_recommendation(avg_impact)

        return {
            "success": True,
            "daily": forecasts,
            "fuel_impact_factor": round(avg_impact, 3),
            "recommendation": recommendation,
            "offline": False,
        }

    def get_forecast_analysis_offline(self) -> Dict[str, Any]:
        """İnternet yoksa mevsime dayalı kaba tahminler üretir."""
        from datetime import datetime

        month = datetime.now().month

        # Mevsime göre ortalama Türkiye değerleri
        seasonal_defaults = {
            1: {"temp": 5, "precip": 5, "wind": 15},  # Ocak
            2: {"temp": 7, "precip": 4, "wind": 14},
            3: {"temp": 12, "precip": 3, "wind": 12},
            4: {"temp": 18, "precip": 2, "wind": 10},
            5: {"temp": 23, "precip": 1, "wind": 8},
            6: {"temp": 28, "precip": 0, "wind": 7},
            7: {"temp": 32, "precip": 0, "wind": 7},
            8: {"temp": 32, "precip": 0, "wind": 6},
            9: {"temp": 26, "precip": 1, "wind": 8},
            10: {"temp": 18, "precip": 3, "wind": 10},
            11: {"temp": 12, "precip": 4, "wind": 12},
            12: {"temp": 6, "precip": 5, "wind": 14},
        }

        defaults = seasonal_defaults.get(month, {"temp": 15, "precip": 0, "wind": 10})
        impact = self.calculate_weather_fuel_impact(
            defaults["temp"], defaults["precip"], defaults["wind"]
        )

        return {
            "success": True,
            "daily": [],
            "fuel_impact_factor": round(impact, 3),
            "recommendation": self.generate_weather_recommendation(impact) + " (Mevsimsel Tahmin)",
            "offline": True,
        }

    async def get_trip_impact_analysis(
        self, cikis_lat: float, cikis_lon: float, varis_lat: float, varis_lon: float
    ) -> Dict[str, Any]:
        """Bir sefer hattı üzerindeki hava durumu etkisini analiz eder (Parallel)."""
        import asyncio
        start_task = self.external_service.get_weather_forecast(cikis_lat, cikis_lon)
        end_task = self.external_service.get_weather_forecast(varis_lat, varis_lon)

        start_weather, end_weather = await asyncio.gather(start_task, end_task)

        if "error" in start_weather or "error" in end_weather:
            logger.warning("Weather API failed, using seasonal offline data.")
            return self.get_forecast_analysis_offline()

        start_daily = start_weather.get("daily", {})
        end_daily = end_weather.get("daily", {})

        # Ortalama değerler (bugünün tahmini)
        avg_temp = (
            start_daily.get("temperature_2m_max", [20])[0]
            + end_daily.get("temperature_2m_max", [20])[0]
        ) / 2
        avg_precip = (
            start_daily.get("precipitation_sum", [0])[0]
            + end_daily.get("precipitation_sum", [0])[0]
        ) / 2
        avg_wind = (
            start_daily.get("wind_speed_10m_max", [10])[0]
            + end_daily.get("wind_speed_10m_max", [10])[0]
        ) / 2

        impact_factor = self.calculate_weather_fuel_impact(avg_temp, avg_precip, avg_wind)
        conditions = self._get_condition_warnings(avg_temp, avg_precip, avg_wind)

        return {
            "success": True,
            "weather_summary": {
                "avg_temperature": round(avg_temp, 1),
                "avg_precipitation": round(avg_precip, 1),
                "avg_wind_speed": round(avg_wind, 1),
            },
            "fuel_impact_factor": round(impact_factor, 3),
            "fuel_impact_percent": round((impact_factor - 1) * 100, 1),
            "conditions": conditions,
            "recommendation": self.generate_weather_recommendation(impact_factor),
        }

    def calculate_weather_fuel_impact(self, temp: float, precip: float, wind: float) -> float:
        """Hava koşullarının yakıt tüketimine etkisini hesaplar (Config-driven)."""
        impact = 1.0

        # Sıcaklık etkisi (settings'den eşikler)
        if temp < 0:
            impact += 0.08
        elif temp < 10:
            impact += 0.04
        elif temp > settings.WEATHER_TEMP_HIGH_THRESHOLD:
            impact += 0.05
        elif temp > 30:
            impact += 0.03

        # Yağış etkisi
        if precip > 20:
            impact += 0.08
        elif precip > 10:
            impact += 0.05
        elif precip > 2:
            impact += 0.02

        # Rüzgar etkisi (settings'den eşik)
        if wind > settings.WEATHER_WIND_HIGH_THRESHOLD:
            impact += 0.15
        elif wind > 40:
            impact += 0.10
        elif wind > 25:
            impact += 0.05
        elif wind > 15:
            impact += 0.02

        return impact

    def generate_weather_recommendation(self, impact_factor: float) -> str:
        """Etki faktörüne göre tavsiye metni oluşturur (Config-driven)."""
        if impact_factor < settings.WEATHER_IMPACT_MEDIUM:
            return "Hava koşulları normal. Standart plan uygulanabilir."
        elif impact_factor < settings.WEATHER_IMPACT_HIGH:
            return "Orta seviye hava etkisi. %5-10 esneklik payı önerilir."
        else:
            return "Olumsuz hava! %15+ tüketim artışı bekleniyor. Dikkat!"

    def _get_condition_warnings(self, temp: float, precip: float, wind: float) -> List[str]:
        """Spesifik uyarı mesajlarını döner."""
        warnings = []
        if temp < 5:
            warnings.append("Soğuk hava - motor ısınma süresi ve rölanti tüketimi artabilir.")
        if precip > 5:
            warnings.append("Yağışlı yol - sürtünme direnci artışı ve güvenlik riski.")
        if wind > 30:
            warnings.append("Şiddetli rüzgar - aerodinamik dirençte belirgin artış.")
        return warnings


# Thread-safe Singleton provider
_weather_service: Optional[WeatherService] = None
_weather_service_lock = threading.Lock()


def get_weather_service() -> WeatherService:
    """Thread-safe singleton getter"""
    global _weather_service
    if _weather_service is None:
        with _weather_service_lock:
            if _weather_service is None:
                _weather_service = WeatherService()
    return _weather_service
