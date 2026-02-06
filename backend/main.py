"""
HexaNote FastAPI Backend Application.
Main entry point for the API server.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from database import init_db
from services.weaviate_service import get_weaviate_service
from routers import notes, chat, sync, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print("Starting HexaNote backend...")

    # Initialize database
    init_db()
    print("Database initialized")

    # Initialize Weaviate and ensure Note collection exists
    weaviate = get_weaviate_service()
    weaviate.ensure_collection()
    print("Weaviate collection ensured")

    yield

    # Shutdown
    print("Shutting down HexaNote backend...")
    weaviate.close()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Cross-platform notebook app with local RAG",
    lifespan=lifespan
)

# Configure CORS for local network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(notes.router, prefix="/api/v1/notes", tags=["Notes"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["Sync"])

# WebSocket is already in sync router, no need to add separately


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
