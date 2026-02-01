import threading
import time
from typing import Dict, Any, Optional
from app.database.connection import AsyncSessionLocal
from sqlalchemy import text
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

class HealthService:
    """
    Sistem bileşenlerinin sağlık durumunu denetler.
    (Database, AI Models, Cache, External APIs)
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
                "latency_ms": round((time.time() - start) * 1000, 2)
            }
        except Exception as e:
            logger.error(f"DB Health Check Failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_ai_readiness(self) -> Dict[str, Any]:
        """AI modellerinin yüklenme durumu"""
        from app.core.ai.rag_engine import get_rag_engine
        
        rag = get_rag_engine()
        rag_stats = rag.get_stats()
        
        return {
            "status": "healthy" if rag_stats.get("initialized") else "degraded",
            "rag_engine": rag_stats,
            "models": ["LightGBM", "LSTM", "RAG"]
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
            "components": {
                "database": db_status,
                "ai_engine": ai_status
            }
        }


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
