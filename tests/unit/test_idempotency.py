import pytest
from fastapi import Request, HTTPException
from unittest.mock import AsyncMock, patch, MagicMock

import app.infrastructure.cache.redis_pubsub
from app.infrastructure.resilience.idempotency import IdempotencyGuard


@pytest.mark.asyncio
async def test_idempotency_guard_no_key():
    guard = IdempotencyGuard()
    request = MagicMock(spec=Request)
    request.headers = {}

    # Should return silently
    result = await guard(request)
    assert result is None


@pytest.mark.asyncio
@patch("app.infrastructure.cache.redis_pubsub.get_pubsub_manager")
async def test_idempotency_guard_first_request(mock_get_redis):
    # Mock Redis client
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Key does not exist
    mock_get_redis.return_value = mock_redis

    guard = IdempotencyGuard()
    request = MagicMock(spec=Request)
    request.headers = {"X-Idempotency-Key": "test-key-123"}
    request.state = MagicMock()
    request.state.user = MagicMock(id=1)

    await guard(request)

    # Verify Redis checks and sets the key
    mock_redis.get.assert_called_once_with("idemp:1:test-key-123")
    mock_redis.set.assert_called_once_with(
        "idemp:1:test-key-123", "processing", expire=300
    )


@pytest.mark.asyncio
@patch("app.infrastructure.cache.redis_pubsub.get_pubsub_manager")
async def test_idempotency_guard_duplicate_request(mock_get_redis):
    # Mock Redis client
    mock_redis = AsyncMock()
    mock_redis.get.return_value = b"processing"  # Key exists
    mock_get_redis.return_value = mock_redis

    guard = IdempotencyGuard()
    request = MagicMock(spec=Request)
    request.headers = {"X-Idempotency-Key": "test-key-123"}
    request.state = MagicMock()
    request.state.user = MagicMock(id=1)

    # Verify HTTPException is raised
    with pytest.raises(HTTPException) as exc_info:
        await guard(request)

    assert exc_info.value.status_code == 409
    assert "zaten işleniyor" in exc_info.value.detail
