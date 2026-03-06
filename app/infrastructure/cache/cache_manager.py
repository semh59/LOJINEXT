"""
TIR Yakıt Takip - Cache Manager
Gelecekte Redis entegrasyonuna izin verecek şekilde soyutlanmış cache katmanı.
"""

import fnmatch
import re
import threading
import time
from typing import Any, Dict, List, Optional

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

# Sensitive key pattern'leri
SENSITIVE_KEY_PATTERNS = re.compile(
    r"(password|token|secret|api_key|private_key|credential|auth)", re.IGNORECASE
)


class CacheManager:
    """
    Thread-Safe In-Memory Cache Manager.

    Features:
        - TTL (Time To Live) desteği
        - Pattern-based key silme (delete_pattern)
        - Cache statistics
        - Thread-safe operations
    """

    _instance = None
    _lock = threading.Lock()
    MAX_CACHE_SIZE = 10000

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CacheManager, cls).__new__(cls)
                    cls._instance._cache = {}
                    cls._instance._stats = {"hits": 0, "misses": 0, "evictions": 0}
                    cls._instance._stop_sweeper = False
                    cls._instance._start_sweeper()
        return cls._instance

    def _start_sweeper(self):
        """Süresi dolmuş cache'leri temizleyen daemon thread'i başlatır."""

        def sweep():
            while not self._stop_sweeper:
                time.sleep(300)  # 5 dakikada bir çalış
                self._sweep_expired()

        sweeper_thread = threading.Thread(target=sweep, daemon=True)
        sweeper_thread.start()
        logger.debug("Cache sweeper thread started.")

    def _sweep_expired(self):
        """Süresi dolmuş tüm anahtarları temizler."""
        now = time.time()
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v["expiry"] < now]
            for k in expired_keys:
                del self._cache[k]

            if expired_keys:
                self._stats["evictions"] += len(expired_keys)
                logger.debug(
                    f"Cache sweeper: {len(expired_keys)} expired keys removed."
                )

    def _validate_key(self, key: str):
        """Cache key güvenliği kontrolü"""
        if not key or len(key) > 256:
            raise ValueError("Cache key must be between 1 and 256 characters")

        # Directory traversal koruması (File-based cache'e geçilirse diye önlem)
        if "../" in key or "..\\" in key:
            raise ValueError("Invalid cache key: Directory traversal attempt")

        # Sensitive data koruması
        if SENSITIVE_KEY_PATTERNS.search(key):
            logger.warning(
                f"Sensitive key pattern detected and rejected: {key[:30]}..."
            )
            raise ValueError(
                "Cache key contains sensitive pattern (password/token/secret)"
            )

    def _evict_if_needed(self):
        """Cache doluysa yer aç (Simple Random Eviction)"""
        if len(self._cache) >= self.MAX_CACHE_SIZE:
            # %10 temizle
            keys_to_remove = list(self._cache.keys())[: int(self.MAX_CACHE_SIZE * 0.1)]
            for k in keys_to_remove:
                del self._cache[k]
            self._stats["evictions"] += len(keys_to_remove)
            logger.warning(f"Cache full, evicted {len(keys_to_remove)} items")

    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Veriyi cache'e kaydet (Thread-safe)"""
        self._validate_key(key)

        with self._lock:
            self._evict_if_needed()

            expiry = time.time() + ttl_seconds
            self._cache[key] = {"value": value, "expiry": expiry}

    def get(self, key: str) -> Optional[Any]:
        """Cache'den veri getir (Thread-safe)"""
        self._validate_key(key)

        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]
            if time.time() > entry["expiry"]:
                # Süresi dolmuş veriyi sil
                del self._cache[key]
                self._stats["evictions"] += 1
                return None

            self._stats["hits"] += 1
            return entry["value"]

    def delete(self, key: str) -> bool:
        """Belirli bir anahtarı sil"""
        self._validate_key(key)

        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Pattern ile eşleşen tüm anahtarları sil.

        Args:
            pattern: fnmatch pattern (örn: "stats:*", "arac:*:details")

        Returns:
            Silinen anahtar sayısı
        """
        if "../" in pattern:
            raise ValueError("Invalid pattern: Directory traversal attempt")

        with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)
            ]
            for key in keys_to_delete:
                del self._cache[key]

            if keys_to_delete:
                logger.debug(
                    f"Cache pattern delete: '{pattern}' - {len(keys_to_delete)} keys removed"
                )

            return len(keys_to_delete)

    def clear(self):
        """Tüm cache'i temizle"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {count} keys removed")

    def get_stats(self) -> Dict[str, Any]:
        """Cache istatistiklerini getir"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
            return {
                "size": len(self._cache),
                "max_size": self.MAX_CACHE_SIZE,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_rate_pct": round(hit_rate, 1),
            }

    def get_keys(self, pattern: str = "*") -> List[str]:
        """Pattern ile eşleşen anahtarları listele"""
        with self._lock:
            return [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]


# Singleton Provider
def get_cache_manager() -> CacheManager:
    return CacheManager()
