"""
Pydantic schemas for Sync API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from schemas.note_schema import NoteResponse


class NoteSyncItem(BaseModel):
    """Schema for a single note sync item."""
    id: str = Field(..., description="Note UUID")
    version: int = Field(..., description="Note version")
    action: str = Field(..., description="Action: create | update | delete")
    data: Optional[dict] = Field(None, description="Note data for create/update")


class SyncRequest(BaseModel):
    """Schema for sync request from client."""
    device_id: str = Field(..., description="Client device identifier")
    last_sync_timestamp: datetime = Field(..., description="Last successful sync timestamp")
    notes: List[NoteSyncItem] = Field(default_factory=list, description="Changed notes to sync")


class ConflictItem(BaseModel):
    """Schema for sync conflict information."""
    note_id: str = Field(..., description="Note UUID with conflict")
    client_version: int = Field(..., description="Client's version number")
    server_version: int = Field(..., description="Server's version number")
    server_note: NoteResponse = Field(..., description="Current server note state")
    resolution_strategy: str = Field(default="server_wins", description="Suggested resolution strategy")


class SyncResponse(BaseModel):
    """Schema for sync response to client."""
    notes_to_update: List[NoteResponse] = Field(default_factory=list, description="Notes updated on server")
    notes_to_delete: List[str] = Field(default_factory=list, description="Note IDs deleted on server")
    conflicts: List[ConflictItem] = Field(default_factory=list, description="Conflicts detected")
    server_timestamp: datetime = Field(..., description="Server timestamp for this sync")


class SyncStatusResponse(BaseModel):
    """Schema for sync status query response."""
    device_id: str
    last_sync: Optional[datetime] = None
    pending_count: int = Field(default=0, description="Number of pending changes")
    status: str = Field(default="synced", description="Sync status: synced | pending | error")


class DeviceRegisterRequest(BaseModel):
    """Schema for device registration."""
    device_name: str = Field(..., min_length=1, max_length=200, description="Device name")
    device_type: str = Field(..., description="Device type: windows | android")


class DeviceRegisterResponse(BaseModel):
    """Schema for device registration response."""
    device_id: str = Field(..., description="Generated device ID")
    message: str = Field(default="Device registered successfully")
