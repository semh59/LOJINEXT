from app.api.v1.endpoints import (
    advanced_reports,
    ai,
    alerts,
    anomalies,
    auth,
    drivers,
    fuel,
    locations,
    predictions,
    reports,
    routes,
    settings as settings_api,
    trips,
    users,
    vehicles,
    weather,
    health,
    guzergahlar,
)
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(guzergahlar.router, prefix="/guzergahlar", tags=["guzergahlar"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])
api_router.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
api_router.include_router(trips.router, prefix="/trips", tags=["trips"])
api_router.include_router(fuel.router, prefix="/fuel", tags=["fuel"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
api_router.include_router(advanced_reports.router, prefix="/advanced-reports", tags=["advanced-reports"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(settings_api.router, prefix="/settings", tags=["settings"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
