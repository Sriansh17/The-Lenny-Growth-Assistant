# The Lenny Growth Assistant

> An AI-powered conversational assistant grounded in Lenny's Podcast transcripts. Built for product managers, growth leaders, and startup founders who want instant, cited answers and generated artifacts from 200+ episodes of product wisdom.

See [Architecture Diagram](docs/architecture.md) for the full system overview.

## Features

- 💬 **Grounded Chat** - Answers cite specific episodes, speakers, and quotes
- 📝 **Ship 30 for 30 Essays** - Generate ~1,250 word essays with hooks, narrative, and takeaways
- 🎨 **Artifact Viewer** - Render Markdown/HTML side-by-side with chat (Claude Artifacts style)
- 🔒 **Secure by Default** - HTML sanitization, iframe sandboxing, CSP headers
- 🤖 **Flexible LLM** - Local (Ollama) or Cloud (Anthropic/OpenAI) with one-click toggle
- 💾 **Persistent Sessions** - PostgreSQL storage with full conversation history
- 🐳 **One-Command Start** - `docker-compose up --build`

## Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM (for Ollama + embedding model)
- 10GB disk space (models + vector DB)

### 1. Clone & Configure
```bash
git clone <your-repo>
cd The-Lenny-Growth-Assistant

# Copy environment template
cp .env.example .env

# Edit .env if needed (optional for local demo)
# Add ANTHROPIC_API_KEY or OPENAI_API_KEY to enable cloud models
```

### 2. Add Transcripts (Required)
Place Lenny's Podcast transcript JSON files in `data/transcripts/`:
```bash
mkdir -p data/transcripts
# Add your transcript files here, e.g.:
# data/transcripts/episode-45-lenny-fareed.json
# data/transcripts/episode-12-lenny-gokul.json
```

**Transcript Format:**
```json
{
  "title": "Episode 45: Fareed Mosavat on Growth",
  "url": "https://www.lennyspodcast.com/episode-45",
  "date": "2023-06-15",
  "speaker": "Fareed Mosavat",
  "content": "Full transcript text here..."
}
```

### 3. Start Everything
```bash
docker-compose up --build
```

**First run** pulls images and downloads the Llama 3.1 8B model (~5GB). Allow 5-10 minutes.

### 4. Access the App
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434

---

## Usage Guide

### Starting a Chat
1. Open http://localhost:5173
2. Click "New Chat" or type in the input box
3. Ask: *"How does Lenny define product-market fit?"*
4. View answer with **Sources** citations

### Generating a Ship 30 Essay
```
Write a Ship 30 for 30 essay on user activation strategies
```
- Auto-detects skill trigger
- Produces ~1,250 word essay with headings, bullets, bold emphasis
- Opens in Artifact Viewer

### Creating an Artifact
```
Create a growth experiment template in HTML
```
- Generates styled HTML/CSS
- Renders in sandboxed iframe
- Toggle **Render** / **Source** views

### Switching Models
1. Open sidebar (☰ on mobile)
2. Select **Provider**: Ollama / Anthropic / OpenAI
3. Select **Model** from dropdown
4. New session uses selected model

---

## Project Structure

```
The-Lenny-Growth-Assistant/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/v1/         # REST endpoints
│   │   ├── core/           # Config, settings
│   │   ├── db/             # SQLAlchemy models, session
│   │   ├── models/         # DB models (Session, Message, Artifact)
│   │   ├── schemas/        # Pydantic request/response
│   │   ├── services/       # Business logic
│   │   │   ├── agent.py    # Conversation orchestration
│   │   │   ├── llm.py      # Provider abstraction
│   │   │   ├── embeddings.py # ChromaDB + sentence-transformers
│   │   │   ├── rag.py      # Retrieval & formatting
│   │   │   ├── ingestion.py # Transcript loading
│   │   │   └── sanitizer.py # HTML security
│   │   └── skills/         # Skill system
│   │       ├── base.py     # BaseSkill, SkillRegistry
│   │       ├── ship30.py   # Ship 30 for 30 essays
│   │       └── artifact.py # Markdown/HTML generation
│   ├── tests/              # Pytest suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── hooks/          # Zustand store
│   │   ├── types/          # TypeScript interfaces
│   │   └── utils/          # API client
│   ├── Dockerfile
│   └── package.json
├── data/
│   └── transcripts/        # Place JSON transcripts here
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   └── design.md
├── agent_transcripts/      # Coding agent logs
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Configuration

### Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama`, `anthropic`, or `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1:8b` | Model name (must be pulled) |
| `ANTHROPIC_API_KEY` | - | Required for Anthropic |
| `OPENAI_API_KEY` | - | Required for OpenAI |
| `CLOUD_MODEL` | `claude-3-5-sonnet-20241022` | Cloud model identifier |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/lenny_assistant` | PostgreSQL connection |
| `VECTOR_DB_PATH` | `./data/chroma` | ChromaDB persistence path |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `CHUNK_SIZE` | `1000` | RAG chunk tokens |
| `TOP_K_RETRIEVAL` | `5` | Chunks per query |
| `SIMILARITY_THRESHOLD` | `0.7` | Min cosine similarity |

### Adding Cloud Models
```bash
# .env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
# or
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

