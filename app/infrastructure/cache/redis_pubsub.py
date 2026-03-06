"""
Redis Async Pub/Sub Service
WebSocket yayınları ve asenkron Event-Driven mesajlaşma için kullanılır.
"""

import os
import json
from typing import Any, AsyncGenerator

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisPubSubManager:
    _instance = None
    _memory_store = {}  # Fallback for key-value (tickets)
    _subscribers = {}  # Fallback for pub/sub: {channel: [queue]}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._redis: aioredis.Redis | None = None
        self._connect()

    def _connect(self):
        if not REDIS_AVAILABLE:
            logger.warning("Redis async is not available. Using In-Memory fallback.")
            return

        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        redis_ssl = os.getenv("REDIS_SSL", "false").lower() == "true"

        scheme = "rediss" if redis_ssl else "redis"
        auth = f":{redis_password}@" if redis_password else ""
        url = f"{scheme}://{auth}{redis_host}:{redis_port}/{redis_db}"

        try:
            if redis_ssl:
                import ssl

                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                self._redis = aioredis.from_url(
                    url,
                    decode_responses=True,
                    ssl=ssl_context,
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0,  # Fast fail
                )
            else:
                self._redis = aioredis.from_url(
                    url,
                    decode_responses=True,
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0,  # Fast fail
                )
            logger.info(f"Async Redis PubSub connected to {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(
                f"Async Redis connection failed, switching to In-Memory: {e}"
            )
            self._redis = None

    async def publish(self, channel: str, message: Any) -> bool:
        """Kanal üzerinden mesaj gönder"""
        payload = json.dumps(message, ensure_ascii=False, default=str)

        if self._redis:
            try:
                await self._redis.publish(channel, payload)
                return True
            except Exception as e:
                logger.error(f"Redis publish error: {e}")
                # Fallback to memory even if redis failed

        # Memory Fallback
        if channel in self._subscribers:
            data = json.loads(payload)
            for q in self._subscribers[channel]:
                await q.put(data)
            return True
        return False

    async def subscribe(self, channel: str) -> AsyncGenerator[dict, None]:
        """Kanalı asenkron olarak dinle"""
        if self._redis:
            try:
                pubsub_conn = self._redis.pubsub()
                await pubsub_conn.subscribe(channel)
                try:
                    async for message in pubsub_conn.listen():
                        if message["type"] == "message":
                            try:
                                yield json.loads(message["data"])
                            except json.JSONDecodeError:
                                pass
                finally:
                    await pubsub_conn.unsubscribe(channel)
                    await pubsub_conn.close()
                return  # Success from Redis
            except Exception as e:
                logger.error(f"Redis subscribe failed, using memory: {e}")

        # Memory Fallback
        import asyncio

        q = asyncio.Queue()
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(q)

        try:
            while True:
                msg = await q.get()
                yield msg
        finally:
            if channel in self._subscribers:
                self._subscribers[channel].remove(q)

    # Key-Value Methods with Fallback
    async def set(self, key: str, value: Any, expire: int = None) -> bool:
        payload = json.dumps(value, ensure_ascii=False, default=str)
        if self._redis:
            try:
                await self._redis.set(key, payload, ex=expire)
                return True
            except Exception as e:
                logger.error(f"Redis set error ({key}): {e}")

        # Memory Fallback
        self._memory_store[key] = payload
        # Note: True expiration logic not strictly needed for short lived tickets in memory
        return True

    async def get(self, key: str) -> Any:
        if self._redis:
            try:
                data = await self._redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis get error ({key}): {e}")

        # Memory Fallback
        data = self._memory_store.get(key)
        return json.loads(data) if data else None

    async def delete(self, key: str) -> bool:
        if self._redis:
            try:
                await self._redis.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error ({key}): {e}")

        # Memory Fallback
        if key in self._memory_store:
            del self._memory_store[key]
            return True
        return False


def get_pubsub_manager() -> RedisPubSubManager:
    return RedisPubSubManager()


async def set_redis_val(key: str, value: Any, expire: int = None) -> bool:
    return await get_pubsub_manager().set(key, value, expire)


async def get_redis_val(key: str) -> Any:
    return await get_pubsub_manager().get(key)


async def delete_redis_val(key: str) -> bool:
    return await get_pubsub_manager().delete(key)
