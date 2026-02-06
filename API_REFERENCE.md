# HexaNote Backend API Reference

## Base URL
```
http://localhost:8001/api/v1
```

## Authentication

### Getting Your Password

The default password is **`hexanote`**. You can customize this by setting the `SIMPLE_PASSWORD` environment variable in your `.env` file or `docker-compose.yml`.

**Location in code:**
- Default value: [backend/config.py:40](backend/config.py#L40)
- Environment variable: `SIMPLE_PASSWORD` in [backend/.env.example:32](backend/.env.example#L32)

### Get Access Token

Authenticate and receive a JWT token valid for 7 days (10080 minutes).

**Endpoint:** `POST /api/v1/token`

**Request:**
```json
{
  "password": "hexanote"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

**Windows Client Example:**
```typescript
// In windows-client/src/services/api.ts
const api = axios.create({
    baseURL: 'http://localhost:8001/api/v1',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_TOKEN_HERE'
    },
})
```

### Register Device

Register a new device for sync functionality.

**Endpoint:** `POST /api/v1/devices/register`

**Request:**
```json
{
  "device_name": "My Windows PC",
  "device_type": "windows"
}
```

**Response:**
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Device registered successfully"
}
```

### Health Check

Check the status of the API and its dependent services.

**Endpoint:** `GET /api/v1/health`

**Response:**
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

---

## Notes API

### List Notes

Get all notes with pagination and optional tag filtering.

**Endpoint:** `GET /api/v1/notes`

**Query Parameters:**
- `page` (integer, default: 1) - Page number
- `limit` (integer, default: 50, max: 100) - Items per page
- `tags` (string, optional) - Comma-separated tags to filter by

**Windows Client Example:**
```typescript
// windows-client/src/services/api.ts:54-58
const response = await api.get<{ notes: Note[] }>('/notes')
return response.data.notes
```

**Response:**
```json
{
  "notes": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "My First Note",
      "content": "# Welcome to HexaNote\n\nThis is a markdown note.",
      "tags": ["welcome", "tutorial"],
      "version": 1,
      "created_at": "2026-02-06T10:00:00Z",
      "updated_at": "2026-02-06T10:00:00Z",
      "deleted_at": null,
      "weaviate_uuid": "00000000-0000-0000-0000-000000000000"
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 50
}
```

### Get Note by ID

Retrieve a single note.

**Endpoint:** `GET /api/v1/notes/{note_id}`

**Windows Client Example:**
```typescript
// windows-client/src/services/api.ts:60-63
const response = await api.get<Note>(`/notes/${id}`)
return response.data
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "My First Note",
  "content": "# Welcome to HexaNote",
  "tags": ["welcome"],
  "version": 1,
  "created_at": "2026-02-06T10:00:00Z",
  "updated_at": "2026-02-06T10:00:00Z"
}
```

### Create Note

Create a new note.

**Endpoint:** `POST /api/v1/notes`

**Windows Client Example:**
```typescript
// windows-client/src/services/api.ts:65-68
const response = await api.post<Note>('/notes', {
  title: "New Note",
  content: "Note content here",
  tags: ["personal", "ideas"]
})
return response.data
```

**Request:**
```json
{
  "title": "My New Note",
  "content": "# Note Content\n\nSupports **Markdown**!",
  "tags": ["personal", "ideas"]
}
```

**Response:** Same as Get Note (201 Created)

### Update Note

Update an existing note. Requires version number for conflict detection.

**Endpoint:** `PUT /api/v1/notes/{note_id}`

**Windows Client Example:**
```typescript
// windows-client/src/services/api.ts:77-80
const response = await api.put<Note>(`/notes/${id}`, {
  title: "Updated Title",
  content: "Updated content",
  tags: ["updated"],
  version: 1  // Current version for conflict detection
})
```

**Request:**
```json
{
  "title": "Updated Title",
  "content": "Updated content",
  "tags": ["updated"],
  "version": 1
}
```

**Response:** Updated note object

**Note:** If the version doesn't match (someone else updated it), you'll get a 409 Conflict error.

### Delete Note

Soft delete a note (marks as deleted but doesn't remove from database).

**Endpoint:** `DELETE /api/v1/notes/{note_id}`

**Windows Client Example:**
```typescript
// windows-client/src/services/api.ts:82-84
await api.delete(`/notes/${id}`)
```

**Response:** 204 No Content

### List Tags

Get all unique tags with usage counts.

**Endpoint:** `GET /api/v1/notes/tags`

**Response:**
```json
{
  "tags": [
    {
      "tag": "tutorial",
      "count": 12
    },
    {
      "tag": "personal",
      "count": 8
    }
  ]
}
```

---

## Search API

### Semantic Search

Search notes using AI-powered vector similarity (powered by Weaviate).

**Endpoint:** `GET /api/v1/notes/search/semantic`

**Query Parameters:**
- `q` (string, required) - Search query
- `limit` (integer, default: 5, max: 20) - Maximum results
- `tags` (string, optional) - Comma-separated tags filter

**Windows Client Example:**
```typescript
// windows-client/src/services/api.ts:70-75
const response = await api.get<{ results: SemanticSearchResult[] }>(
  '/notes/search/semantic',
  {
    params: { q: "machine learning concepts", limit: 10 }
  }
)
return response.data.results
```

**Response:**
```json
{
  "results": [
    {
      "note_id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Introduction to Neural Networks",
      "content": "Neural networks are...",
      "tags": ["ai", "ml"],
      "created_at": "2026-02-06T10:00:00Z",
      "updated_at": "2026-02-06T10:00:00Z",
      "relevance_score": 0.89
    }
  ],
  "query": "machine learning concepts",
  "count": 1
}
```

### Search Within Note

Search within a specific note and get context around the best match.

**Endpoint:** `GET /api/v1/notes/{note_id}/search`

**Query Parameters:**
- `q` (string, required) - Search query
- `window` (integer, default: 2, max: 5) - Number of chunks before/after best match

**Windows Client Example:**
```typescript
// windows-client/src/services/api.ts:91-102
const response = await api.get<{
  context: string;
  title: string;
  chunk_range: string;
  total_chunks: number;
  best_chunk_index: number;
}>(`/notes/${noteId}/search`, {
  params: { q: "specific paragraph", window: 2 }
})
```

**Response:**
```json
{
  "context": "...previous text...\n\nBest matching paragraph here.\n\n...following text...",
  "title": "Note Title",
  "chunk_range": "3-5",
  "total_chunks": 10,
  "best_chunk_index": 4
}
```

### Reindex Notes

Re-index all notes in Weaviate (useful after bulk changes).

**Endpoint:** `POST /api/v1/notes/reindex`

**Windows Client Example:**
```typescript
// windows-client/src/services/api.ts:86-89
const response = await api.post<{
  message: string;
  total: number;
  success: number;
  errors: number;
}>('/notes/reindex')
```

**Response:**
```json
{
  "message": "Reindexing completed",
  "total": 100,
  "success": 98,
  "errors": 2
}
```

---

## Chat API (RAG)

### Chat Query

Ask questions about your notes using Retrieval-Augmented Generation (RAG).

**Endpoint:** `POST /api/v1/chat/query`

**Windows Client Example:**
```typescript
// windows-client/src/services/api.ts:106-120
const response = await api.post<ChatResponse>('/chat/query', {
  message: "What are my notes about machine learning?",
  session_id: "session-123",  // Optional, for conversation continuity
  limit: 5,
  additional_context: "Focus on practical applications"  // Optional
})
```

**Request:**
```json
{
  "message": "What are my notes about machine learning?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "note_filter": ["ai", "ml"],
  "limit": 5,
  "additional_context": "Focus on practical applications"
}
```

**Response:**
```json
{
  "message": "Based on your notes, you have several entries about machine learning...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "context_notes": [
    {
      "note_id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "ML Basics",
      "content_preview": "Machine learning is a subset of AI...",
      "relevance_score": 0.92
    }
  ],
  "created_at": "2026-02-06T10:30:00Z"
}
```

### Get Chat History

Retrieve conversation history for a session.

**Endpoint:** `GET /api/v1/chat/history`

**Query Parameters:**
- `session_id` (string, required) - Session UUID
- `limit` (integer, default: 50, max: 200) - Maximum messages

**Response:**
```json
{
  "messages": [
    {
      "id": "msg-1",
      "session_id": "session-123",
      "role": "user",
      "content": "What is machine learning?",
      "context_note_ids": [],
      "created_at": "2026-02-06T10:00:00Z"
    },
    {
      "id": "msg-2",
      "session_id": "session-123",
      "role": "assistant",
      "content": "Machine learning is...",
      "context_note_ids": ["note-1", "note-2"],
      "created_at": "2026-02-06T10:00:05Z"
    }
  ],
  "session_id": "session-123",
  "total": 2
}
```

### Create Chat Session

Create a new chat session.

**Endpoint:** `POST /api/v1/chat/sessions`

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Sync API

Used for synchronizing notes between devices.

### Sync Notes

Batch sync notes between client and server.

**Endpoint:** `POST /api/v1/sync`

**Request:**
```json
{
  "device_id": "device-uuid",
  "last_sync_timestamp": "2026-02-06T09:00:00Z",
  "notes": [
    {
      "id": "note-uuid",
      "version": 2,
      "action": "update",
      "data": {
        "title": "Updated Note",
        "content": "New content",
        "tags": ["updated"]
      }
    },
    {
      "id": "note-uuid-2",
      "version": 1,
      "action": "delete",
      "data": null
    }
  ]
}
```

**Response:**
```json
{
  "notes_to_update": [
    {
      "id": "note-from-server",
      "title": "Server Note",
      "content": "Content",
      "tags": [],
      "version": 3,
      "created_at": "2026-02-06T08:00:00Z",
      "updated_at": "2026-02-06T10:00:00Z"
    }
  ],
  "notes_to_delete": ["deleted-note-id"],
  "conflicts": [
    {
      "note_id": "conflict-note-id",
      "client_version": 2,
      "server_version": 3,
      "server_note": { /* full note object */ },
      "resolution_strategy": "server_wins"
    }
  ],
  "server_timestamp": "2026-02-06T10:30:00Z"
}
```

---

## Error Responses

All endpoints follow standard HTTP status codes:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid password"
}
```

### 404 Not Found
```json
{
  "detail": "Note not found"
}
```

### 409 Conflict
```json
{
  "detail": "Version conflict - note was modified by another client"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Configuration

### Environment Variables

Key environment variables you can configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `SIMPLE_PASSWORD` | `hexanote` | Authentication password |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `DATABASE_URL` | `sqlite:///./data/hexanote.db` | SQLite database path |
| `WEAVIATE_URL` | `http://weaviate:8080` | Weaviate vector DB URL |
| `OLLAMA_URL` | `http://ollama:11434` | Ollama LLM server URL |
| `OLLAMA_EMBEDDING_MODEL` | `mxbai-embed-large:latest` | Embedding model |
| `OLLAMA_GENERATION_MODEL` | `llama3.2:1b` | Chat model |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` (7 days) | Token expiration |

See [backend/.env.example](backend/.env.example) for full configuration options.

---

## TypeScript Types

For TypeScript/JavaScript clients, here are the main interface definitions from the Windows client:

```typescript
// From windows-client/src/services/api.ts

export interface Note {
    id: string
    title: string
    content: string
    tags: string[]
    version: number
    created_at?: string
    updated_at?: string
}

export interface SemanticSearchResult {
    note_id: string
    title: string
    content: string
    tags: string[]
    created_at?: string
    updated_at?: string
    relevance_score?: number
}

export interface ChatRequest {
    message: string
    session_id?: string
    limit?: number
    additional_context?: string
}

export interface ContextNote {
    note_id: string
    title: string
    content_preview: string
    relevance_score?: number
}

export interface ChatResponse {
    message: string
    session_id: string
    context_notes: ContextNote[]
    created_at: string
}
```

---

## Quick Start Example

Here's a complete example of authenticating and creating a note:

```bash
# 1. Get access token
curl -X POST http://localhost:8001/api/v1/token \
  -H "Content-Type: application/json" \
  -d '{"password": "hexanote"}'

# Response: {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 604800}

# 2. Create a note (use the token from step 1)
curl -X POST http://localhost:8001/api/v1/notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{
    "title": "My First Note",
    "content": "# Hello World\n\nThis is my first note!",
    "tags": ["welcome"]
  }'

# 3. Search notes
curl -X GET "http://localhost:8001/api/v1/notes/search/semantic?q=hello&limit=5" \
  -H "Authorization: Bearer eyJ..."
```

---

## OpenAPI/Swagger Documentation

The API also provides interactive documentation at:
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **OpenAPI JSON:** http://localhost:8001/openapi.json

---

## Need Help?

- Check the [main README](README.md) for setup instructions
- Review the Windows client code in [windows-client/src/services/api.ts](windows-client/src/services/api.ts) for working examples
- View backend implementation in [backend/routers/](backend/routers/)
