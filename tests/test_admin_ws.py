import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.api.v1.endpoints.admin_ws import training_ws_manager
from app.infrastructure.security.jwt_handler import create_access_token
from app.config import settings

client = TestClient(app)


@pytest.mark.asyncio
async def test_ws_connection_unauthorized():
    """Verify that WS rejects connections without token."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/admin/ws/training"):
            pass
    assert exc_info.value.code == 1008


@pytest.mark.asyncio
async def test_ws_connection_authorized():
    """Verify successful secure WS connection with token."""
    token = create_access_token(
        data={"sub": settings.SUPER_ADMIN_USERNAME, "typ": "access", "is_super": True}
    )

    with client.websocket_connect(
        f"/api/v1/admin/ws/training?token={token}"
    ) as websocket:
        websocket.send_text("ping")
        data = websocket.receive_json()
        assert data["type"] == "pong"


@pytest.mark.asyncio
async def test_ws_broadcast():
    """Verifies that manager correctly broadcasts to connected agents."""
    # We need to mock the websocket list to avoid real IO during broadcast test
    mock_ws = AsyncMock()
    training_ws_manager.active_connections = [mock_ws]

    test_msg = {"event": "progress", "value": 45}
    await training_ws_manager.broadcast(test_msg)

    mock_ws.send_text.assert_called_once()
    sent_data = json.loads(mock_ws.send_text.call_args[0][0])
    assert sent_data["value"] == 45

    # Clean up
    training_ws_manager.active_connections = []
