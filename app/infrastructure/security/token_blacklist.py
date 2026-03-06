import threading
from datetime import datetime, timezone
from typing import Set


class TokenBlacklist:
    """
    Thread-safe in-memory blacklist for JWT tokens.
    In a production environment with multiple instances, this should be replaced by Redis.
    """

    _instance = None
    _lock = threading.Lock()
    _blacklist: Set[str] = set()
    _expirations: dict[str, datetime] = {}

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TokenBlacklist, cls).__new__(cls)
            return cls._instance

    def add(self, token: str, expires_at: datetime):
        """Add token to blacklist until its expiration."""
        with self._lock:
            self._blacklist.add(token)
            self._expirations[token] = expires_at.replace(tzinfo=timezone.utc)
            self._cleanup()

    def is_blacklisted(self, token: str) -> bool:
        """Check if token is in blacklist."""
        with self._lock:
            self._cleanup()
            return token in self._blacklist

    def _cleanup(self):
        """Remove expired tokens from blacklist memory."""
        now = datetime.now(timezone.utc)
        expired = [t for t, exp in self._expirations.items() if exp < now]
        for t in expired:
            self._blacklist.remove(t)
            del self._expirations[t]


blacklist = TokenBlacklist()
