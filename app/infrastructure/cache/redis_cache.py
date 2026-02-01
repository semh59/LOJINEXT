"""
Redis Cache Service - Yakıt Yönetim Sistemi
Tekrar eden sorgular için önbellekleme
"""

import hashlib
import json
import os
import re
import threading
from typing import Any, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.infrastructure.logging.logger import get_logger
from app.infrastructure.cache.cache_manager import get_cache_manager

logger = get_logger(__name__)


class RedisCache:
    """
    Redis tabanlı cache sistemi.
    
    Redis yoksa veya bağlantı başarısızsa,
    in-memory fallback kullanır.
    """

    _instance = None
    _lock = threading.Lock()  # Thread-safe singleton için
    
    # Key'de izin verilmeyen karakterler
    _KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_:.\-]+$')

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._redis_client = None
        self._fallback = get_cache_manager()
        self._default_ttl = 3600  # 1 saat

        # Redis bağlantısını dene
        self._connect()

    def _connect(self):
        """Redis bağlantısı kur"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis kütüphanesi yüklü değil. In-memory cache kullanılacak.")
            return

        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        redis_ssl = os.getenv("REDIS_SSL", "false").lower() == "true"

        try:
            self._redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                ssl=redis_ssl,  # SSL/TLS desteği
                ssl_cert_reqs='required' if redis_ssl else None
            )
            # Bağlantı testi
            self._redis_client.ping()
            ssl_status = " (SSL)" if redis_ssl else ""
            logger.info(f"Redis bağlantısı kuruldu: {redis_host}:{redis_port}{ssl_status}")
        except Exception as e:
            logger.warning(f"Redis bağlantısı kurulamadı: {e}. In-memory cache kullanılacak.")
            self._redis_client = None

    @property
    def is_redis_available(self) -> bool:
        """Redis kullanılabilir mi?"""
        return self._redis_client is not None

    def _validate_key(self, key: str):
        """Cache key güvenliği kontrolü"""
        # Redis key length limit is 512MB technically but we want sane limits
        if not key or len(key) > 512: 
            raise ValueError("Cache key too long (max 512 chars)")
        
        # Karakter kontrolü - sadece güvenli karakterler
        if not self._KEY_PATTERN.match(key):
            raise ValueError(f"Invalid cache key characters: {key[:50]}")
        
        # Directory traversal koruması
        if "../" in key or "..\\" in key:
            raise ValueError("Invalid cache key: Directory traversal attempt")
        
    def _evict_fallback_if_needed(self):
        """Fallback cache dolarsa yer aç"""
        if len(self._fallback_cache) >= self.MAX_FALLBACK_SIZE:
             # %10 temizle
            keys = list(self._fallback_cache.keys())
            to_remove = keys[:int(self.MAX_FALLBACK_SIZE * 0.1)]
            for k in to_remove:
                self._fallback_cache.pop(k, None)
                self._fallback_expiry.pop(k, None)
            logger.warning(f"Fallback cache full, evicted {len(to_remove)} items")

    def _generate_key(self, query: str, prefix: str = "qc") -> str:
        """Sorgu için unique cache key oluştur"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"{prefix}:{query_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Cache'den değer al.
        
        Args:
            key: Cache anahtarı
            
        Returns:
            Cache değeri veya None
        """
        self._validate_key(key)
        
        try:
            if self._redis_client:
                cached = self._redis_client.get(key)
                if cached:
                    logger.debug(f"✅ Redis cache hit: {key[:20]}...")
                    return json.loads(cached)
            else:
                # Use central CacheManager as fallback
                logger.debug(f"✅ Fallback to Memory cache: {key[:20]}...")
                return self._fallback.get(key)
        except Exception as e:
            logger.error(f"Cache get hatası: {e}")

        return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Cache'e değer yaz.
        
        Args:
            key: Cache anahtarı
            value: Saklanacak değer
            ttl: Time-to-live (saniye)
            
        Returns:
            Başarılı mı
        """
        self._validate_key(key)
        ttl = ttl or self._default_ttl

        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)

            if self._redis_client:
                self._redis_client.setex(key, ttl, serialized)
                logger.debug(f"Redis cache set: {key[:20]}... (TTL: {ttl}s)")
            else:
                # Use central CacheManager as fallback
                self._fallback.set(key, value, ttl)
                logger.debug(f"Fallback Memory cache set: {key[:20]}... (TTL: {ttl}s)")

            return True
        except Exception as e:
            logger.error(f"Cache set hatası: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Cache'den sil"""
        try:
            if self._redis_client:
                self._redis_client.delete(key)
            else:
                self._fallback.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete hatası: {e}")
            return False

    def clear_all(self) -> bool:
        """Tüm cache'i temizle"""
        try:
            if self._redis_client:
                self._redis_client.flushdb()
            else:
                self._fallback.clear()
            logger.info("Cache temizlendi")
            return True
        except Exception as e:
            logger.error(f"Cache clear hatası: {e}")
            return False

    def get_cached_response(self, query: str) -> Optional[str]:
        """Sorgu için cache'lenmiş yanıt al"""
        key = self._generate_key(query)
        return self.get(key)

    def cache_response(self, query: str, response: str, ttl: int = None) -> bool:
        """Sorgu yanıtını cache'le"""
        key = self._generate_key(query)
        return self.set(key, response, ttl)

    def get_stats(self) -> dict:
        """Cache istatistikleri"""
        stats = {
            "backend": "redis" if self._redis_client else "memory",
            "connected": self.is_redis_available
        }

        if self._redis_client:
            try:
                info = self._redis_client.info("memory")
                stats["used_memory"] = info.get("used_memory_human", "N/A")
                stats["keys"] = self._redis_client.dbsize()
            except:
                pass
        else:
            stats["keys"] = len(self._fallback_cache)

        return stats


# Singleton accessor
def get_redis_cache() -> RedisCache:
    """Redis cache singleton'ı getir"""
    return RedisCache()


# Decorator for caching function results
def cached(ttl: int = 3600, prefix: str = "fn"):
    """
    Fonksiyon sonuçlarını cache'leyen decorator.
    
    Kullanım:
        @cached(ttl=600)
        def expensive_calculation(param):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_redis_cache()

            # Key oluştur
            key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            key = cache._generate_key(key_data, prefix)

            # Cache kontrol
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result

            # Hesapla ve cache'le
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)

            return result
        return wrapper
    return decorator
