"""
Circuit Breaker Pattern - Cascade Failure Prevention
External API hatalarında sistemi korur.
"""

import asyncio
import threading
import time
from enum import Enum
from functools import wraps
from typing import Callable, Dict, Optional, Type

from app.config import settings
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Normal çalışma
    OPEN = "open"          # Hatalar nedeniyle devre açık, istekler engelleniyor
    HALF_OPEN = "half_open"  # Test aşaması, tek istek geçiyor


class CircuitBreakerError(Exception):
    """Circuit açıkken fırlatılan exception"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker implementasyonu.
    
    States:
    - CLOSED: Normal, istekler geçiyor
    - OPEN: Hatalar sonrası, istekler engelleniyor
    - HALF_OPEN: Timeout sonrası, bir istek test ediliyor
    """
    
    def __init__(
        self,
        name: str,
        fail_max: int = 5,
        reset_timeout: float = 60.0,
        exclude_exceptions: tuple = ()
    ):
        """
        Args:
            name: Circuit breaker adı
            fail_max: OPEN state için gereken ardışık hata sayısı
            reset_timeout: OPEN → HALF_OPEN geçiş süresi (saniye)
            exclude_exceptions: Circuit'i tetiklememesi gereken exception'lar
        """
        self.name = name
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.exclude_exceptions = exclude_exceptions
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._async_lock = asyncio.Lock()
        self._sync_lock = threading.Lock()  # Sync context için
    
    @property
    def state(self) -> CircuitState:
        """Mevcut state (HALF_OPEN kontrolü ile)"""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and (time.time() - self._last_failure_time) >= self.reset_timeout:
                return CircuitState.HALF_OPEN
        return self._state
    
    async def call(self, func: Callable, *args, **kwargs):
        """
        Fonksiyonu circuit breaker koruması altında çağır (async).
        """
        async with self._async_lock:
            current_state = self.state
            
            if current_state == CircuitState.OPEN:
                logger.warning(f"Circuit '{self.name}' is OPEN, rejecting call")
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")
            
            if current_state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit '{self.name}' is HALF_OPEN, testing...")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            if not isinstance(e, self.exclude_exceptions):
                await self._on_failure()
            raise
    
    def call_sync(self, func: Callable, *args, **kwargs):
        """
        Fonksiyonu circuit breaker koruması altında çağır (sync).
        """
        with self._sync_lock:
            current_state = self.state
            
            if current_state == CircuitState.OPEN:
                logger.warning(f"Circuit '{self.name}' is OPEN, rejecting call")
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")
            
            if current_state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit '{self.name}' is HALF_OPEN, testing...")
        
        try:
            result = func(*args, **kwargs)
            self._on_success_sync()
            return result
        except Exception as e:
            if not isinstance(e, self.exclude_exceptions):
                self._on_failure_sync()
            raise
    
    async def _on_success(self):
        """Başarılı çağrı sonrası (async)"""
        async with self._async_lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit '{self.name}' recovered, closing")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
    
    def _on_success_sync(self):
        """Başarılı çağrı sonrası (sync)"""
        with self._sync_lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit '{self.name}' recovered, closing")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
    
    async def _on_failure(self):
        """Hatalı çağrı sonrası (async)"""
        async with self._async_lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._failure_count >= self.fail_max:
                self._state = CircuitState.OPEN
                logger.error(f"Circuit '{self.name}' OPENED after {self._failure_count} failures")
            elif self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit '{self.name}' test failed, reopening")
    
    def _on_failure_sync(self):
        """Hatalı çağrı sonrası (sync)"""
        with self._sync_lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._failure_count >= self.fail_max:
                self._state = CircuitState.OPEN
                logger.error(f"Circuit '{self.name}' OPENED after {self._failure_count} failures")
            elif self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit '{self.name}' test failed, reopening")
    
    def get_status(self) -> dict:
        """Circuit durumu"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "fail_max": self.fail_max,
            "reset_timeout": self.reset_timeout
        }


class CircuitBreakerRegistry:
    """
    Singleton registry for named circuit breakers.
    Thread-safe implementation.
    """
    _breakers: Dict[str, CircuitBreaker] = {}
    _async_lock = asyncio.Lock()
    _sync_lock = threading.Lock()  # Sync context için
    
    @classmethod
    async def get(
        cls,
        name: str,
        fail_max: int = settings.CB_FAIL_MAX,
        reset_timeout: float = settings.CB_RESET_TIMEOUT,
        exclude_exceptions: tuple = ()
    ) -> CircuitBreaker:
        """Named circuit breaker al veya oluştur (async)."""
        async with cls._async_lock:
            if name not in cls._breakers:
                cls._breakers[name] = CircuitBreaker(
                    name, fail_max, reset_timeout, exclude_exceptions
                )
                logger.info(f"Created circuit breaker '{name}': fail_max={fail_max}, reset={reset_timeout}s")
            return cls._breakers[name]
    
    @classmethod
    def get_sync(
        cls,
        name: str,
        fail_max: int = settings.CB_FAIL_MAX,
        reset_timeout: float = settings.CB_RESET_TIMEOUT
    ) -> CircuitBreaker:
        """Senkron ortamda breaker oluştur (thread-safe)"""
        with cls._sync_lock:
            if name not in cls._breakers:
                cls._breakers[name] = CircuitBreaker(name, fail_max, reset_timeout)
                logger.info(f"Created circuit breaker '{name}' (sync): fail_max={fail_max}, reset={reset_timeout}s")
            return cls._breakers[name]
    
    @classmethod
    def get_all_status(cls) -> list:
        """Tüm circuit breaker'ların durumu"""
        return [cb.get_status() for cb in cls._breakers.values()]


def circuit_protected(
    breaker_name: str,
    fail_max: int = settings.CB_FAIL_MAX,
    reset_timeout: float = settings.CB_RESET_TIMEOUT,
    fallback: Callable = None
):
    """
    Decorator: Fonksiyonu circuit breaker ile korur.
    
    Kullanım:
        @circuit_protected("openroute", fail_max=5, reset_timeout=60)
        async def call_openroute_api():
            ...
        
        # Fallback ile:
        @circuit_protected("weather", fallback=lambda: {"temp": 15, "source": "fallback"})
        async def get_weather():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = await CircuitBreakerRegistry.get(breaker_name, fail_max, reset_timeout)
            try:
                return await breaker.call(func, *args, **kwargs)
            except CircuitBreakerError:
                if fallback:
                    logger.info(f"Circuit '{breaker_name}' open, using fallback")
                    return fallback() if callable(fallback) else fallback
                raise
        return wrapper
    return decorator
