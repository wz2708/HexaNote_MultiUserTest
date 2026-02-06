"""
Note model for storing markdown notes with version control.
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, Index
from sqlalchemy.sql import func
from database import Base
import uuid


class Note(Base):
    """Note model with markdown content and versioning."""

    __tablename__ = "notes"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Content fields
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)  # Markdown content
    tags = Column(Text, default="[]")  # JSON array stored as text

    # Version control for conflict resolution
    version = Column(Integer, default=1, nullable=False)

    # Weaviate reference
    weaviate_uuid = Column(String(36), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete

    # Indexes for performance
    __table_args__ = (
        Index('idx_notes_updated_at', 'updated_at'),
        Index('idx_notes_deleted_at', 'deleted_at'),
    )

    def __repr__(self):
        return f"<Note(id={self.id}, title='{self.title}', version={self.version})>"
