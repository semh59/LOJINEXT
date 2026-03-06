import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import jwt, JWTError

from app.config import settings
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # user_email -> list of websockets
        self.user_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        str_message = json.dumps(message)
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(str_message)
                except Exception as e:
                    logger.error(f"WebSocket send error for user {user_id}: {e}")
                    self.disconnect(connection, user_id)

    async def broadcast(self, message: dict):
        str_message = json.dumps(message)
        for user_id, connections in list(self.user_connections.items()):
            for connection in connections:
                try:
                    await connection.send_text(str_message)
                except Exception as e:
                    logger.error(f"WebSocket broadcast error: {e}")
                    self.disconnect(connection, user_id)


training_ws_manager = ConnectionManager()
notification_ws_manager = ConnectionManager()


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
    Expects connection string: /api/v1/admin/ws/training?token=xxx
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    email = await verify_ws_token(token)
    if not email:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await training_ws_manager.connect(websocket, email)
    logger.info(f"WebSocket User {email} connected to training monitor.")

    try:
        while True:
            # We just keep the connection open and wait for messages.
            # Client can send simple 'ping' requests
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        training_ws_manager.disconnect(websocket, email)
        logger.info(f"WebSocket User {email} disconnected from training monitor.")


@router.websocket("/live")
async def notifications_ws(websocket: WebSocket):
    """
    WebSocket endpoint for real-time notifications.
    Expects connection string: /api/v1/admin/ws/live?token=xxx
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    email = await verify_ws_token(token)
    if not email:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await notification_ws_manager.connect(websocket, email)
    logger.info(f"User {email} connected to live notifications.")

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        notification_ws_manager.disconnect(websocket, email)
        logger.info(f"User {email} disconnected from live notifications.")
