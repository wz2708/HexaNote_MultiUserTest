"""
Chat service for RAG-powered conversations.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
import json

from models.chat import ChatHistory
from services.weaviate_service import WeaviateService
from schemas.chat_schema import ChatRequest, ChatResponse, ContextNote


class ChatService:
    """Service for RAG chat operations."""

    def __init__(self, weaviate_service: WeaviateService):
        self.weaviate = weaviate_service

    def process_query(
        self,
        db: Session,
        request: ChatRequest
    ) -> ChatResponse:
        """Process a chat query using RAG."""
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Store user message
        user_message = ChatHistory(
            session_id=session_id,
            role="user",
            content=request.message,
            context_note_ids="[]"
        )
        db.add(user_message)

        # Perform RAG search with optional additional context
        rag_result = self.weaviate.generative_search(
            query=request.message,
            limit=request.limit,
            tag_filter=request.note_filter,
            additional_context=request.additional_context
        )

        # Format context notes
        context_notes = [
            ContextNote(
                note_id=note["note_id"],
                title=note["title"],
                content_preview=note["content_preview"]
            )
            for note in rag_result.get("context_notes", [])
        ]

        # Store assistant response
        assistant_message = ChatHistory(
            session_id=session_id,
            role="assistant",
            content=rag_result["response"],
            context_note_ids=json.dumps([n.note_id for n in context_notes])
        )
        db.add(assistant_message)
        db.commit()

        return ChatResponse(
            message=rag_result["response"],
            session_id=session_id,
            context_notes=context_notes,
            created_at=assistant_message.created_at
        )

    def get_history(
        self,
        db: Session,
        session_id: str,
        limit: int = 50
    ) -> List[ChatHistory]:
        """Get chat history for a session."""
        return db.query(ChatHistory).filter(
            ChatHistory.session_id == session_id
        ).order_by(ChatHistory.created_at.asc()).limit(limit).all()
