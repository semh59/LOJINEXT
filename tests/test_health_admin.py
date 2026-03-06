import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.services.health_service import HealthService


@pytest.mark.asyncio
async def test_health_service_admin_details():
    service = HealthService()

    # Mocking components that involve DB or RAG
    with patch.object(HealthService, "check_db", return_value={"status": "healthy"}):
        with patch.object(
            HealthService, "check_ai_readiness", return_value={"status": "healthy"}
        ):
            details = await service.get_admin_health_details()

            assert details["status"] == "healthy"
            assert "sentry" in details
            assert "circuit_breakers" in details
            assert "backups" in details
            assert details["sentry"]["enabled"] is False  # Default for tests usually


@pytest.mark.asyncio
async def test_health_service_check_db_healthy():
    """Verify DB health check logic."""
    service = HealthService()
    # Need to mock the AsyncSessionLocal context manager
    with patch(
        "app.core.services.health_service.AsyncSessionLocal"
    ) as mock_session_cls:
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        status = await service.check_db()
        assert status["status"] == "healthy"
        assert "latency_ms" in status


@pytest.mark.asyncio
async def test_health_service_check_ai_readiness_failure():
    """Verify AI readiness when RAG fails or is not initialized."""
    service = HealthService()
    # Path changed to where it's actually imported in the service method or where it resides
    with patch("app.core.ai.rag_engine.get_rag_engine") as mock_get_rag:
        mock_rag = MagicMock()
        mock_rag.get_stats.return_value = {"initialized": False}
        mock_get_rag.return_value = mock_rag

        status = await service.check_ai_readiness()
        assert status["status"] == "degraded"
