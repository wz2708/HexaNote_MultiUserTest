"""
Notes API router for CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from database import get_db
from models.note import Note
from services.weaviate_service import get_weaviate_service, WeaviateService
from services.note_service import NoteService
from schemas.note_schema import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
    TagListResponse,
    SemanticSearchResponse,
)

router = APIRouter()


def note_to_response(note) -> NoteResponse:
    """Convert Note model to NoteResponse with proper type conversion."""
    return NoteResponse(
        id=note.id,
        title=note.title,
        content=note.content,
        tags=json.loads(note.tags) if note.tags else [],
        version=note.version,
        weaviate_uuid=note.weaviate_uuid,
        created_at=note.created_at,
        updated_at=note.updated_at,
        deleted_at=note.deleted_at
    )


def get_note_service(weaviate: WeaviateService = Depends(get_weaviate_service)) -> NoteService:
    """Dependency for NoteService."""
    return NoteService(weaviate)


@router.get("", response_model=NoteListResponse)
def list_notes(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    db: Session = Depends(get_db),
    note_service: NoteService = Depends(get_note_service)
):
    """List all notes with pagination and optional tag filter."""
    tag_list = tags.split(",") if tags else None
    skip = (page - 1) * limit

    notes, total = note_service.list_notes(db, skip=skip, limit=limit, tags=tag_list)

    return NoteListResponse(
        notes=[note_to_response(note) for note in notes],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/tags", response_model=TagListResponse)
def list_tags(
    db: Session = Depends(get_db),
    note_service: NoteService = Depends(get_note_service)
):
    """Get all unique tags with counts."""
    tags = note_service.get_all_tags(db)
    return TagListResponse(tags=tags)


@router.get("/search/semantic", response_model=SemanticSearchResponse)
def semantic_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Maximum results"),
    tags: Optional[str] = Query(None, description="Comma-separated tags filter"),
    note_service: NoteService = Depends(get_note_service)
):
    """Semantic search using Weaviate vector similarity."""
    tag_list = tags.split(",") if tags else None
    results = note_service.weaviate.semantic_search(
        query=q,
        limit=limit,
        tag_filter=tag_list
    )
    return {"results": results, "query": q, "count": len(results)}


@router.get("/{note_id}/search")
def search_within_note(
    note_id: str,
    q: str = Query(..., description="Search query"),
    window: int = Query(2, ge=1, le=5, description="Number of chunks before/after best match"),
    note_service: NoteService = Depends(get_note_service)
):
    """Search within a specific note and return context window around best match."""
    result = note_service.weaviate.search_within_note(
        note_id=note_id,
        query=q,
        window_chunks=window
    )

    if not result:
        raise HTTPException(status_code=404, detail="Note not found or no matches")

    return result


@router.post("/reindex")
def reindex_notes(
    db: Session = Depends(get_db),
    note_service: NoteService = Depends(get_note_service)
):
    """Re-index all notes from SQLite to Weaviate. Clears existing collection to avoid duplicates."""
    import json as json_lib

    # Delete and recreate collection to clear any duplicates
    try:
        print("🗑️  Deleting existing 'Note' collection to clear duplicates...")
        note_service.weaviate.client.collections.delete("Note")
        print("✓ Collection deleted")

        # Small delay to ensure deletion is complete
        import time
        time.sleep(0.5)

        # Directly create the collection (don't use ensure_collection which checks if exists)
        print("🔧 Creating fresh 'Note' collection with vectorizer config...")
        import weaviate.classes.config as wc
        import weaviate.classes as wvc
        from config import settings

        note_service.weaviate.client.collections.create(
            name="Note",
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_ollama(
                api_endpoint=settings.ollama_url,
                model=settings.ollama_embedding_model,
            ),
            generative_config=wvc.config.Configure.Generative.ollama(
                api_endpoint=settings.ollama_url,
                model=settings.ollama_generation_model,
            ),
            properties=[
                wc.Property(name="note_id", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="title", data_type=wc.DataType.TEXT),
                wc.Property(name="content", data_type=wc.DataType.TEXT),
                wc.Property(name="chunk_index", data_type=wc.DataType.INT, skip_vectorization=True),
                wc.Property(name="total_chunks", data_type=wc.DataType.INT, skip_vectorization=True),
                wc.Property(name="tags", data_type=wc.DataType.TEXT),
                wc.Property(name="created_at", data_type=wc.DataType.TEXT, skip_vectorization=True),
                wc.Property(name="updated_at", data_type=wc.DataType.TEXT, skip_vectorization=True),
            ],
        )
        print("✓ Collection created with vectorizer")
    except Exception as e:
        print(f"Error recreating collection: {e}")
        # Fallback to ensure_collection if direct creation fails
        note_service.weaviate.ensure_collection()
    
    # Get all notes from DB
    notes = db.query(Note).filter(
        Note.deleted_at == None
    ).all()
    
    success_count = 0
    error_count = 0
    
    for note in notes:
        try:
            tags = json_lib.loads(note.tags) if note.tags else []
            uuid = note_service.weaviate.index_note(
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
            else:
                error_count += 1
        except Exception as e:
            error_count += 1
            print(f"Error indexing note {note.id}: {e}")
    
    db.commit()
    
    return {
        "message": f"Reindexed {success_count} notes successfully",
        "total": len(notes),
        "success": success_count,
        "errors": error_count
    }


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: str,
    db: Session = Depends(get_db),
    note_service: NoteService = Depends(get_note_service)
):
    """Get a single note by ID."""
    note = note_service.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note_to_response(note)


@router.post("", response_model=NoteResponse, status_code=201)
def create_note(
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    note_service: NoteService = Depends(get_note_service)
):
    """Create a new note."""
    note = note_service.create_note(db, note_data)
    return note_to_response(note)


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: str,
    note_data: NoteUpdate,
    db: Session = Depends(get_db),
    note_service: NoteService = Depends(get_note_service)
):
    """Update an existing note."""
    try:
        note = note_service.update_note(db, note_id, note_data)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note_to_response(note)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    note_service: NoteService = Depends(get_note_service)
):
    """Delete a note (soft delete)."""
    success = note_service.delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return None
