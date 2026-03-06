import asyncio
import json
from unittest.mock import patch

import pytest

from app.infrastructure.cache.redis_cache import get_redis_cache
from app.infrastructure.events.event_bus import Event, EventType, get_event_bus
from app.infrastructure.logging.logger import get_logger


@pytest.mark.asyncio
async def test_cache_fallback_ttl():
    """Fallback cache TTL kontrolü"""
    cache = get_redis_cache()
    # Redis'in kapalı olduğunu simüle et (fallback moduna geç)
    with patch.object(cache, "_redis_client", None):
        key = "test_ttl_key"
        val = {"data": "test"}
        cache.set(key, val, ttl=1)  # 1 saniye TTL

        # Hemen kontrol et
        assert cache.get(key) == val

        # 1.1 saniye bekle
        await asyncio.sleep(1.1)

        # Süresi dolmuş olmalı
        assert cache.get(key) is None


@pytest.mark.asyncio
async def test_event_bus_handler_isolation():
    """Bir handler fail olduğunda diğeri çalışmalı"""
    bus = get_event_bus()

    handler1_called = False
    handler2_called = False

    async def failing_handler(event):
        nonlocal handler1_called
        handler1_called = True
        raise ValueError("Intentional failure")

    async def success_handler(event):
        nonlocal handler2_called
        handler2_called = True

    bus.subscribe(EventType.DATA_REFRESH_NEEDED, failing_handler)
    bus.subscribe(EventType.DATA_REFRESH_NEEDED, success_handler)

    await bus.publish_async(Event(type=EventType.DATA_REFRESH_NEEDED))

    assert handler1_called
    assert handler2_called  # İkinci handler çalışmış olmalı


def test_logging_json_integrity():
    """Log injection denemesinde JSON bütünlüğü bozulmamalı"""
    logger = get_logger("test_integrity")

    # Newline injection içeren mesaj
    malicious_msg = 'Normal message\n{"extra": "malicious"}'

    # Bu testi manuel log kontrolü yerine JSONFormatter'ı doğrudan çağırarak yapalım
    import logging

    from app.infrastructure.logging.logger import JSONFormatter

    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=malicious_msg,
        args=None,
        exc_info=None,
    )

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    # Mesaj field'ı injection'ı bir string olarak içermeli, JSON yapısını bozmamalı
    assert parsed["message"] == malicious_msg
    # "extra" anahtarı kök dizinde olmamalı (injection başarısız)
    assert "extra" not in parsed or parsed.get("extra") != "malicious"
