"""
Migration script to upgrade to chunking-enabled schema.
Run this after updating weaviate_service.py to enable chunking support.

This script will:
1. Delete the old Note collection
2. Recreate it with chunking support
3. Reindex all notes with automatic chunking
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.weaviate_service import WeaviateService
from database import SessionLocal
from models.note import Note
import json


def migrate():
    """Migrate to chunking-enabled schema."""
    print("🔄 Starting migration to chunking-enabled schema...")

    # Initialize services
    weaviate = WeaviateService()
    db = SessionLocal()

    try:
        # Step 1: Delete old collection
        print("\n📦 Step 1: Deleting old collection...")
        try:
            note_collection = weaviate.client.collections.get("Note")
            note_collection.delete()
            print("✓ Old collection deleted")
        except Exception as e:
            print(f"⚠️  Collection might not exist: {e}")

        # Step 2: Create new collection with chunking support
        print("\n📦 Step 2: Creating new collection with chunking support...")
        weaviate.ensure_collection()
        print("✓ New collection created")

        # Step 3: Reindex all notes
        print("\n📦 Step 3: Reindexing all notes with chunking...")
        notes = db.query(Note).filter(Note.deleted_at == None).all()
        total = len(notes)

        print(f"Found {total} notes to reindex")

        success_count = 0
        error_count = 0

        for i, note in enumerate(notes, 1):
            try:
                tags = json.loads(note.tags) if note.tags else []
                uuid = weaviate.index_note(
                    note_id=note.id,
                    title=note.title,
                    content=note.content,
                    tags=tags,
                    created_at=note.created_at.isoformat() if note.created_at else "",
                    updated_at=note.updated_at.isoformat() if note.updated_at else ""
                )
                if uuid:
                    note.weaviate_uuid = uuid
                    success_count += 1
                    print(f"  [{i}/{total}] ✓ {note.title}")
                else:
                    error_count += 1
                    print(f"  [{i}/{total}] ✗ {note.title} - Failed to index")
            except Exception as e:
                error_count += 1
                print(f"  [{i}/{total}] ✗ {note.title} - Error: {e}")

        db.commit()

        # Summary
        print(f"\n{'='*60}")
        print(f"✅ Migration complete!")
        print(f"   Total notes: {total}")
        print(f"   Successfully indexed: {success_count}")
        print(f"   Errors: {error_count}")
        print(f"{'='*60}\n")

        if error_count > 0:
            print("⚠️  Some notes failed to index. Check the errors above.")
        else:
            print("🎉 All notes indexed successfully with chunking support!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        db.close()
        weaviate.close()


if __name__ == "__main__":
    migrate()
