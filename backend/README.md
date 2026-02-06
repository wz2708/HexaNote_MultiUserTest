# HexaNote Backend API

FastAPI backend for HexaNote cross-platform notebook app with local RAG capabilities.

## Features

- **Notes CRUD** - Create, read, update, delete markdown notes with math support
- **Vector Search** - Semantic search using Weaviate + Ollama embeddings
- **RAG Chat** - AI-powered chat that queries your notes
- **Real-time Sync** - WebSocket-based synchronization between devices
- **Version Control** - Conflict detection and resolution for concurrent edits
- **Single-user Auth** - Simple password-based authentication for local network

## Architecture

```
Backend (FastAPI)
├── SQLite - Note metadata, sync state, chat history
├── Weaviate - Vector embeddings for semantic search
└── Ollama - Local LLM for embeddings and generation
```

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for running migration script)
- Ollama models pulled (see parent README.md)

### 2. Run Migration Script

First time only - migrate from Book to Note collection:

```bash


# From LocalRAG directory
python 5-migrate-to-notes.py
```

### 3. Start Services

```bash
# From LocalRAG directory
docker compose up -d
```

This starts:
- Ollama (port 11434)
- Weaviate (port 8080)
- Backend API (port 8001)


```bash

docker exec -it ollama ollama pull llama3.2:1b
docker exec -it ollama ollama pull mxbai-embed-large

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install weaviate-client>=4.16.0

```

### 4. Verify Health

```bash
curl http://localhost:8001/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "database": true,
    "weaviate": true
  },
  "version": "1.0.0"
}
```

### 5. View API Documentation

Open in browser: http://localhost:8001/docs

## API Endpoints

### Authentication

- `POST /api/v1/auth/token` - Get access token (password: `hexanote`)
- `POST /api/v1/auth/devices/register` - Register a device
- `GET /api/v1/health` - Health check

### Notes

- `GET /api/v1/notes` - List notes (pagination, tag filter)
- `GET /api/v1/notes/{id}` - Get single note
- `POST /api/v1/notes` - Create note
- `PUT /api/v1/notes/{id}` - Update note (version check)
- `DELETE /api/v1/notes/{id}` - Delete note
- `GET /api/v1/notes/tags` - Get all tags with counts

### Chat (RAG)

- `POST /api/v1/chat/query` - Ask question using RAG
- `GET /api/v1/chat/history?session_id={uuid}` - Get chat history
- `POST /api/v1/chat/sessions` - Create new session

### Sync

- `POST /api/v1/sync` - Batch sync notes
- `WS /ws/sync?device_id={id}` - WebSocket for real-time sync

## Example Usage

### Create a Note

```bash
curl -X POST http://localhost:8001/api/v1/notes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Basics",
    "content": "# Python Notes\n\nPython is great for:\n- Data science\n- Web development\n\n## Math\n\n$E = mc^2$",
    "tags": ["python", "programming"]
  }'
```

### Semantic Search

```bash
curl "http://localhost:8001/api/v1/search/semantic?q=python%20programming&limit=5"
```

### RAG Chat Query

```bash
curl -X POST http://localhost:8001/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are my notes about Python?",
    "limit": 3
  }'
```

## Configuration

Configuration is managed via environment variables (see [.env.example](.env.example)):

Key settings:
- `SIMPLE_PASSWORD` - Authentication password (default: `hexanote`)
- `WEAVIATE_URL` - Weaviate endpoint (default: `http://weaviate:8080`)
- `OLLAMA_URL` - Ollama endpoint (default: `http://ollama:11434`)
- `DATABASE_URL` - SQLite database path

## Development

### Run Locally (without Docker)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export WEAVIATE_URL=http://localhost:8080
export OLLAMA_URL=http://localhost:11434
export DATABASE_URL=sqlite:///./hexanote.db

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Database Schema

See [database.py](database.py) and models in [models/](models/):
- `notes` - Note content, version, timestamps
- `devices` - Registered client devices
- `sync_states` - Per-device sync tracking
- `chat_history` - RAG conversation history

## Troubleshooting

### Backend won't start

- Check Docker logs: `docker logs hexanote-backend`
- Ensure Weaviate and Ollama are running: `docker ps`
- Verify migration ran: `docker exec -it hexanote-backend python -c "from services.weaviate_service import get_weaviate_service; print(get_weaviate_service().is_ready())"`

### Weaviate connection errors

- Ensure Note collection exists (run migration script)
- Check Weaviate logs: `docker logs weaviate`
- Test connection: `curl http://localhost:8080/v1/.well-known/ready`

### Semantic search returns no results

- Check if notes are indexed in Weaviate
- Ensure Ollama embedding model is pulled: `docker exec -it ollama ollama list`
- Verify model name matches config: `mxbai-embed-large:latest`

## Next Steps

- **Phase 2**: Build Windows desktop client (Electron + React)
- **Phase 3**: Build Android mobile client (Kotlin + Compose)
- See main [implementation plan](../README.md) for details

## License

Part of the HexaNote project.
