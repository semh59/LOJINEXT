"""
TIR Yakıt Takip Sistemi - Event Bus
Observer Pattern implementasyonu
"""

import asyncio
import hashlib
import inspect
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Set, Tuple

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class EventType(Enum):
    """Olay türleri"""
    # Veri değişiklikleri
    ARAC_ADDED = "arac_added"
    ARAC_UPDATED = "arac_updated"
    ARAC_DELETED = "arac_deleted"

    SOFOR_ADDED = "sofor_added"
    SOFOR_UPDATED = "sofor_updated"
    SOFOR_DELETED = "sofor_deleted"

    YAKIT_ADDED = "yakit_added"
    YAKIT_UPDATED = "yakit_updated"
    YAKIT_DELETED = "yakit_deleted"

    SEFER_ADDED = "sefer_added"
    SEFER_UPDATED = "sefer_updated"
    SEFER_DELETED = "sefer_deleted"

    LOKASYON_ADDED = "lokasyon_added"
    LOKASYON_UPDATED = "lokasyon_updated"
    LOKASYON_DELETED = "lokasyon_deleted"

    # Hesaplama olayları
    PERIYOT_CREATED = "periyot_created"
    YAKIT_DISTRIBUTED = "yakit_distributed"
    ANOMALY_DETECTED = "anomaly_detected"

    # UI olayları
    DATA_REFRESH_NEEDED = "data_refresh_needed"
    CACHE_INVALIDATED = "cache_invalidated"

    # Sistem olayları
    APP_STARTED = "app_started"
    APP_CLOSING = "app_closing"
    SETTINGS_CHANGED = "settings_changed"


@dataclass
class Event:
    """Olay verisi"""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""

    def __str__(self):
        return f"Event({self.type.value}, source={self.source})"


