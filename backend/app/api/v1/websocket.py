"""WebSocket API for real-time updates."""

import asyncio
import json
from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from starlette.websockets import WebSocketState

from backend.app.core.security import decode_token

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections per tenant."""

    def __init__(self):
        # tenant_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str):
        """Accept and register a new connection."""
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = set()
        self.active_connections[tenant_id].add(websocket)

    def disconnect(self, websocket: WebSocket, tenant_id: str):
        """Remove a connection."""
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].discard(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific connection."""
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json(message)

    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        """Broadcast message to all connections for a tenant."""
        if tenant_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[tenant_id]:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # Clean up disconnected connections
            for conn in disconnected:
                self.active_connections[tenant_id].discard(conn)


manager = ConnectionManager()


@router.websocket("/live")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time updates.

    Connect with: ws://host/api/v1/ws/live?token=<jwt_token>

    Events sent:
    - signal_new: New signal received
    - signal_parsed: Signal successfully parsed
    - trade_opened: Trade opened on MT5
    - trade_closed: Trade closed
    - trade_updated: Trade status updated
    - account_sync: MT5 account sync completed
    - error: Error occurred
    """
    # Verify token
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Invalid token")
        return

    tenant_id = payload.get("sub")
    if not tenant_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    # Connect
    await manager.connect(websocket, tenant_id)

    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "connected",
                "message": "WebSocket connection established",
            },
            websocket,
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (ping/pong, commands, etc.)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,  # Timeout for keepalive
                )

                try:
                    message = json.loads(data)

                    # Handle ping
                    if message.get("type") == "ping":
                        await manager.send_personal_message(
                            {"type": "pong"},
                            websocket,
                        )
                    # Handle other commands if needed
                    else:
                        await manager.send_personal_message(
                            {
                                "type": "ack",
                                "message": "Message received",
                            },
                            websocket,
                        )
                except json.JSONDecodeError:
                    await manager.send_personal_message(
                        {
                            "type": "error",
                            "message": "Invalid JSON",
                        },
                        websocket,
                    )

            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await manager.send_personal_message(
                        {"type": "ping"},
                        websocket,
                    )
                except Exception:
                    break

    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)
    except Exception:
        manager.disconnect(websocket, tenant_id)


async def broadcast_signal_event(tenant_id: str, event_type: str, data: dict):
    """Broadcast a signal-related event to all tenant connections."""
    await manager.broadcast_to_tenant(
        tenant_id,
        {
            "type": event_type,
            "data": data,
        },
    )


async def broadcast_trade_event(tenant_id: str, event_type: str, data: dict):
    """Broadcast a trade-related event to all tenant connections."""
    await manager.broadcast_to_tenant(
        tenant_id,
        {
            "type": event_type,
            "data": data,
        },
    )


# Export for use in other modules
def get_connection_manager() -> ConnectionManager:
    """Get the connection manager instance."""
    return manager
