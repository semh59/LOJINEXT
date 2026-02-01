"""
TIR Yakıt Takip - Rapor Servisi
Trend raporları ve özet istatistikler
Async Refactoring: Veritabanı işlemleri non-blocking thread'lerde çalıştırılır.
PostgreSQL Migration: SQLite kaldırıldı, SQLAlchemy + PostgreSQL kullanılıyor.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TrendReport:
    """Trend rapor modeli"""
    period: str
    start_date: date
    end_date: date
    toplam_sefer: int
    toplam_km: int
    toplam_yakit: float
    ortalama_tuketim: float
    onceki_tuketim: Optional[float] = None
    tuketim_degisim: Optional[float] = None


class ReportService:
    """
    Rapor oluşturma servisi (Async).
    
    Ağır veritabanı işlemleri `asyncio.to_thread` ile thread pool'da çalıştırılır,
    böylece main event loop (UI) bloklanmaz.
    """

    def __init__(self, sefer_repo=None, yakit_repo=None, arac_repo=None, sofor_repo=None):
        if arac_repo:
            self.arac_repo = arac_repo
        else:
            from app.database.repositories.arac_repo import get_arac_repo
            self.arac_repo = get_arac_repo()

        if sofor_repo:
            self.sofor_repo = sofor_repo
        else:
            from app.database.repositories.sofor_repo import get_sofor_repo
            self.sofor_repo = get_sofor_repo()

        if sefer_repo:
            self.sefer_repo = sefer_repo
        else:
            from app.database.repositories.sefer_repo import get_sefer_repo
            self.sefer_repo = get_sefer_repo()

        if yakit_repo:
            self.yakit_repo = yakit_repo
        else:
            from app.database.repositories.yakit_repo import get_yakit_repo
            self.yakit_repo = get_yakit_repo()

    @property
    def analiz_repo(self):
        from app.database.repositories.analiz_repo import get_analiz_repo
        return get_analiz_repo()

    # =========================================================================
    # AYLIK TREND (ASYNC)
    # =========================================================================

    async def generate_monthly_trend(self, year: int = None, month: int = None) -> Dict:
        """Aylık trend raporu (Async & Parallel)"""
        import asyncio
        today = date.today()
        year = year or today.year
        month = month or today.month

        # Bu ay
        bu_ay_bas = date(year, month, 1)
        if month == 12:
            bu_ay_son = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            bu_ay_son = date(year, month + 1, 1) - timedelta(days=1)

        # Geçen ay
        gecen_ay_son = bu_ay_bas - timedelta(days=1)
        gecen_ay_bas = gecen_ay_son.replace(day=1)

        # Paralel çekim
        bu_ay_task = self.analiz_repo.get_period_stats(bu_ay_bas, bu_ay_son)
        gecen_ay_task = self.analiz_repo.get_period_stats(gecen_ay_bas, gecen_ay_son)
        
        bu_ay_data, gecen_ay_data = await asyncio.gather(bu_ay_task, gecen_ay_task)

        # Değişim hesapla
        degisimler = {}
        for key in ['toplam_sefer', 'toplam_km', 'toplam_yakit', 'ortalama_tuketim']:
            bu = bu_ay_data.get(key, 0) or 0
            gecen = gecen_ay_data.get(key, 0) or 0

            if gecen > 0:
                degisimler[f'{key}_degisim'] = round((bu - gecen) / gecen * 100, 1)
            else:
                degisimler[f'{key}_degisim'] = 0

        return {
            'donem': f"{year}-{month:02d}",
            'bu_ay': bu_ay_data,
            'gecen_ay': gecen_ay_data,
            'degisimler': degisimler
        }

    # =========================================================================
    # ARAÇ RAPORU (ASYNC)
    # =========================================================================

    async def generate_vehicle_report(self, arac_id: int, month: int = None, year: int = None, days: int = 30) -> Dict:
        """Araç detaylı raporu (Async & Parallel)"""
        import asyncio
        arac = await self.arac_repo.get_by_id(arac_id)
        if not arac:
            return {'error': 'Araç bulunamadı'}

        if month and year:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        else:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

        # Paralel çekim
        stats_task = self.analiz_repo.get_vehicle_summary_stats(arac_id, start_date)
        gunluk_task = self.analiz_repo.get_daily_consumption_series(days)
        guzergahlar_task = self.analiz_repo.get_top_routes_by_vehicle(arac_id, start_date, limit=5)

        stats, gunluk, guzergahlar = await asyncio.gather(stats_task, gunluk_task, guzergahlar_task)

        return {
            'plaka': arac['plaka'],
            'marka': arac['marka'],
            'model': arac.get('model', ''),
            'hedef_tuketim': arac.get('hedef_tuketim', 32.0),
            'performance_score': 85.0,
            'arac': arac,
            'donem': f"{month}/{year}" if month else f"Son {days} gün",
            'istatistikler': stats,
            'gunluk_trend': gunluk,
            'top_guzergahlar': guzergahlar
        }

    # =========================================================================
    # ŞOFÖR RAPORU (ASYNC)
    # =========================================================================

    async def generate_driver_report(self, sofor_id: int, days: int = 30) -> Dict:
        """Şoför detaylı raporu (Async)"""
        sofor = await self.sofor_repo.get_by_id(sofor_id)

        if not sofor:
            return {'error': 'Şoför bulunamadı'}

        # Değerlendirme (Entities üzerinden)
        from app.core.container import get_container
        degerlendirme = await get_container().degerlendirme_service.evaluate_driver(sofor_id)

        return {
            'sofor': sofor,
            'donem': f"Son {days} gün",
            'degerlendirme': degerlendirme.model_dump() if degerlendirme else None
        }

    # =========================================================================
    # FİLO ÖZETİ (ASYNC)
    # =========================================================================

    async def generate_fleet_summary(self, start_date: date = None, end_date: date = None, days: int = 30) -> Dict:
        """Filo özet raporu (Async) - Tarih aralığı veya Gün tabanlı"""
        if not start_date:
            start_date = date.today() - timedelta(days=days)
        
        # 1. Genel istatistikler ve harcama (Repository üzerinden)
        stats = await self.analiz_repo.get_fleet_performance_stats(start_date)

        # 2. Araç performans listesi (Advanced reports için gerekli)
        araclar = await self.analiz_repo.get_top_performing_vehicles(limit=15)

        return {
            'donem': f"Son {days} gün" if not end_date else f"{start_date} - {end_date}",
            'genel': stats,
            'total_vehicles': stats.get('total_vehicles', 0),
            'total_trips': stats.get('total_trips', 0),
            'total_distance': stats.get('total_distance', 0),
            'total_fuel': stats.get('total_fuel', 0),
            'avg_consumption': stats.get('avg_consumption', 0),
            'total_cost': stats.get('total_cost', 0),
            'vehicle_performance': araclar
        }


    # =========================================================================
    # DASHBOARD & GENEL İSTATİSTİKLER (ASYNC)
    # =========================================================================

    async def get_dashboard_summary(self) -> Dict:
        """Dashboard özet istatistiklerini getir (Async)"""
        from app.database.repositories.analiz_repo import get_analiz_repo
        return await get_analiz_repo().get_dashboard_stats()

    async def get_monthly_comparison(self) -> Dict[str, Any]:
        """Dashboard kümülatif istatistikler ve değişim oranları (Async)"""
        from app.database.repositories.analiz_repo import get_analiz_repo
        return await get_analiz_repo().get_monthly_comparison_stats()

    async def get_daily_consumption_trend(self, days: int = 30) -> List[Dict]:
        """Son X günün günlük tüketim verileri (Async)"""
        from app.database.repositories.analiz_repo import get_analiz_repo
        return await get_analiz_repo().get_daily_consumption_series(days)

    async def get_heatmap_data(self, days: int = 30) -> List[List[Any]]:
        """Leaflet veya Heatmap için yoğunluk verisi (Repository Method)."""
        from app.database.repositories.analiz_repo import get_analiz_repo
        
        analiz_repo = get_analiz_repo()
        return await analiz_repo.get_heatmap_data(days=days)

    async def get_driver_comparison_chart(self, limit: int = 10) -> Dict:
        """ECharts Bar Chart için şoför karşılaştırma verisi (Repository Method)."""
        from app.database.repositories.analiz_repo import get_analiz_repo
        
        analiz_repo = get_analiz_repo()
        return await analiz_repo.get_driver_comparison(limit=limit)

def get_report_service() -> ReportService:
    from app.core.container import get_container
    return get_container().report_service

