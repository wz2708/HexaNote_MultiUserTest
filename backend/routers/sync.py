"""
Sync API router for real-time synchronization.
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import json

from database import get_db
from services.sync_service import sync_service
from schemas.sync_schema import SyncRequest, SyncResponse

router = APIRouter()


@router.post("", response_model=SyncResponse)
def sync_notes(
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """Batch sync notes."""
    return sync_service.sync_notes(db, request)


@router.websocket("/ws")
async def websocket_sync(websocket: WebSocket, device_id: str = "default"):
    """WebSocket endpoint for real-time sync."""
    await sync_service.ws_manager.connect(websocket, device_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") in ["note_create", "note_update", "note_delete"]:
                # Broadcast to other devices
                await sync_service.ws_manager.broadcast_except(
                    exclude_device=device_id,
                    message=message
                )
            # Add more message handlers as needed

    except WebSocketDisconnect:
        sync_service.ws_manager.disconnect(websocket, device_id)