---

## Development

### Backend Only
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start PostgreSQL & Ollama separately, or use docker-compose for deps only
docker-compose up -d postgres ollama

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Only
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
pytest -v --cov=app

# Frontend tests (when added)
cd frontend
npm test
```

### Ingesting Transcripts Manually
```bash
cd backend
python -c "
from app.services.ingestion import ingestion_service
result = ingestion_service.ingest_all()
print(result)
"
```

### Refreshing Vector DB
```bash
cd backend
python -c "
from app.services.ingestion import ingestion_service
result = ingestion_service.refresh()
print(result)
"
```

---

## Troubleshooting

### Ollama Not Starting
```bash
# Check logs
docker-compose logs ollama

# Common: No GPU memory
# Solution: Use CPU-only model or smaller model
# In .env: OLLAMA_MODEL=llama3.1:8b (or mistral:7b)
```

### Database Connection Failed
```bash
# Check PostgreSQL health
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up --build
```

### Frontend Can't Connect to Backend
- Check `docker-compose ps` - all services should be `healthy`
- Verify backend port 8000 accessible
- Check browser console for CORS errors

### Transcripts Not Loading
- Ensure JSON files in `data/transcripts/`
- Check format matches schema (title, url, date, speaker, content)
- Restart backend to re-ingest: `docker-compose restart backend`

### Out of Memory
- Reduce `OLLAMA_MODEL` to `llama3.1:8b` or `mistral:7b`
- Increase Docker memory limit (Docker Desktop → Resources → Memory)

---

## Extending the System

### Adding a New Skill
1. Create `backend/app/skills/my_skill.py`:
```python
from app.skills.base import BaseSkill, SkillRegistry, SkillResult

class MySkill(BaseSkill):
    name = "my_skill"
    description = "What this skill does"
    trigger_keywords = ["trigger", "words"]
    
    def get_system_prompt(self) -> str:
        return "System prompt..."
    
    def get_user_prompt_template(self) -> str:
        return "User prompt with {query} and {context}"

SkillRegistry.register(MySkill())
```

2. Import in `backend/app/skills/__init__.py`:
```python
from .my_skill import MySkill
```

### Adding a New LLM Provider
1. Implement `BaseLLMProvider` in `app/services/llm.py`
2. Add to `get_llm_provider()` factory
3. Add config to `app/core/config.py`

### Using a Different Vector DB
1. Implement `EmbeddingService` interface in `app/services/embeddings.py`
2. Update `RAGService` to use new service
3. Add config for connection details

---

## Demo Video Script

**2-3 minutes covering:**
1. **Problem** (15s): PMs waste hours searching Lenny's content
2. **Product Tour** (60s): Chat → citations → follow-up
3. **Ship 30 Skill** (30s): Generate essay → artifact viewer
4. **Artifact Skill** (30s): Create HTML template → render/source
5. **Local Model** (15s): Sidebar shows Ollama, no API keys needed
6. **Trade-off** (30s): Local vs cloud quality/latency/privacy

---

## License

MIT License - see LICENSE file for details.

---

## Acknowledgments

- Lenny Rachitsky for the incredible podcast content
- Anthropic, Ollama, and open-source community
- FastAPI, React, TailwindCSS, ChromaDB, pgvector teams