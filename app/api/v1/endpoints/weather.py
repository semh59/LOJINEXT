from typing import List, Optional, Annotated

from app.api.deps import WeatherServiceDep, SessionDep, get_current_user
from app.database.models import Kullanici
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

router = APIRouter()


class WeatherRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Enlem")
    lon: float = Field(..., ge=-180, le=180, description="Boylam")


class WeatherForecast(BaseModel):
    date: str
    temperature_max: float
    precipitation_sum: float
    wind_speed_max: float
    impact_factor: float


class WeatherResponse(BaseModel):
    success: bool
    location: dict
    daily: List[WeatherForecast]
    fuel_impact_factor: float = Field(
        1.0,
        description="Hava koşullarının yakıt tüketimine etkisi (1.0 = normal, >1 = artış, <1 = azalış)"
    )
    recommendation: str


class TripWeatherRequest(BaseModel):
    cikis_lat: float = Field(..., ge=-90, le=90)
    cikis_lon: float = Field(..., ge=-180, le=180)
    varis_lat: float = Field(..., ge=-90, le=90)
    varis_lon: float = Field(..., ge=-180, le=180)
    trip_date: Optional[str] = Field(None, description="Sefer tarihi (YYYY-MM-DD)")


# === ENDPOINTS ===

@router.post("/forecast", response_model=WeatherResponse)
async def get_weather_forecast(
    request: WeatherRequest,
    service: WeatherServiceDep,
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Belirtilen koordinatlar için hava durumu tahmini al.
    Yakıt tüketimi etkisini hesapla.
    """
    result = await service.get_forecast_analysis(request.lat, request.lon)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Hava durumu hatası"))

    return WeatherResponse(
        success=True,
        location={"lat": request.lat, "lon": request.lon},
        daily=result["daily"],
        fuel_impact_factor=result["fuel_impact_factor"],
        recommendation=result["recommendation"]
    )


@router.post("/trip-impact")
async def get_trip_weather_impact(
    request: TripWeatherRequest,
    service: WeatherServiceDep,
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Bir seferin hava koşullarından etkilenme oranını hesapla.
    Çıkış ve varış noktalarının ortalamasını alır.
    """
    result = await service.get_trip_impact_analysis(
        request.cikis_lat, request.cikis_lon,
        request.varis_lat, request.varis_lon
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Hava durumu hatası"))

    return result
