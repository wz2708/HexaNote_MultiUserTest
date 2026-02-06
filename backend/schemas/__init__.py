"""
Pydantic schemas for HexaNote API.
"""
from schemas.note_schema import (
    NoteBase,
    NoteCreate,
    NoteUpdate,
    NotePartialUpdate,
    NoteResponse,
    NoteListResponse,
    TagCount,
    TagListResponse,
)
from schemas.sync_schema import (
    NoteSyncItem,
    SyncRequest,
    ConflictItem,
    SyncResponse,
    SyncStatusResponse,
    DeviceRegisterRequest,
    DeviceRegisterResponse,
)
from schemas.chat_schema import (
    ChatRequest,
    ContextNote,
    ChatResponse,
    ChatMessageResponse,
    ChatHistoryResponse,
    SessionCreateResponse,
)
from schemas.auth_schema import (
    TokenRequest,
    TokenResponse,
    HealthResponse,
)

__all__ = [
    # Note schemas
    "NoteBase",
    "NoteCreate",
    "NoteUpdate",
    "NotePartialUpdate",
    "NoteResponse",
    "NoteListResponse",
    "TagCount",
    "TagListResponse",
    # Sync schemas
    "NoteSyncItem",
    "SyncRequest",
    "ConflictItem",
    "SyncResponse",
    "SyncStatusResponse",
    "DeviceRegisterRequest",
    "DeviceRegisterResponse",
    # Chat schemas
    "ChatRequest",
    "ContextNote",
    "ChatResponse",
    "ChatMessageResponse",
    "ChatHistoryResponse",
    "SessionCreateResponse",
    # Auth schemas
    "TokenRequest",
    "TokenResponse",
    "HealthResponse",
]
