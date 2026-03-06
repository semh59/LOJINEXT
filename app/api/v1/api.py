from fastapi import APIRouter

from app.api.v1.endpoints import (
    advanced_reports,
    ai,
    anomalies,
    auth,
    drivers,
    fuel,
    health,
    locations,
    predictions,
    reports,
    routes,
    trips,
    vehicles,
    weather,
    ws_ticket,
    admin_config,
    admin_roles,
    admin_users,
    admin_ws,
    admin_imports,
    admin_ml,
    admin_attribution,
    admin_calibration,
    admin_maintenance,
    admin_notifications,
    admin_health,
    trailers,
    preferences,
)

api_router = APIRouter()
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    admin_config.router, prefix="/admin/config", tags=["admin-config"]
)
api_router.include_router(
    admin_roles.router, prefix="/admin/roles", tags=["admin-roles"]
)
api_router.include_router(
    admin_users.router, prefix="/admin/users", tags=["admin-users"]
)
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])
api_router.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
api_router.include_router(trips.router, prefix="/trips", tags=["trips"])
api_router.include_router(fuel.router, prefix="/fuel", tags=["fuel"])
api_router.include_router(
    predictions.router, prefix="/predictions", tags=["predictions"]
)
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
api_router.include_router(
    advanced_reports.router, prefix="/advanced-reports", tags=["advanced-reports"]
)
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(ws_ticket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(admin_ws.router, prefix="/admin/ws", tags=["admin-ws"])
api_router.include_router(
    admin_imports.router, prefix="/admin/imports", tags=["admin-imports"]
)
api_router.include_router(admin_ml.router, prefix="/admin/ml", tags=["admin-ml"])
api_router.include_router(
    admin_attribution.router, prefix="/admin/attribution", tags=["admin-attribution"]
)
api_router.include_router(
    admin_calibration.router, prefix="/admin/calibration", tags=["admin-calibration"]
)
api_router.include_router(
    admin_maintenance.router, prefix="/admin/maintenance", tags=["admin-maintenance"]
)
api_router.include_router(
    admin_notifications.router,
    prefix="/admin/notifications",
    tags=["admin-notifications"],
)
api_router.include_router(
    admin_health.router, prefix="/admin/health", tags=["admin-health"]
)
api_router.include_router(trailers.router, prefix="/trailers", tags=["trailers"])
api_router.include_router(
    preferences.router, prefix="/preferences", tags=["preferences"]
)
