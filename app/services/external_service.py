import asyncio
import threading
from datetime import datetime
from typing import Dict, Optional

import httpx

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class ExternalService:
    """
    Harici Servis Entegrasyonları.
    
    Bu sınıf, dış API'lere (Open-Meteo vb.) bağlanan HTTP client'ları yönetir.
    
    Features:
        - Persistent HTTP client (Connection Pooling)
        - Circuit Breaker pattern (Cascading failure prevention)
        - Thread-safe async operations (asyncio.Lock)
        - Automatic timeout handling (10s)
        - Offline fallback support
        - Error logging with structured format
        - Graceful shutdown support (close method)
    
    Supported Services:
        - Open-Meteo: Hava durumu tahminleri (ücretsiz, sınırsız)
    
    Thread Safety:
        - Singleton pattern thread-safe
        - Circuit breaker state protected by asyncio.Lock
        - HTTP client shared across requests (connection pooling)
    """
    
    OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Circuit Breaker parametreleri
    CB_FAILURE_THRESHOLD = 5
    CB_RECOVERY_TIMEOUT = 60  # saniye
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        # Circuit breaker state
        self._cb_failure_count = 0
        self._cb_last_failure_time: Optional[datetime] = None
        self._cb_is_open = False
        # Thread-safety için async lock
        self._cb_lock = asyncio.Lock()

    async def _check_circuit_breaker(self) -> bool:
        """
        Circuit breaker durumunu kontrol et (Thread-safe).
        
        Returns:
            True: İstek yapılabilir
            False: Circuit açık, fallback kullan
        """
        async with self._cb_lock:
            if not self._cb_is_open:
                return True
            
            # Recovery timeout kontrolü
            if self._cb_last_failure_time:
                elapsed = (datetime.now() - self._cb_last_failure_time).total_seconds()
                if elapsed >= self.CB_RECOVERY_TIMEOUT:
                    # Half-open: Bir deneme yap
                    logger.info("Circuit breaker HALF-OPEN, recovery deneniyor...")
                    self._cb_is_open = False
                    self._cb_failure_count = 0
                    return True
            
            return False
    
    async def _record_success(self):
        """Başarılı istek kaydı (Thread-safe)"""
        async with self._cb_lock:
            self._cb_failure_count = 0
            self._cb_is_open = False
    
    async def _record_failure(self):
        """Hatalı istek kaydı (Thread-safe)"""
        async with self._cb_lock:
            self._cb_failure_count += 1
            self._cb_last_failure_time = datetime.now()
            
            if self._cb_failure_count >= self.CB_FAILURE_THRESHOLD:
                self._cb_is_open = True
                logger.warning(
                    f"Circuit breaker AÇILDI! {self.CB_FAILURE_THRESHOLD} ardışık hata. "
                    f"Recovery: {self.CB_RECOVERY_TIMEOUT}s"
                )

    async def _get_client(self) -> httpx.AsyncClient:
        """
        Kalıcı AsyncClient döner (Connection Pooling).
        
        Returns:
            httpx.AsyncClient: Paylaşılan HTTP client instance
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client
    
    def _get_fallback_weather(self) -> Dict:
        """
        Mevsimsel ortalama değerler döner (Offline fallback).
        Circuit breaker açık olduğunda veya hata durumunda kullanılır.
        """
        import datetime as dt
        month = dt.date.today().month
        
        if month in [12, 1, 2]:
            # Kış
            return {"temp": 5, "precip": 30, "wind": 15, "source": "fallback_winter"}
        elif month in [6, 7, 8]:
            # Yaz
            return {"temp": 30, "precip": 5, "wind": 10, "source": "fallback_summer"}
        else:
            # İlkbahar/Güz
            return {"temp": 18, "precip": 15, "wind": 12, "source": "fallback_transition"}

    async def get_weather_forecast(self, lat: float, lon: float) -> Dict:
        """
        Open-Meteo'dan hava durumu tahmini al.
        
        Circuit breaker pattern ile korumalı (thread-safe).
        Hata durumunda offline fallback kullanır.
        
        Args:
            lat: Enlem (latitude)
            lon: Boylam (longitude)
            
        Returns:
            Dict: Hava durumu verisi veya fallback verisi
        """
        # Circuit breaker kontrolü (async)
        if not await self._check_circuit_breaker():
            logger.debug("Circuit breaker OPEN - using fallback")
            return self._get_fallback_weather()
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto"
        }
        try:
            client = await self._get_client()
            response = await client.get(self.OPENMETEO_URL, params=params)
            response.raise_for_status()
            await self._record_success()
            return response.json()
        except Exception as e:
            await self._record_failure()
            logger.error(f"Weather forecast error: {e}")
            return self._get_fallback_weather()

    async def close(self):
        """
        Client bağlantısını kapat (Lifespan temizliği için).
        
        Bu metod app shutdown sırasında çağrılmalıdır.
        """
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("ExternalService client closed.")


# Thread-safe Singleton
_external_service: Optional[ExternalService] = None
_external_service_lock = threading.Lock()


def get_external_service() -> ExternalService:
    """Thread-safe singleton getter"""
    global _external_service
    if _external_service is None:
        with _external_service_lock:
            if _external_service is None:
                _external_service = ExternalService()
    return _external_service

