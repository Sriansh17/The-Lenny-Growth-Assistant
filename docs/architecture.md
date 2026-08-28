# Architecture Document: The Lenny Growth Assistant

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Sidebar    │  │ Message List │  │Artifact View │             │
│  │ - Sessions   │  │ - Bubbles    │  │ - Render/    │             │
│  │ - Model Sel  │  │ - Citations  │  │   Source     │             │
│  │ - Skills     │  │ - Streaming  │  │ - Sanitized  │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/JSON (REST)
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Sessions   │  │    Chat      │  │   Skills     │             │
│  │   CRUD API   │  │   Endpoint   │  │   Registry   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│         │                │                │                        │
│         ▼                ▼                ▼                        │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    AGENT SERVICE                            │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────────┐  │  │
│  │  │ Session │  │  RAG    │  │  Skill  │  │   LLM         │  │  │
│  │  │ Manager │──▶│ Service │──▶│ Router  │──▶│ Provider      │  │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └───────────────┘  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│         │                │                │                        │
│         ▼                ▼                ▼                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  PostgreSQL  │  │  ChromaDB    │  │   Sanitizer  │             │
│  │  (Sessions,  │  │  (Vectors,   │  │  (Bleach,    │             │
│  │   Messages,  │  │   Metadata)  │  │   Iframe)    │             │
│  │   Artifacts) │  │              │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌────────────┐  ┌────────────┐  ┌────────────┐
            │  Ollama    │  │ Anthropic  │  │  OpenAI    │
            │  (Local)   │  │  (Cloud)   │  │  (Cloud)   │
            └────────────┘  └────────────┘  └────────────┘
```

---

## 2. Database Schema

### PostgreSQL Tables

```sql
-- Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255),
    user_id VARCHAR(255),
    llm_provider VARCHAR(50) NOT NULL DEFAULT 'ollama',
    llm_model VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    citations TEXT,
    model_used VARCHAR(100),
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Artifacts
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('markdown', 'html')),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    sanitized_content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_messages_session ON messages(session_id, created_at);
CREATE INDEX idx_artifacts_session ON artifacts(session_id);
CREATE INDEX idx_sessions_user ON sessions(user_id);
```

### ChromaDB Collection

```python
Collection: "lenny_transcripts"
Metadata: {"hnsw:space": "cosine"}
Documents: Chunked transcript text
Metadata per chunk:
  - source: episode identifier
  - title: episode title
  - url: source URL
  - date: publication date
  - speaker: host/guest
  - chunk_index: position in episode
  - total_chunks: total chunks for episode
```

---

## 3. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | System health check |
| POST | `/api/v1/sessions` | Create new session |
| GET | `/api/v1/sessions` | List sessions |
| GET | `/api/v1/sessions/{id}` | Get session with messages |
| PATCH | `/api/v1/sessions/{id}` | Update session title |
| DELETE | `/api/v1/sessions/{id}` | Delete session |
| POST | `/api/v1/chat` | Send message, get response |
| GET | `/api/v1/sessions/{id}/artifacts` | List session artifacts |
| GET | `/api/v1/skills` | List available skills |

### Chat Request/Response

```json
// POST /api/v1/chat
{
  "message": "How does Lenny define PMF?",
  "session_id": "uuid-optional",
  "use_skill": "ship30"
}

