"""
Pydantic schemas for Note API requests and responses.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class NoteBase(BaseModel):
    """Base note schema with common fields."""
    title: str = Field(..., min_length=1, max_length=500, description="Note title")
    content: str = Field(..., description="Markdown content")
    tags: List[str] = Field(default_factory=list, description="List of tags")


class NoteCreate(NoteBase):
    """Schema for creating a new note."""
    pass


class NoteUpdate(NoteBase):
    """Schema for updating an existing note."""
    version: int = Field(..., description="Current version for conflict detection")


class NotePartialUpdate(BaseModel):
    """Schema for partial note updates (optional fields)."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    version: int = Field(..., description="Current version for conflict detection")


class NoteResponse(NoteBase):
    """Schema for note responses."""
    id: str = Field(..., description="Note UUID")
    version: int = Field(..., description="Current version number")
    weaviate_uuid: Optional[str] = Field(None, description="Weaviate vector UUID")
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NoteListResponse(BaseModel):
    """Schema for paginated note list responses."""
    notes: List[NoteResponse]
    total: int = Field(..., description="Total number of notes")
    page: int = Field(default=1, description="Current page number")
    limit: int = Field(default=50, description="Items per page")


class TagCount(BaseModel):
    """Schema for tag count response."""
    tag: str
    count: int


class TagListResponse(BaseModel):
    """Schema for tag list responses."""
    tags: List[TagCount]


class SemanticSearchResult(BaseModel):
    """Schema for individual semantic search result from Weaviate."""
    note_id: str = Field(..., description="Note UUID")
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    relevance_score: Optional[float] = Field(None, description="Similarity score")


class SemanticSearchResponse(BaseModel):
    """Schema for semantic search response."""
    results: List[SemanticSearchResult]
    query: str
    count: int
