"""
Script to re-index all notes from SQLite into Weaviate.
Run this once to sync all existing notes into the vector database.

Usage:
    docker exec -it hexanote-backend python reindex_notes.py
    
Or from outside Docker:
    cd backend
    python reindex_notes.py
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from models.note import Note
from services.weaviate_service import WeaviateService
import json


def main():
    print("=" * 60)
    print("HexaNote: Re-index All Notes to Weaviate")
    print("=" * 60)
    
    # Connect to SQLite
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Connect to Weaviate
    print("\n1. Connecting to Weaviate...")
    weaviate = WeaviateService()
    
    if not weaviate.is_ready():
        print("❌ Weaviate is not ready. Make sure Docker services are running.")
        return
    
    print("✓ Weaviate connected")
    
    # Ensure collection exists
    print("\n2. Ensuring Note collection exists...")
    weaviate.ensure_collection()
    
    # Get all notes from SQLite
    print("\n3. Fetching notes from SQLite...")
    notes = db.query(Note).filter(Note.deleted_at == None).all()
    print(f"   Found {len(notes)} notes in SQLite")
    
    # Index each note
    print("\n4. Indexing notes to Weaviate...")
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
                # Update note with Weaviate UUID
                note.weaviate_uuid = uuid
                success_count += 1
                print(f"   [{i}/{len(notes)}] ✓ {note.title[:40]}")
            else:
                error_count += 1
                print(f"   [{i}/{len(notes)}] ❌ Failed: {note.title[:40]}")
                
        except Exception as e:
            error_count += 1
            print(f"   [{i}/{len(notes)}] ❌ Error: {note.title[:40]} - {e}")
    
    # Commit UUID updates
    db.commit()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total notes:     {len(notes)}")
    print(f"Indexed:         {success_count}")
    print(f"Errors:          {error_count}")
    print("\n✅ Re-indexing complete!")
    print("\nYour RAG chat should now find all notes.")
    
    # Cleanup
    db.close()
    weaviate.close()


if __name__ == "__main__":
    main()
