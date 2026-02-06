"""
SyncState model for tracking synchronization status per device.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from database import Base
import uuid


class SyncState(Base):
    """Track sync status for each note-device combination."""

    __tablename__ = "sync_states"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign keys
    note_id = Column(String(36), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(String(100), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)

    # Sync tracking
    last_synced_version = Column(Integer, default=0, nullable=False)
    last_sync_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Timestamps
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_sync_note_device', 'note_id', 'device_id', unique=True),
        Index('idx_sync_device', 'device_id'),
    )

    def __repr__(self):
        return f"<SyncState(note_id={self.note_id}, device_id={self.device_id}, version={self.last_synced_version})>"
