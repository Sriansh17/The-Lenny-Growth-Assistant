# Setup Requirements for The Lenny Growth Assistant

---

## YOUR TODO — Steps You Must Do Manually

These are things I can't do from the IDE. Run them in order.

### Step 1: Download Transcripts (5 min)
```bash
cd The-Lenny-Growth-Assistant

# This script clones 269 transcripts from ChatPRD/lennys-podcast-transcripts
python scripts/download_transcripts.py

# Or limit to first 30 for faster testing:
python scripts/download_transcripts.py --limit 30
```

### Step 2: Install Frontend Dependencies & Generate Lockfile (2 min)
```bash
cd frontend
npm install
# This creates node_modules/ and package-lock.json (needed for reproducible builds)
cd ..
```

### Step 3: Install Ollama Locally (5 min)
- Download from https://ollama.com/download
- Install and run:
```bash
ollama serve
# In another terminal:
ollama pull llama3.1:8b
```
If your machine struggles with 8B, use `ollama pull mistral:7b` and update `OLLAMA_MODEL=mistral:7b` in `.env`.

### Step 4: Copy .env and Configure (1 min)
```bash
cp .env.example .env
# Edit .env — defaults work for local Ollama demo
# Optional: Add ANTHROPIC_API_KEY for cloud mode with agent tool-use
```

### Step 5: Start Everything with Docker Compose (10-15 min first run)
```bash
docker-compose up --build
```
Wait for all services to be healthy. First run downloads Docker images + Ollama model (~5GB).

### Step 6: Verify It Works
- Frontend: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs
- Health check: `curl http://localhost:8000/api/v1/health`
- Test: Click "New Chat" → Ask "How does Gokul define product-market fit?"

### Step 7: Record Demo Video (30-60 min)
Record a 2-3 minute video (camera on):
1. Explain the problem briefly
2. Show the chat UI with a grounded answer + citations
3. Demo the Ship 30 for 30 essay skill
4. Show the Artifact Viewer
5. Show Ollama running locally (terminal or model selector)
6. Briefly cover one trade-off (e.g., local model quality vs latency)

Upload to YouTube (unlisted is fine).

### Step 8: Populate Agent Transcripts
Save your Kiro/Claude coding session logs to `agent_transcripts/`:
- Include at least 2-3 sessions
- Include any failed attempts and how you fixed them
- Remove any API keys or secrets before committing

### Step 9: Push to GitHub
```bash
git add -A
git commit -m "feat: complete Lenny Growth Assistant"
git push origin main
```
Make sure the repo is **public** and has no committed secrets.

### Step 10: Submit
Fill the form: https://forms.gle/LgotDHNVxW1mbzNE7
- Due: **28/08/26 EOD**

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10/11, macOS 12+, Linux | Linux/macOS (better Docker performance) |
| **RAM** | 8 GB | 16+ GB (for Ollama + embedding model) |
| **Disk** | 15 GB free | 25+ GB (models + vector DB + Docker images) |
| **CPU** | 4 cores | 8+ cores (faster local inference) |
| **GPU** | Optional | NVIDIA GPU with 8GB+ VRAM (for faster Ollama) |

## Required Software

### 1. Python 3.10+ (Required for scripts)
- For running `download_transcripts.py` and local development
- Verify: `python --version`

### 2. Docker & Docker Compose (Required)
- **Docker Desktop** (Windows/macOS) or **Docker Engine + Compose** (Linux)
- Version: Docker 24+, Compose 2.20+
- Verify: `docker --version` && `docker compose version`

### 3. Node.js 18+ (Required for frontend)
- Verify: `node --version` && `npm --version`

### 4. Git (Required)
- For cloning the repository and transcripts
- Verify: `git --version`

---

## One-Command Setup (After Prerequisites)

```bash
# 1. Clone repository
git clone <your-repo-url>
cd The-Lenny-Growth-Assistant

# 2. Download transcripts (269 episodes from Lenny's Podcast)
python scripts/download_transcripts.py

# 3. Install frontend deps (generates package-lock.json)
cd frontend && npm install && cd ..

# 4. Copy environment template
cp .env.example .env

# 5. Start everything
docker-compose up --build
```

**First run takes 10-15 minutes** (downloads Docker images, pulls Ollama model ~5GB).

**Access points:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Ollama: http://localhost:11434

---

