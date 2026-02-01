"""
TIR Yakıt Takip - Dashboard Servisi
UI ve Veri katmanı arasındaki köprü.
"""

from typing import Any, Dict

import asyncio
from app.core.services.report_service import get_report_service
from app.database.repositories.sefer_repo import get_sefer_repo
from app.database.repositories.analiz_repo import get_analiz_repo
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

from app.infrastructure.cache.redis_cache import cached

class DashboardService:
    """
    Dashboard sayfası için veri toplama ve işleme servisi.
    UI'ın doğrudan repo veya diğer servislerle konuşmasını engeller.
    """

    def __init__(self):
        self.sefer_repo = get_sefer_repo()
        self.report_service = get_report_service()

    @cached(ttl=300, prefix="dashboard")
    async def get_dashboard_data(
        self, 
        offset: int = 0, 
        limit: int = 10, 
        search: str = None
    ) -> Dict[str, Any]:
        """
        Dashboard verilerini getir (Sayfalama ve Sanallaştırma desteğiyle).
        """
        try:
            # Parallel Fetching (Faz 5: Async & Parallel Optimization)
            analiz_repo = get_analiz_repo()
            
            
            # Tasks tanımla
            stats_task = self.report_service.get_dashboard_summary()
            comparison_task = self.report_service.get_monthly_comparison()
            
            trips_task = self.sefer_repo.get_all(
                offset=offset, 
                limit=limit,
                search_query=search
            )
            
            count_task = self.sefer_repo.count(search_query=search)
            
            chart_task = analiz_repo.get_monthly_consumption_series(months=6)

            # Hepsini paralel çalıştır
            stats, comparison, recent_trips_data, total_count, chart_data = await asyncio.gather(
                stats_task,
                comparison_task,
                trips_task,
                count_task,
                chart_task
            )
            
            # Trendleri stats'a enjekte et
            if stats and comparison:
                stats['trends'] = {
                    'sefer': comparison.get('sefer_degisim', 0),
                    'km': comparison.get('km_degisim', 0),
                    'tuketim': comparison.get('tuketim_degisim', 0)
                }

            return {
                "stats": stats,
                "recent_trips": recent_trips_data,
                "total_trips": total_count,
                "chart_data": chart_data or []
            }

        except Exception as e:
            logger.error(f"Dashboard data fetch error: {e}", exc_info=True)
            return {
                "stats": {},
                "recent_trips": [],
                "chart_data": []
            }

# Thread-safe singleton
import threading

_dashboard_service = None
_dashboard_lock = threading.Lock()

def get_dashboard_service() -> DashboardService:
    global _dashboard_service
    if _dashboard_service is None:
        with _dashboard_lock:
            if _dashboard_service is None:
                _dashboard_service = DashboardService()
    return _dashboard_service
