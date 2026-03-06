from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.services.health_service import HealthService


@pytest.fixture
def health_service():
    return HealthService()


@pytest.mark.asyncio
async def test_check_db_healthy(health_service):
    # Mock AsyncSessionLocal
    with patch(
        "app.core.services.health_service.AsyncSessionLocal"
    ) as mock_session_cls:
        # Create a mock session object that will be returned by __aenter__
        mock_session = AsyncMock()
        mock_session.execute.return_value = None

        # Configure the context manager to return our mock session
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_session
        mock_ctx.__aexit__.return_value = None

        # When AsyncSessionLocal() is called, return the context manager
        mock_session_cls.return_value = mock_ctx

        result = await health_service.check_db()

        assert result["status"] == "healthy"
        assert "latency_ms" in result
        mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_check_db_unhealthy(health_service):
    with patch(
        "app.core.services.health_service.AsyncSessionLocal"
    ) as mock_session_cls:
        # Configure context manager to raise exception on enter
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.side_effect = Exception("DB Down")
        mock_session_cls.return_value = mock_ctx

        result = await health_service.check_db()

        assert result["status"] == "unhealthy"
        assert result["error"] == "DB Down"


@pytest.mark.asyncio
async def test_check_ai_readiness_healthy(health_service):
    # get_rag_engine fonksiyon içinde import edildiği için kaynağından (app.core.ai.rag_engine) patch edilmeli
    with patch("app.core.ai.rag_engine.get_rag_engine") as mock_get_rag:
        mock_rag = Mock()
        mock_rag.get_stats.return_value = {"initialized": True, "total_documents": 100}
        mock_get_rag.return_value = mock_rag

        result = await health_service.check_ai_readiness()

        assert result["status"] == "healthy"
        assert result["rag_engine"]["total_documents"] == 100
        assert "LightGBM" in result["models"]


@pytest.mark.asyncio
async def test_check_ai_readiness_degraded(health_service):
    with patch("app.core.ai.rag_engine.get_rag_engine") as mock_get_rag:
        mock_rag = Mock()
        mock_rag.get_stats.return_value = {"initialized": False}
        mock_get_rag.return_value = mock_rag

        result = await health_service.check_ai_readiness()

        assert result["status"] == "degraded"
        assert result["rag_engine"]["initialized"] is False


@pytest.mark.asyncio
async def test_get_full_status(health_service):
    # Mock internal methods
    with (
        patch.object(
            health_service, "check_db", return_value={"status": "healthy"}
        ) as mock_db,
        patch.object(
            health_service, "check_ai_readiness", return_value={"status": "healthy"}
        ) as mock_ai,
    ):
        result = await health_service.get_full_status()

        assert result["status"] == "healthy"
        assert "uptime_seconds" in result
        assert result["components"]["database"]["status"] == "healthy"
        assert result["components"]["ai_engine"]["status"] == "healthy"
