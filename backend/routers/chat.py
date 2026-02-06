"""
Chat API router for RAG-powered conversations.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from database import get_db
from services.weaviate_service import get_weaviate_service, WeaviateService
from services.chat_service import ChatService
from schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ChatMessageResponse,
    SessionCreateResponse,
)

router = APIRouter()


def get_chat_service(weaviate: WeaviateService = Depends(get_weaviate_service)) -> ChatService:
    """Dependency for ChatService."""
    return ChatService(weaviate)


@router.post("/query", response_model=ChatResponse)
def chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Process a chat query using RAG."""
    return chat_service.process_query(db, request)


@router.get("/history", response_model=ChatHistoryResponse)
def get_chat_history(
    session_id: str = Query(..., description="Session ID"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get chat history for a session."""
    messages = chat_service.get_history(db, session_id, limit)
    return ChatHistoryResponse(
        messages=[ChatMessageResponse.model_validate(msg) for msg in messages],
        session_id=session_id,
        total=len(messages)
    )


@router.post("/sessions", response_model=SessionCreateResponse)
def create_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    return SessionCreateResponse(session_id=session_id)
