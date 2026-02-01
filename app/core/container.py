
"""
TIR Yakıt Takip Sistemi - Dependency Injection Container
Tüm bağımlılıkları yöneten merkezi konteyner.
"""

import threading
from typing import Optional


class Container:
    """
    Dependency Injection Container.
    Singleton pattern ile uygulama genelinde tek bir instance tutar.
    Lazy loading ile bellek kullanımını optimize eder.
    """

    def __init__(self):
        self._lock = threading.RLock() # Re-entrant lock to prevent deadlocks when properties call each other
        
        # Infrastructure
        self._event_bus = None
        
        # Repositories
        self._arac_repo = None
        self._sefer_repo = None
        self._sofor_repo = None
        self._yakit_repo = None
        self._lokasyon_repo = None
        self._analiz_repo = None
        
        # Services
        self._arac_service = None
        self._sofor_service = None
        self._sefer_service = None
        self._yakit_service = None
        self._lokasyon_service = None
        self._analiz_service = None
        self._import_service = None
        self._report_service = None
        self._prediction_service = None
        self._anomaly_detector = None
        self._time_series_service = None
        self._license_service = None
        self._health_service = None
        self._route_service = None
        self._smart_ai_service = None
        self._yakit_tahmin_service = None
        self._sofor_analiz_service = None
        self._degerlendirme_service = None
        self._external_service = None
        self._weather_service = None

    @property
    def event_bus(self):
        if self._event_bus is None:
            with self._lock:
                if self._event_bus is None:
                    from app.infrastructure.events.event_bus import get_event_bus
                    self._event_bus = get_event_bus()
        return self._event_bus

    # --- Repositories ---

    @property
    def arac_repo(self):
        if self._arac_repo is None:
            with self._lock:
                if self._arac_repo is None:
                    from app.database.repositories.arac_repo import AracRepository
                    self._arac_repo = AracRepository()
        return self._arac_repo

    @property
    def sefer_repo(self):
        if self._sefer_repo is None:
            with self._lock:
                if self._sefer_repo is None:
                    from app.database.repositories.sefer_repo import SeferRepository
                    self._sefer_repo = SeferRepository()
        return self._sefer_repo

    @property
    def sofor_repo(self):
        if self._sofor_repo is None:
            with self._lock:
                if self._sofor_repo is None:
                    from app.database.repositories.sofor_repo import SoforRepository
                    self._sofor_repo = SoforRepository()
        return self._sofor_repo

    @property
    def yakit_repo(self):
        if self._yakit_repo is None:
            with self._lock:
                if self._yakit_repo is None:
                    from app.database.repositories.yakit_repo import YakitRepository
                    self._yakit_repo = YakitRepository()
        return self._yakit_repo

    @property
    def lokasyon_repo(self):
        if self._lokasyon_repo is None:
            with self._lock:
                if self._lokasyon_repo is None:
                    from app.database.repositories.lokasyon_repo import LokasyonRepository
                    self._lokasyon_repo = LokasyonRepository()
        return self._lokasyon_repo

    # --- Core Services ---

    @property
    def arac_service(self):
        if self._arac_service is None:
            with self._lock:
                if self._arac_service is None:
                    from app.core.services.arac_service import AracService
                    self._arac_service = AracService(repo=self.arac_repo, event_bus=self.event_bus)
        return self._arac_service

    @property
    def sofor_service(self):
        if self._sofor_service is None:
            with self._lock:
                if self._sofor_service is None:
                    from app.core.services.sofor_service import SoforService
                    self._sofor_service = SoforService(repo=self.sofor_repo, event_bus=self.event_bus)
        return self._sofor_service

    @property
    def sefer_service(self):
        if self._sefer_service is None:
            with self._lock:
                if self._sefer_service is None:
                    from app.core.services.sefer_service import SeferService
                    self._sefer_service = SeferService(repo=self.sefer_repo, event_bus=self.event_bus)
        return self._sefer_service

    @property
    def yakit_service(self):
        if self._yakit_service is None:
            with self._lock:
                if self._yakit_service is None:
                    from app.core.services.yakit_service import YakitService
                    self._yakit_service = YakitService(repo=self.yakit_repo, event_bus=self.event_bus)
        return self._yakit_service

    @property
    def lokasyon_service(self):
        if self._lokasyon_service is None:
            with self._lock:
                if self._lokasyon_service is None:
                    from app.core.services.lokasyon_service import LokasyonService
                    self._lokasyon_service = LokasyonService(repo=self.lokasyon_repo, event_bus=self.event_bus)
        return self._lokasyon_service

    @property
    def analiz_repo(self):
        if self._analiz_repo is None:
            with self._lock:
                if self._analiz_repo is None:
                    from app.database.repositories.analiz_repo import AnalizRepository
                    self._analiz_repo = AnalizRepository()
        return self._analiz_repo

    @property
    def analiz_service(self):
        if self._analiz_service is None:
            with self._lock:
                if self._analiz_service is None:
                    from app.core.services.analiz_service import AnalizService
                    self._analiz_service = AnalizService(
                        arac_repo=self.arac_repo,
                        sefer_repo=self.sefer_repo,
                        yakit_repo=self.yakit_repo
                    )
        return self._analiz_service

    @property
    def import_service(self):
        if self._import_service is None:
            with self._lock:
                if self._import_service is None:
                    from app.core.services.import_service import ImportService
                    self._import_service = ImportService(
                        sefer_service=self.sefer_service,
                        yakit_service=self.yakit_service,
                        arac_repo=self.arac_repo,
                        sofor_repo=self.sofor_repo
                    )
        return self._import_service

    @property
    def report_service(self):
        if self._report_service is None:
            with self._lock:
                if self._report_service is None:
                    from app.core.services.report_service import ReportService
                    self._report_service = ReportService(
                        sefer_repo=self.sefer_repo,
                        yakit_repo=self.yakit_repo,
                        arac_repo=self.arac_repo,
                        sofor_repo=self.sofor_repo
                    )
        return self._report_service

    @property
    def prediction_service(self):
        if self._prediction_service is None:
            with self._lock:
                if self._prediction_service is None:
                    from app.services.prediction_service import PredictionService
                    self._prediction_service = PredictionService()
        return self._prediction_service

    @property
    def anomaly_detector(self):
        if self._anomaly_detector is None:
            with self._lock:
                if self._anomaly_detector is None:
                    from app.core.services.anomaly_detector import AnomalyDetector
                    self._anomaly_detector = AnomalyDetector()
        return self._anomaly_detector

    @property
    def time_series_service(self):
        if self._time_series_service is None:
            with self._lock:
                if self._time_series_service is None:
                    from app.services.time_series_service import TimeSeriesService
                    self._time_series_service = TimeSeriesService()
        return self._time_series_service

    @property
    def license_service(self):
        if self._license_service is None:
            with self._lock:
                if self._license_service is None:
                    from app.core.services.license_service import LicenseEngine
                    self._license_service = LicenseEngine()
        return self._license_service

    @property
    def health_service(self):
        if self._health_service is None:
            with self._lock:
                if self._health_service is None:
                    from app.core.services.health_service import HealthService
                    self._health_service = HealthService()
        return self._health_service

    @property
    def route_service(self):
        if self._route_service is None:
            with self._lock:
                if self._route_service is None:
                    from app.services.route_service import RouteService
                    self._route_service = RouteService()
        return self._route_service

    @property
    def smart_ai_service(self):
        if self._smart_ai_service is None:
            with self._lock:
                if self._smart_ai_service is None:
                    from app.services.smart_ai_service import SmartAIService
                    self._smart_ai_service = SmartAIService()
        return self._smart_ai_service

    @property
    def yakit_tahmin_service(self):
        if self._yakit_tahmin_service is None:
            with self._lock:
                if self._yakit_tahmin_service is None:
                    from app.core.services.yakit_tahmin_service import YakitTahminService
                    self._yakit_tahmin_service = YakitTahminService()
        return self._yakit_tahmin_service

    @property
    def sofor_analiz_service(self):
        if self._sofor_analiz_service is None:
            with self._lock:
                if self._sofor_analiz_service is None:
                    from app.core.services.sofor_analiz_service import SoforAnalizService
                    self._sofor_analiz_service = SoforAnalizService()
        return self._sofor_analiz_service

    @property
    def degerlendirme_service(self):
        if self._degerlendirme_service is None:
            with self._lock:
                if self._degerlendirme_service is None:
                    from app.core.entities.sofor_degerlendirme import SoforDegerlendirmeService
                    # Get required repos from self properties to ensure they are initialized
                    self._degerlendirme_service = SoforDegerlendirmeService(
                        analiz_repo=self.analiz_repo,
                        sofor_repo=self.sofor_repo
                    )
        return self._degerlendirme_service

    @property
    def external_service(self):
        if self._external_service is None:
            with self._lock:
                if self._external_service is None:
                    from app.services.external_service import get_external_service
                    self._external_service = get_external_service()
        return self._external_service

    @property
    def weather_service(self):
        if self._weather_service is None:
            with self._lock:
                if self._weather_service is None:
                    from app.core.services.weather_service import get_weather_service
                    self._weather_service = get_weather_service()
        return self._weather_service

    def shutdown(self) -> None:
        """
        Tüm servisleri ve kaynakları temizle.
        Garbage collection'a yardımcı olur ve bağlantıları keser.
        """
        with self._lock:
            # Servisleri sıfırla (Dependency sırasının tersine)
            self._degerlendirme_service = None
            self._smart_ai_service = None
            self._route_service = None
            self._prediction_service = None
            self._report_service = None
            self._analiz_service = None
            self._import_service = None
            self._yakit_service = None
            self._lokasyon_service = None
            self._sefer_service = None
            self._sofor_service = None
            self._arac_service = None
            
            # Repositories
            self._yakit_repo = None
            self._lokasyon_repo = None
            self._sefer_repo = None
            self._sofor_repo = None
            self._arac_repo = None
            
            # Infrastructure
            self._event_bus = None


# Global Instance
_container: Optional[Container] = None
_container_lock = threading.Lock()





def get_container() -> Container:
    """Container singleton instance'ını getir (Thread-safe)."""
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = Container()
    return _container


def reset_container() -> None:
    """
    Container singleton'ını sıfırla (Thread-safe).
    
    ⚠️ SADECE TEST İÇİN KULLANIN!
    """
    global _container
    with _container_lock:
        if _container:
            _container.shutdown()
        _container = None
