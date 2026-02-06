# HexaNote 📝

A **privacy-first, AI-powered note-taking app** with semantic search and RAG (Retrieval-Augmented Generation). Everything runs **100% locally** on your machine.

## Features

- ✅ **Semantic Search** - Find notes by meaning, not just keywords
- ✅ **RAG Chat** - Ask questions about your notes, get AI-powered answers
- ✅ **Multi-device Sync** - Sync notes across devices via WebSocket
- ✅ **Local AI** - Powered by Ollama (LLM) and Weaviate (Vector DB)
- ✅ **Privacy First** - All data stays on your machine

---

## Quick Start

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Docker Desktop** | Latest | With WSL2 backend enabled |
| **Node.js** | 18+ | For Windows client |
| **WSL2** | Ubuntu recommended | For running Docker |

---

## 1. Backend Setup (WSL2/Docker)
### Step 0: Configure WSL2

-  Use Mirrored Network Mode for outside availablity 


### Step 1: Clone and Navigate

```bash
# In WSL2 terminal
cd /mnt/c/Users/YOUR_USERNAME/HexaNote


# install dep

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install weaviate-client>=4.16.0

cd backend
pip3 install -r requirements.txt

```

### Step 2: Start Docker Containers, check for the Nvidia GPU config part

```bash
cd ..

docker compose up -d --build backend

docker compose up -d
```

This starts:
- **Ollama** (port 11434) - Local LLM inference
- **Weaviate** (port 8080) - Vector database
- **Backend API** (port 8001) - FastAPI server

### Step 3: Pull AI Models

```bash
# Pull embedding model (for semantic search)
docker exec -it ollama ollama pull mxbai-embed-large

# Pull LLM model (for RAG chat)
docker exec -it ollama ollama pull llama3.2:1b
```

### Step 4: Initialize Database Schema

```bash
python3 5-migrate-to-notes_run-after-docker-compose-up-d.py 
```

### Step 5: Verify Health

```bash
curl http://localhost:8001/api/v1/health
```

Expected response:
```json
{"status": "healthy", "version": "1.0.0"}
```

---

## 2. Windows Client Setup

### Step 1: Navigate to Client Folder

```powershell
# In PowerShell or Command Prompt
cd C:\Users\YOUR_USERNAME\HexaNote\windows-client
```

### Step 2: Install Dependencies

```bash
npm install
```

### Step 3: Run Development Server

```bash
npm run dev
```

### Step 4: Open in Browser

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/notes` | GET | List all notes |
| `/api/v1/notes` | POST | Create a note |
| `/api/v1/notes/{id}` | PUT | Update a note |
| `/api/v1/notes/{id}` | DELETE | Delete a note |
| `/api/v1/notes/search/semantic` | GET | Semantic search |
| `/api/v1/notes/reindex` | POST | Reindex notes in Weaviate |
| `/api/v1/chat/query` | POST | RAG chat query |
| `/api/v1/sync` | POST | Batch sync notes |
| `/api/v1/sync/ws` | WS | Real-time sync |

---

## Troubleshooting

### Semantic Search Returns Poor Results

1. Click **Reindex** button in the Chat tab
2. Wait for "Reindexed successfully" message
3. Try searching again

### RAG Chat Times Out

- CPU inference is slow (~45-60 seconds per query)
- The timeout is set to 5 minutes, just wait
- For faster results, use a smaller model:
  ```bash
  docker exec -it ollama ollama pull qwen2:0.5b
  ```



### "Model not found" Error

Pull the required models:
```bash
docker exec -it ollama ollama pull mxbai-embed-large
docker exec -it ollama ollama pull llama3.2:1b
```

### Container Not Starting

```bash
# Check logs
docker logs hexanote-backend --tail 50
docker logs weaviate --tail 50
docker logs ollama --tail 50

# Restart all containers
docker compose restart
```

---

## Project Structure

```
HexaNote/
├── backend/              # FastAPI backend
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   └── Dockerfile
├── windows-client/       # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   └── services/     # API client
│   └── package.json
├── docker-compose.yml    # Docker orchestration
└── README.md             # This file
```

---

## Development

### Run Backend Locally (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Build Windows Client for Production

```bash
cd windows-client
npm run build
```

---





### 5. Test the API

```bash
# Health check
curl http://localhost:8001/api/v1/health


# Check all the notes
curl http://localhost:8001/api/v1/notes | jq

# Create a note
curl -X POST http://localhost:8001/api/v1/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"My First Note","content":"# Hello\n\nMath: $E=mc^2$","tags":["test"]}'

# Chat with your notes
curl -X POST http://localhost:8001/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"message":"What notes do I have?","limit":5}'


# semantic search API
curl "http://localhost:8001/api/v1/notes/search/semantic?q=python&limit=5"
```




## License

MIT License - Use freely for personal or commercial projects.
