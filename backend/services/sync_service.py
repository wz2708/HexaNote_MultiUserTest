"""
Sync service for real-time note synchronization.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Set
from datetime import datetime
from fastapi import WebSocket
import json

from models.note import Note
from models.device import Device
from models.sync_state import SyncState
from schemas.sync_schema import SyncRequest, SyncResponse, ConflictItem
from schemas.note_schema import NoteResponse


class WebSocketManager:
    """Manage WebSocket connections for real-time sync."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}  # device_id -> set of websockets

    async def connect(self, websocket: WebSocket, device_id: str):
        """Connect a WebSocket client."""
        await websocket.accept()
        if device_id not in self.active_connections:
            self.active_connections[device_id] = set()
        self.active_connections[device_id].add(websocket)

    def disconnect(self, websocket: WebSocket, device_id: str):
        """Disconnect a WebSocket client."""
        if device_id in self.active_connections:
            self.active_connections[device_id].discard(websocket)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]

    async def broadcast_to_device(self, device_id: str, message: dict):
        """Broadcast message to all connections of a device."""
        if device_id in self.active_connections:
            for connection in self.active_connections[device_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass  # Connection closed

    async def broadcast_except(self, exclude_device: str, message: dict):
        """Broadcast to all devices except one."""
        for device_id, connections in self.active_connections.items():
            if device_id != exclude_device:
                for connection in connections:
                    try:
                        await connection.send_json(message)
                    except:
                        pass


class SyncService:
    """Service for note synchronization."""

    def __init__(self):
        self.ws_manager = WebSocketManager()

    def sync_notes(
        self,
        db: Session,
        request: SyncRequest
    ) -> SyncResponse:
        """Process sync request and return changes."""
        conflicts = []
        notes_to_update = []
        notes_to_delete = []

        # Get notes modified since last sync
        server_notes = db.query(Note).filter(
            Note.updated_at > request.last_sync_timestamp
        ).all()

        for note in server_notes:
            if note.deleted_at:
                notes_to_delete.append(note.id)
            else:
                notes_to_update.append(self._note_to_response(note))

        # Process client changes
        for sync_item in request.notes:
            if sync_item.action == "delete":
                # Handle delete
                note = db.query(Note).filter(Note.id == sync_item.id).first()
                if note:
                    note.deleted_at = datetime.utcnow()
                    db.commit()
            elif sync_item.action in ["create", "update"]:
                note = db.query(Note).filter(Note.id == sync_item.id).first()

                if note and note.version != sync_item.version:
                    # Conflict detected
                    conflicts.append(ConflictItem(
                        note_id=sync_item.id,
                        client_version=sync_item.version,
                        server_version=note.version,
                        server_note=self._note_to_response(note)
                    ))
                elif sync_item.data:
                    # Accept change (simplified - should use NoteService)
                    if not note:
                        note = Note(
                            id=sync_item.id,
                            title=sync_item.data.get("title", ""),
                            content=sync_item.data.get("content", ""),
                            tags=json.dumps(sync_item.data.get("tags", [])),
                            version=1
                        )
                        db.add(note)
                    else:
                        note.title = sync_item.data.get("title", note.title)
                        note.content = sync_item.data.get("content", note.content)
                        note.tags = json.dumps(sync_item.data.get("tags", []))
                        note.version += 1
                        note.updated_at = datetime.utcnow()
                    db.commit()

        return SyncResponse(
            notes_to_update=notes_to_update,
            notes_to_delete=notes_to_delete,
            conflicts=conflicts,
            server_timestamp=datetime.utcnow()
        )

    def _note_to_response(self, note: Note) -> NoteResponse:
        """Convert Note model to NoteResponse."""
        return NoteResponse(
            id=note.id,
            title=note.title,
            content=note.content,
            tags=json.loads(note.tags) if note.tags else [],
            version=note.version,
            weaviate_uuid=note.weaviate_uuid,
            created_at=note.created_at,
            updated_at=note.updated_at,
            deleted_at=note.deleted_at
        )


# Global instance
sync_service = SyncService()
