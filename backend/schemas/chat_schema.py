"""
Pydantic schemas for Chat/RAG API requests and responses.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class ChatRequest(BaseModel):
    """Schema for chat query request."""
    message: str = Field(..., min_length=1, description="User's question or message")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")
    note_filter: Optional[List[str]] = Field(None, description="Optional tag filter for note search")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of notes to use as context")
    additional_context: Optional[str] = Field(None, description="Additional context to include without vectorization")


class ContextNote(BaseModel):
    """Schema for context note information in chat response."""
    note_id: str
    title: str
    content_preview: str = Field(..., description="Preview of note content")
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Schema for chat query response."""
    message: str = Field(..., description="AI-generated response")
    session_id: str = Field(..., description="Session ID for this conversation")
    context_notes: List[ContextNote] = Field(default_factory=list, description="Notes used as context")
    created_at: datetime


class ChatMessageResponse(BaseModel):
    """Schema for individual chat message in history."""
    id: str
    session_id: str
    role: str = Field(..., description="Message role: user | assistant")
    content: str
    context_note_ids: List[str] = Field(default_factory=list, description="Note IDs used for this message")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    """Schema for chat history response."""
    messages: List[ChatMessageResponse]
    session_id: str
    total: int = Field(..., description="Total number of messages in session")


class SessionCreateResponse(BaseModel):
    """Schema for new session creation response."""
    session_id: str = Field(..., description="New session UUID")