// Response
{
  "session_id": "uuid",
  "message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "assistant",
    "content": "Based on transcripts... [1][2]",
    "citations": "[1] Episode 45 - Lenny & Fareed...\n[2] Episode 12 - Lenny & Gokul...",
    "model_used": "llama3.1:8b",
    "tokens_used": 342,
    "created_at": "2026-01-15T10:30:00Z"
  },
  "artifacts": []
}
```

---

## 4. Component Boundaries

### Backend Modules

| Module | Responsibility | Key Classes |
|--------|---------------|-------------|
| `app.api.v1.session` | HTTP routing, validation | `router` |
| `app.services.agent` | Orchestration, session lifecycle | `AgentService` |
| `app.services.llm` | Provider abstraction | `BaseLLMProvider`, `OllamaProvider`, etc. |
| `app.services.embeddings` | Vector operations | `EmbeddingService` |
| `app.services.rag` | Retrieval, formatting | `RAGService`, `RetrievalResult` |
| `app.services.ingestion` | Transcript loading, chunking | `TranscriptIngestionService` |
| `app.services.sanitizer` | HTML safety | `sanitize_html`, `create_sandboxed_html` |
| `app.skills.base` | Skill framework | `BaseSkill`, `SkillRegistry` |
| `app.skills.ship30` | Essay generation | `Ship30Skill` |
| `app.skills.artifact` | Document generation | `ArtifactSkill` |

### Frontend Modules

| Component | Responsibility |
|-----------|---------------|
| `Sidebar` | Sessions, model selector, skills |
| `MessageList` | Virtualized message history |
| `MessageBubble` | Render markdown, citations |
| `ChatInput` | Textarea, skill triggers, send |
| `ArtifactViewer` | Iframe sandbox, render/source toggle |

---

## 5. Ingestion & Retrieval Flow

### Ingestion (Startup / Manual)
```
1. Scan data/transcripts/*.json
2. Parse each: {title, url, date, content, speaker}
3. Split content → chunks (1000 tokens, 200 overlap)
4. Embed chunks → sentence-transformers/all-MiniLM-L6-v2
5. Store in ChromaDB with metadata
6. Index complete → ready for queries
```

### Retrieval (Per Query)
```
1. User message → embed query
2. ChromaDB similarity search (top_k=5)
3. Filter by SIMILARITY_THRESHOLD (0.7)
4. Format context + citations
5. Inject into system prompt
6. LLM generates grounded response
```

---

## 6. Agent Routing & Skill System

### Routing Logic
```python
def route_message(message: str, use_skill: str = None) -> Skill:
    if use_skill:
        return SkillRegistry.get(use_skill)
    return SkillRegistry.find_triggered(message) or None
```

### Skill Interface
```python
class BaseSkill(ABC):
    name: str
    description: str
    trigger_keywords: List[str]
    
    @abstractmethod
    def get_system_prompt() -> str: ...
    
    @abstractmethod
    def get_user_prompt_template() -> str: ...
    
    async def execute(query, history) -> SkillResult: ...
```

### Registered Skills
1. **ship30** - Ship 30 for 30 style essays (~1250 words)
2. **artifact** - Markdown/HTML document generation

---

## 7. Model Toggle Architecture

### Configuration Layer
```python
settings.LLM_PROVIDER  # "ollama" | "anthropic" | "openai"
```

### Provider Factory
```python
def get_llm_provider(provider: str = None) -> BaseLLMProvider:
    provider = provider or settings.LLM_PROVIDER
    if provider == "ollama": return OllamaProvider()
    elif provider == "anthropic": return AnthropicProvider()
    elif provider == "openai": return OpenAIProvider()
    raise ValueError(f"Unknown provider: {provider}")
```

### Fallback Behavior
- Default: Ollama (local, free, private)
- If Ollama unavailable → health check fails → UI shows disconnected
- User can switch to cloud via sidebar (requires API key in `.env`)
- Session stores provider/model for continuity

---

## 8. Security Architecture

### Artifact Sanitization Pipeline
```
Raw LLM Output
     │
     ▼
┌─────────────────────────────────────┐
│  Bleach Clean                       │
│  - Allowlist tags/attrs/styles      │
│  - Strip scripts, iframes, events   │
│  - Remove javascript: protocols     │
└─────────────────────────────────────┘
     │
     ▼
Sanitized HTML stored in DB
     │
     ▼
Iframe Render (sandbox="allow-scripts allow-same-origin")
```

### Allowed HTML Subset
- **Tags**: p, h1-h6, ul/ol/li, table, code/pre, blockquote, a, img, div/span, semantic HTML5
- **Attributes**: class, id, style (allowlisted CSS), href, src, alt, target, rel
- **Styles**: color, font, layout, spacing, borders, shadows (no position:fixed, no @import)
- **Protocols**: http, https, mailto, data

### CSP Headers (via FastAPI middleware)
```
Content-Security-Policy: 
  default-src 'self';
  script-src 'self' 'unsafe-inline' 'unsafe-eval';
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  font-src 'self' https://fonts.gstatic.com;
  img-src 'self' data:;
  frame-src 'self';
  connect-src 'self' http://localhost:8000 http://localhost:11434;
```

---

## 9. Deployment Topology

### Local Development (Docker Compose)
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│  Backend    │────▶│  PostgreSQL │
│  (5173)     │     │  (8000)     │     │  (5432)     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Ollama    │
                    │  (11434)    │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  ChromaDB   │
                    │ (file-based)│
                    └─────────────┘
```

### Production Considerations
| Component | Local | Production |
|-----------|-------|------------|
| PostgreSQL | Docker | Supabase/Railway/AWS RDS |
| Ollama | Docker | GPU instance / Ollama Cloud |
| ChromaDB | File | Chroma Cloud / Pinecone / Weaviate |
| Frontend | Vite dev | Vercel/Netlify/Cloudflare Pages |
| Backend | Uvicorn | Gunicorn + Uvicorn workers |
| Secrets | .env | Vault/Secrets Manager |

---

## 10. Observability

### Structured Logging (JSON)
```json
{
  "timestamp": "2026-01-15T10:30:00.123Z",
  "level": "INFO",
  "logger": "app.services.agent",
  "event": "chat_complete",
  "session_id": "uuid",
  "model": "llama3.1:8b",
  "tokens": 342,
  "latency_ms": 1250,
  "skill_used": "ship30"
}
```

### Health Check Response
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "llm_provider": "ollama",
  "llm_model": "llama3.1:8b"
}
```

### Key Metrics to Monitor
- Request latency (p50, p95, p99)
- Token usage per request
- Retrieval score distribution
- Error rates by type
- Session duration
- Artifact generation rate

---

## 11. Extensibility Points

| Extension Point | Location | Example |
|----------------|----------|---------|
| New Skill | `app/skills/` | `TrendAnalysisSkill` |
| New LLM Provider | `app/services/llm.py` | `GeminiProvider` |
| New Vector DB | `app/services/embeddings.py` | `PineconeEmbeddingService` |
| New Artifact Type | `app/skills/artifact.py` | `NotionExportSkill` |
| Auth | `app/api/deps.py` | `get_current_user` |
| Webhooks | `app/api/v1/webhooks.py` | `SlackBotHandler` |