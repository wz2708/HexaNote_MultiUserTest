"""
ChatHistory model for storing RAG chat conversations.
"""
from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.sql import func
from database import Base
import uuid


class ChatHistory(Base):
    """Chat message history for RAG conversations."""

    __tablename__ = "chat_history"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Session grouping
    session_id = Column(String(36), nullable=False, index=True)

    # Message data
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)

    # Context tracking (JSON array of note IDs used in RAG)
    context_note_ids = Column(Text, default="[]")

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_chat_session_created', 'session_id', 'created_at'),
    )

    def __repr__(self):
        return f"<ChatHistory(id={self.id}, session={self.session_id}, role='{self.role}')>"