## Manual Setup (Without Docker)

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (required)
# Option A: Docker only for DB
docker run -d --name postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=lenny_assistant \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Option B: Local PostgreSQL + pgvector extension
# CREATE EXTENSION vector;

# Start Ollama (required for local LLM)
# Install from https://ollama.com/download
ollama serve
# In another terminal:
ollama pull llama3.1:8b

# Run migrations
alembic upgrade head

# Ingest transcripts (after running download_transcripts.py)
python -c "from app.services.ingestion import ingestion_service; print(ingestion_service.ingest_all())"

# Start backend
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## Transcript Setup (Required for RAG)

### Automated Download (Recommended)
```bash
# Downloads all 269 transcripts from github.com/ChatPRD/lennys-podcast-transcripts
python scripts/download_transcripts.py

# Or limit for faster testing:
python scripts/download_transcripts.py --limit 20
```

The script:
1. Clones the ChatPRD transcript repository
2. Parses markdown files with YAML frontmatter
3. Converts to JSON format in `data/transcripts/`
4. Skips already-converted files (idempotent)

### JSON Format
Each transcript is stored as:
```json
{
  "title": "Episode 45: Fareed Mosavat on Growth Loops",
  "url": "https://youtube.com/watch?v=...",
  "date": "2023-06-15",
  "speaker": "Fareed Mosavat",
  "content": "Full transcript text here..."
}
```

### Sample Files Included
The repo includes 3 sample transcripts for immediate testing:
- `data/transcripts/episode-1-lenny-gokul.json`
- `data/transcripts/episode-2-lenny-fareed.json`
- `data/transcripts/episode-3-lenny-rachel.json`

### Re-ingesting After Adding Transcripts
```bash
# Docker:
docker-compose restart backend
# (auto-ingests on startup if vector DB is empty)

# Manual:
cd backend && python scripts/ingest_transcripts.py
```

---

## Cloud LLM Setup (Optional — enables Anthropic Agent)

When using Anthropic as the LLM provider, the system activates the **Anthropic Agent Layer** with tool-use:
- The agent autonomously decides whether to search transcripts, generate essays, or create artifacts
- This is the recommended experience for evaluators with an API key

### 1. Get API Keys
- **Anthropic**: https://console.anthropic.com/
- **OpenAI**: https://platform.openai.com/api-keys

### 2. Update .env
```bash
# .env
LLM_PROVIDER=anthropic  # or openai
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENAI_API_KEY=sk-...
```

### 3. Restart Backend
```bash
docker-compose restart backend
```

### Agent Behavior by Provider
| Provider | Behavior |
|----------|----------|
| `ollama` | Manual RAG + skill routing (keyword triggers) |
| `anthropic` | Anthropic Agent with tool-use (autonomous routing) |
| `openai` | Manual RAG + skill routing (same as ollama) |

---

## Configuration Reference (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama`, `anthropic`, `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server |
| `OLLAMA_MODEL` | `llama3.1:8b` | Model name |
| `ANTHROPIC_API_KEY` | - | Required for Anthropic agent mode |
| `OPENAI_API_KEY` | - | Required for OpenAI |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `VECTOR_DB_PATH` | `./data/chroma` | ChromaDB persistence |
| `CHUNK_SIZE` | `1000` | RAG chunk tokens |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_RETRIEVAL` | `5` | Chunks per query |
| `SIMILARITY_THRESHOLD` | `0.7` | Min cosine similarity |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `console` | `console` or `json` |

---

## Verification Checklist

After setup, verify each component:

### ✅ Database
```bash
# Check PostgreSQL
docker exec -it lenny_postgres psql -U postgres -d lenny_assistant -c "\dt"
# Should show: sessions, messages, artifacts, alembic_version
```

### ✅ Vector Database
```bash
curl http://localhost:8000/api/v1/health
# Should show: "database": "connected", "status": "healthy"
```

### ✅ Ollama
```bash
curl http://localhost:11434/api/tags
# Should show llama3.1:8b in models list
```

### ✅ Backend API
```bash
curl http://localhost:8000/api/v1/health
# Returns: { status, version, database, llm_provider, llm_model }

