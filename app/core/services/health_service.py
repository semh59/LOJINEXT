import threading
import time
from typing import Any, Dict, Optional, List
import sentry_sdk
from sqlalchemy import text

from app.database.connection import AsyncSessionLocal
from app.infrastructure.logging.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


class HealthService:
    """
    Sistem bileşenlerinin sağlık durumunu denetler.
    (Database, AI Models, Cache, External APIs, Sentry Errors)
    """

    def __init__(self):
        self.start_time = time.time()

    async def check_db(self) -> Dict[str, Any]:
        """Veritabanı bağlantı testi"""
        start = time.time()
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "latency_ms": round((time.time() - start) * 1000, 2),
            }
        except Exception as e:
            logger.error(f"DB Health Check Failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def check_ai_readiness(self) -> Dict[str, Any]:
        """AI modellerinin yüklenme durumu"""
        try:
            from app.core.ai.rag_engine import get_rag_engine

            rag = get_rag_engine()
            rag_stats = rag.get_stats()

            return {
                "status": "healthy" if rag_stats.get("initialized") else "degraded",
                "rag_engine": rag_stats,
                "models": ["LightGBM", "LSTM", "RAG"],
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_sentry_summary(self) -> Dict[str, Any]:
        """Sentry entegrasyon durumu ve temel hata metrikleri (Mocked)"""
        # In a real environment, we'd use Sentry's web API.
        # For now, we report if client is active.
        is_active = sentry_sdk.Hub.current.client is not None
        return {
            "enabled": bool(settings.SENTRY_DSN),
            "client_active": is_active,
            "environment": settings.ENVIRONMENT,
            "recent_errors_24h": 0,  # Placeholder for real metrics
        }

    async def get_circuit_breakers(self) -> List[Dict[str, Any]]:
        """Sistemdeki harici servis devre kesicilerinin durumu (Mocked)"""
        # Usually checking Redis keys or global state
        return [
            {"service": "WeatherAPI", "status": "CLOSED", "failure_count": 0},
            {"service": "MapService", "status": "CLOSED", "failure_count": 0},
        ]

    async def get_backup_status(self) -> Dict[str, Any]:
        """Son yedekleme durumu ve zamanı"""
        return {
            "last_backup": "2026-02-28 03:00:00 UTC",  # Mocked
            "status": "success",
            "storage": "Local + S3",
        }

    async def get_full_status(self) -> Dict[str, Any]:
        """Tüm sistemin sağlık özeti"""
        db_status = await self.check_db()
        ai_status = await self.check_ai_readiness()

        overall = "healthy"
        if db_status["status"] != "healthy" or ai_status["status"] != "healthy":
            overall = "degraded"

        return {
            "status": overall,
            "uptime_seconds": int(time.time() - self.start_time),
            "components": {"database": db_status, "ai_engine": ai_status},
        }

    async def get_admin_health_details(self) -> Dict[str, Any]:
        """Admin paneli için detaylı teknik sağlık raporu"""
        status = await self.get_full_status()
        status["sentry"] = await self.get_sentry_summary()
        status["circuit_breakers"] = await self.get_circuit_breakers()
        status["backups"] = await self.get_backup_status()
        return status


# Thread-safe Singleton
_health_service: Optional["HealthService"] = None
_health_service_lock = threading.Lock()


def get_health_service() -> HealthService:
    """Thread-safe singleton getter"""
    global _health_service
    if _health_service is None:
        with _health_service_lock:
            if _health_service is None:
                _health_service = HealthService()
    return _health_service