class EventBus:
    """
    Merkezi olay yönetim sistemi (Singleton).
    
    Observer Pattern implementasyonu:
    - subscribe(): Olaya abone ol
    - unsubscribe(): Aboneliği iptal et
    - publish(): Olay yayınla
    
    Thread-safe tasarım.
    
    Kullanım:
        event_bus = EventBus()
        
        # Abone ol
        def on_yakit_added(event: Event):
            print(f"Yeni yakıt: {event.data}")
        
        event_bus.subscribe(EventType.YAKIT_ADDED, on_yakit_added)
        
        # Olay yayınla
        event_bus.publish(Event(
            type=EventType.YAKIT_ADDED,
            data={"arac_id": 1, "litre": 250}
        ))
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._event_history: List[Event] = []
        self._failed_events: List[Tuple[Event, str, str, datetime]] = []  # DLQ: event, callback, error, time
        self._processed_events: Set[str] = set()  # Idempotency tracking
        self._max_history = 100
        self._max_dlq_size = 100
        self._max_processed_cache = 1000  # Son 1000 event ID
        self._max_payload_size = 1024 * 1024  # 1MB
        self._enabled = True
        self._initialized = True

    def _validate_event(self, event: Event):
        """Event validasyonu"""
        if not event or not event.type:
            raise ValueError("Invalid event: Event must have a type")
        if event.data is None:
            event.data = {}  # Default safe
        
        # Payload size limit
        payload_size = sys.getsizeof(str(event.data))
        if payload_size > self._max_payload_size:
            raise ValueError(f"Event payload too large: {payload_size} bytes (max {self._max_payload_size})")
    
    def _get_event_id(self, event: Event) -> str:
        """Event için unique ID üret (idempotency için)"""
        data_str = f"{event.type.value}:{event.timestamp.isoformat()}:{str(event.data)[:100]}"
        return hashlib.md5(data_str.encode()).hexdigest()[:16]
    
    def _is_duplicate(self, event: Event) -> bool:
        """Event daha önce işlendi mi kontrol et"""
        event_id = self._get_event_id(event)
        if event_id in self._processed_events:
            logger.debug(f"Duplicate event detected: {event_id}")
            return True
        
        # Cache'e ekle
        self._processed_events.add(event_id)
        
        # Cache boyutunu sınırla
        if len(self._processed_events) > self._max_processed_cache:
            # Eski entryleri temizle (basit FIFO - set'i yenile)
            self._processed_events = set(list(self._processed_events)[-500:])
        
        return False

    def _handle_failure(self, event: Event, callback_name: str, error: str):
        """Hata durumunu kaydet (DLQ yönetimi)"""
        if len(self._failed_events) >= self._max_dlq_size:
            # En eskiyi sil
            self._failed_events.pop(0)
            
        self._failed_events.append((event, callback_name, error, datetime.now()))


    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Olaya abone ol.
        
        Args:
            event_type: Abone olunacak olay türü
            callback: Olay tetiklendiğinde çağrılacak fonksiyon
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)


    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> bool:
        """
        Aboneliği iptal et.
        
        Args:
            event_type: Olay türü
            callback: Kaldırılacak callback
            
        Returns:
            Başarılı mı
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                return True
            except ValueError:
                pass
        return False

    async def publish_async(self, event: Event) -> int:
        """
        Olayı asenkron yayınla (Async IO dostu).
        
        Args:
            event: Yayınlanacak olay
            
        Returns:
            Bilgilendirilen abone sayısı
        """
        if not self._enabled:
            return 0
        
        self._validate_event(event)
        
        # Idempotency check
        if self._is_duplicate(event):
            logger.debug(f"Skipping duplicate event: {event.type.value}")
            return 0

        # Geçmişe ekle
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Abonelere bildir
        count = 0
        tasks = []

        for callback in self._subscribers.get(event.type, []):
            try:
                if inspect.iscoroutinefunction(callback):
                    # Async callback - await
                    await callback(event)
                else:
                    # Sync callback - run directly
                    callback(event)
                count += 1
            except Exception as e:
                callback_name = getattr(callback, "__name__", str(callback))
                logger.error(
                    f"EventBus async callback failed | Event: {event.type.value} | "
                    f"Callback: {callback_name} | Error: {e}",
                    exc_info=True
                )
                self._handle_failure(event, callback_name, str(e))

        return count

    def publish(self, event: Event) -> int:
        """
        Olay yayınla (Senkron).
        Uyarı: Async subscriber'lar 'fire-and-forget' mantığıyla task olarak atılır.
        """
        if not self._enabled:
            return 0
            
        self._validate_event(event)
        
        # Idempotency check
        if self._is_duplicate(event):
            logger.debug(f"Skipping duplicate event: {event.type.value}")
            return 0

        # Geçmişe ekle
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Abonelere bildir
        count = 0
        for callback in self._subscribers.get(event.type, []):
            try:
                if inspect.iscoroutinefunction(callback):
                    # Sync context -> Async callback
                    # Mevcut bir loop varsa task oluştur
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(callback(event))
                            count += 1
                        else:
                            logger.warning(
                                f"Skipping async subscriber {callback} inside sync publish (no running loop)"
                            )
                    except RuntimeError:
                         logger.warning(
                            f"Skipping async subscriber {callback} inside sync publish (RuntimeError getting loop)"
                        )
                else:
                    callback(event)
                    count += 1
            except Exception as e:
                # Log error with full context
                callback_name = getattr(callback, "__name__", str(callback))
                logger.error(
                    f"EventBus callback failed | Event: {event.type.value} | "
                    f"Callback: {callback_name} | Error: {e}",
                    exc_info=True
                )

                # Dead Letter Queue (DLQ)
                self._handle_failure(event, callback_name, str(e))

        return count


    async def publish_simple_async(self, event_type: EventType, **data) -> int:
        """Asenkron basit olay yayınla"""
        return await self.publish_async(Event(type=event_type, data=data))

    def publish_simple(self, event_type: EventType, **data) -> int:
        """Basit olay yayınla (Event nesnesi oluşturmadan)"""
        return self.publish(Event(type=event_type, data=data))

    def get_subscribers_count(self, event_type: EventType = None) -> int:
        """
        Abone sayısını getir.
        
        Args:
            event_type: Olay türü (None ise toplam)
            
        Returns:
            Abone sayısı
        """
        if event_type:
            return len(self._subscribers.get(event_type, []))

        return sum(len(subs) for subs in self._subscribers.values())

    def clear_history(self):
        """Olay geçmişini temizle"""
        self._event_history.clear()
        self._failed_events.clear()



def get_event_bus() -> EventBus:
    """EventBus singleton instance"""
    return EventBus()

# Decorator for auto-publishing
def publishes(event_type: EventType):
    """
    Method sonucu otomatik event publish eden decorator.
    Hem sync hem async metodları destekler.
    """
    from functools import wraps

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                await get_event_bus().publish_simple_async(event_type, result=result)
                return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                get_event_bus().publish_simple(event_type, result=result)
                return result
            return sync_wrapper

    return decorator

