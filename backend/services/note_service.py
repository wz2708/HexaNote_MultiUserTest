"""
Note service for CRUD operations with version control and Weaviate sync.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from models.note import Note
from schemas.note_schema import NoteCreate, NoteUpdate, NotePartialUpdate
from services.weaviate_service import WeaviateService


class NoteService:
    """Service for note CRUD operations."""

    def __init__(self, weaviate_service: WeaviateService):
        self.weaviate = weaviate_service

    def create_note(self, db: Session, note_data: NoteCreate) -> Note:
        """Create a new note in both SQLite and Weaviate."""
        # Create SQLite entry
        note = Note(
            title=note_data.title,
            content=note_data.content,
            tags=json.dumps(note_data.tags),
            version=1
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        # Index in Weaviate
        weaviate_uuid = self.weaviate.index_note(
            note_id=note.id,
            title=note.title,
            content=note.content,
            tags=note_data.tags,
            created_at=note.created_at.isoformat(),
            updated_at=note.updated_at.isoformat()
        )

        # Update with Weaviate UUID
        if weaviate_uuid:
            note.weaviate_uuid = weaviate_uuid
            db.commit()
            db.refresh(note)

        return note

    def get_note(self, db: Session, note_id: str) -> Optional[Note]:
        """Get a note by ID (excluding soft-deleted)."""
        return db.query(Note).filter(
            Note.id == note_id,
            Note.deleted_at.is_(None)
        ).first()

    def list_notes(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        tags: Optional[List[str]] = None
    ) -> tuple[List[Note], int]:
        """List notes with pagination and optional tag filter."""
        query = db.query(Note).filter(Note.deleted_at.is_(None))

        # Filter by tags if provided
        if tags:
            for tag in tags:
                query = query.filter(Note.tags.contains(f'"{tag}"'))

        total = query.count()
        notes = query.order_by(Note.updated_at.desc()).offset(skip).limit(limit).all()

        return notes, total

    def update_note(
        self,
        db: Session,
        note_id: str,
        note_data: NoteUpdate
    ) -> Optional[Note]:
        """Update a note with version conflict detection."""
        note = self.get_note(db, note_id)
        if not note:
            return None

        # Version conflict check
        if note.version != note_data.version:
            raise ValueError(f"Version conflict: expected {note.version}, got {note_data.version}")

        # Update note
        note.title = note_data.title
        note.content = note_data.content
        note.tags = json.dumps(note_data.tags)
        note.version += 1
        note.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(note)

        # Update in Weaviate
        self.weaviate.index_note(
            note_id=note.id,
            title=note.title,
            content=note.content,
            tags=note_data.tags,
            created_at=note.created_at.isoformat(),
            updated_at=note.updated_at.isoformat()
        )

        return note

    def delete_note(self, db: Session, note_id: str) -> bool:
        """Soft delete a note."""
        note = self.get_note(db, note_id)
        if not note:
            return False

        # Soft delete in SQLite
        note.deleted_at = datetime.utcnow()
        db.commit()

        # Delete from Weaviate
        self.weaviate.delete_note(note_id)

        return True

    def get_all_tags(self, db: Session) -> List[dict]:
        """Get all unique tags with counts."""
        notes = db.query(Note).filter(Note.deleted_at.is_(None)).all()

        tag_counts = {}
        for note in notes:
            try:
                tags = json.loads(note.tags)
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            except:
                pass

        return [{"tag": tag, "count": count} for tag, count in sorted(tag_counts.items())]