curl http://localhost:8000/api/v1/skills
# Returns: list of available skills (ship30, artifact)
```

### ✅ Frontend
- Open http://localhost:5173
- Should see "Lenny Growth Assistant" with sidebar
- Header shows model provider + model name + green status dot
- Click "New Chat" → type a question → get streamed response with citations

### ✅ End-to-End Test
1. Click "New Chat"
2. Ask: "How does Gokul define product-market fit?"
3. Should get streaming response with "Sources" citations
4. Ask: "Write a Ship 30 for 30 essay about growth strategies"
5. Should generate ~1250 word essay with artifact viewer

---

## Troubleshooting Common Issues

### Port Conflicts
```bash
# Linux/macOS:
netstat -tulpn | grep -E '5173|8000|5432|11434'

# Windows (PowerShell):
netstat -an | Select-String "5173|8000|5432|11434"

# Kill or change ports in docker-compose.yml
```

### Ollama Model Not Downloading
```bash
# Manual pull inside container
docker exec -it lenny_ollama ollama pull llama3.1:8b

# Or use smaller model in .env:
OLLAMA_MODEL=mistral:7b
```

### Out of Memory
```bash
# Increase Docker memory: Docker Desktop > Resources > Memory > 8GB+
# Or use smaller model:
OLLAMA_MODEL=llama3.1:8b  # instead of 70b
```

### GPU Acceleration (Optional)
If you have an NVIDIA GPU and want faster Ollama inference:
1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Uncomment the `deploy` block in `docker-compose.yml` under the `ollama` service
3. Restart: `docker-compose up -d --build`

### Transcripts Not Loading
```bash
# Verify files exist
# Linux/macOS:
ls data/transcripts/ | wc -l
# Windows (PowerShell):
(Get-ChildItem data\transcripts\*.json).Count

# Re-download:
python scripts/download_transcripts.py --skip-download

# Re-ingest:
docker-compose restart backend
```

### Frontend Can't Connect to Backend
- Check `docker-compose ps` — all services should be `healthy`
- Check browser console (F12) for CORS errors
- Verify Vite proxy in `frontend/vite.config.ts` points to backend
- Try direct: `curl http://localhost:8000/api/v1/health`

### Alembic Migration Fails
```bash
# If tables already exist (from init_db), mark migration as done:
docker exec -it lenny_backend alembic stamp head

# Or fresh start:
docker-compose down -v
docker-compose up --build
```

---

## Production Deployment Notes

For production deployment (beyond this assignment):

| Component | Local | Production |
|-----------|-------|------------|
| PostgreSQL | Docker | Supabase / Railway / AWS RDS |
| Ollama | Docker | GPU instance / Ollama Cloud |
| ChromaDB | File | Chroma Cloud / Pinecone / Weaviate |
| Frontend | Vite dev | Vercel / Netlify / Cloudflare Pages |
| Backend | Uvicorn | Gunicorn + Uvicorn workers |
| Secrets | .env | Vault / AWS Secrets Manager |

---

## Quick Commands Reference

```bash
# Start all services
docker-compose up --build

# Start in background
docker-compose up -d --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama

# Restart single service
docker-compose restart backend

# Stop all
docker-compose down

# Stop + remove volumes (complete fresh start)
docker-compose down -v

# Run backend tests
cd backend && pytest -v

# Download transcripts
python scripts/download_transcripts.py

# Run ingestion manually
cd backend && python scripts/ingest_transcripts.py

# Pull different Ollama model
docker exec -it lenny_ollama ollama pull mistral:7b
```

---

## Project Structure

```
The-Lenny-Growth-Assistant/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── agents/          # Anthropic agent with tool-use
│   │   ├── api/v1/          # REST endpoints (sessions, chat, health)
│   │   ├── core/            # Config, middleware, resilience
│   │   ├── db/              # SQLAlchemy async setup
│   │   ├── models/          # ORM models (Session, Message, Artifact)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Agent, LLM, RAG, ingestion, sanitizer
│   │   └── skills/          # Ship 30 for 30, Artifact generation
│   ├── alembic/             # Database migrations
│   ├── tests/               # Automated tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/      # UI components (Chat, Sidebar, ArtifactViewer)
│   │   ├── hooks/           # Zustand store
│   │   ├── types/           # TypeScript interfaces
│   │   └── utils/           # API client
│   ├── Dockerfile
│   └── package.json
├── data/
│   └── transcripts/         # JSON transcript files
├── scripts/                  # Download + ingestion scripts
├── docs/                     # PRD, architecture, design documents
├── tests/                    # Manual test plan
├── agent_transcripts/        # AI coding session logs
├── docker-compose.yml
├── .env.example
└── README.md
```
