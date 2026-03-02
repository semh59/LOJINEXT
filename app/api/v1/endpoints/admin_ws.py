import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from jose import jwt, JWTError

from app.config import settings
from app.database.unit_of_work import UnitOfWork
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        str_message = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(str_message)
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")
                self.disconnect(connection)


training_ws_manager = ConnectionManager()


async def verify_ws_token(token: str) -> Optional[str]:
    """Verify standard JWT token for WebSocket connection."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


@router.websocket("/training")
async def training_status_ws(websocket: WebSocket):
    """
    WebSocket endpoint for streaming real-time ML Training Progress.
    Expects connection string: /api/v1/ws/training?token=xxx
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    email = await verify_ws_token(token)
    if not email:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await training_ws_manager.connect(websocket)
    logger.info(f"WebSocket User {email} connected to training monitor.")

    try:
        while True:
            # We just keep the connection open and wait for messages.
            # Client can send simple 'ping' requests
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        training_ws_manager.disconnect(websocket)
        logger.info(f"WebSocket User {email} disconnected from training monitor.")
