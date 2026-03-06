from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import SessionDep, WeatherServiceDep, get_current_user
from app.database.models import Kullanici

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
        description="Hava koşullarının yakıt tüketimine etkisi (1.0 = normal, >1 = artış, <1 = azalış)",
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
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    """
    Belirtilen koordinatlar için hava durumu tahmini al.
    Yakıt tüketimi etkisini hesapla.
    """
    result = await service.get_forecast_analysis(request.lat, request.lon)

    if not result.get("success"):
        raise HTTPException(
            status_code=500, detail=result.get("error", "Hava durumu hatası")
        )

    return WeatherResponse(
        success=True,
        location={"lat": request.lat, "lon": request.lon},
        daily=result["daily"],
        fuel_impact_factor=result["fuel_impact_factor"],
        recommendation=result["recommendation"],
    )


@router.post("/trip-impact")
async def get_trip_weather_impact(
    request: TripWeatherRequest,
    service: WeatherServiceDep,
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    """
    Bir seferin hava koşullarından etkilenme oranını hesapla.
    Çıkış ve varış noktalarının ortalamasını alır.
    """
    result = await service.get_trip_impact_analysis(
        request.cikis_lat, request.cikis_lon, request.varis_lat, request.varis_lon
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500, detail=result.get("error", "Hava durumu hatası")
        )

    return result


@router.get("/dashboard-summary")
async def get_dashboard_weather_summary(
    service: WeatherServiceDep,
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    """
    Dashboard için aktif seferlerin hava durumu özetini getirir.
    Cache mekanizması sayesinde performanslıdır.
    """
    from app.core.services.sefer_service import get_sefer_service

    sefer_service = get_sefer_service()

    # 1. Aktif Seferleri Getir (Yolda veya Devam Ediyor)
    # 1. Aktif Seferleri Getir (Yolda veya Devam Ediyor)
    res_yolda = await sefer_service.get_all_paged(
        current_user=current_user, durum="Yolda", limit=50
    )
    res_devam = await sefer_service.get_all_paged(
        current_user=current_user, durum="Devam Ediyor", limit=50
    )
    all_active = res_yolda["items"] + res_devam["items"]

    # 2. Risk Analizi
    summary = {
        "total_active": len(all_active),
        "high_risk": 0,
        "medium_risk": 0,
        "normal": 0,
        "details": [],
    }

    # 3. Güzergah Detaylarını Toplu Getir (N+1 Prevention)
    guzergah_ids = {t.guzergah_id for t in all_active if t.guzergah_id}

    routes_map = {}
    if guzergah_ids:
        from app.database.repositories.lokasyon_repo import get_lokasyon_repo

        lokasyon_repo = get_lokasyon_repo(db)  # Use session from dep
        # Basitçe hepsini çekip Python'da filtreleyelim veya WHERE IN yapalım
        # LokasyonRepo'da get_by_ids yoksa, manuel query veya loop
        # Şimdilik loop (cache varsa hızlıdır) veya get_all
        all_routes = await lokasyon_repo.get_all(limit=1000)
        routes_map = {r["id"]: r for r in all_routes if r["id"] in guzergah_ids}

    # 4. Paralel Analiz Hazırlığı
    async def analyze_trip(trip):
        impact = 1.0
        details = {}
        if trip.guzergah_id and trip.guzergah_id in routes_map:
            route = routes_map[trip.guzergah_id]
            c_lat = route.get("cikis_lat")
            v_lat = route.get("varis_lat")

            if c_lat and v_lat:
                w_res = await service.get_trip_impact_analysis(
                    c_lat, route["cikis_lon"], v_lat, route["varis_lon"]
                )
                if w_res.get("success"):
                    impact = w_res.get("fuel_impact_factor", 1.0)
                    details = w_res
        return {"trip": trip, "impact": impact, "details": details}

    import asyncio

    tasks = [analyze_trip(t) for t in all_active]
    results = await asyncio.gather(*tasks)

    # 5. Sonuçları İşle
    for res in results:
        trip = res["trip"]
        impact = res["impact"]

        # Sınıflandırma
        if impact > 1.10:
            summary["high_risk"] += 1
            summary["details"].append(
                {
                    "trip_id": trip.id,
                    "plaka": getattr(trip, "plaka", "Bilinmiyor"),
                    "risk": "High",
                    "impact": impact,
                }
            )
        elif impact > 1.02:
            summary["medium_risk"] += 1
        else:
            summary["normal"] += 1

    return summary
