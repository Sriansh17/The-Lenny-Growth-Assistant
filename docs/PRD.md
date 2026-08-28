# Product Requirements Document: The Lenny Growth Assistant

## 1. User and Problem

### Primary User
**Product Managers, Growth Leaders, and Startup Founders** who follow Lenny's Podcast/Newsletter for product and growth insights but struggle to:
- Find specific advice across 200+ episodes
- Synthesize learnings into actionable formats
- Apply principles to their specific context

### Job to Be Done
> "When I have a product/growth question, I want grounded answers from Lenny's transcripts instantly, so I can make better decisions without spending hours searching through episodes."

### Pain Points Removed
- **Search fatigue**: No more scrubbing through transcripts or YouTube
- **Context loss**: Session memory maintains conversation thread
- **Format friction**: One-click generation of essays, templates, artifacts
- **Hallucination risk**: Every claim cites source episode/transcript

---

## 2. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Query Resolution Rate** | ≥85% | % of questions answered with ≥1 citation |
| **Session Length** | ≥5 messages | Average messages per session |
| **Artifact Generation** | ≥30% sessions | Sessions producing ≥1 artifact |
| **Local Model Latency** | <5s p95 | Time to first token (Ollama) |
| **Hallucination Rate** | <2% | Manual eval of 100 responses |

---

## 3. Assumptions

| Assumption | Rationale | Validation |
|------------|-----------|------------|
| Transcripts available as JSON | Lenny's repo provides structured data | Verified via public repo |
| 8B param model sufficient | Llama 3.1 8B handles RAG well | Benchmarked locally |
| Single-user local demo | FDE engagement is internal tool | No auth needed for MVP |
| ChromaDB local persistence | Simpler than managed vector DB | Zero-config for evaluator |
| 1000 token chunks | Balances context vs precision | Standard RAG practice |

---

## 4. Scope Choices

### Included (MVP)
- ✅ FastAPI + PostgreSQL + ChromaDB
- ✅ Ollama local LLM (primary demo)
- ✅ Anthropic/OpenAI cloud fallback
- ✅ RAG with source citations
- ✅ Session persistence
- ✅ Ship 30 for 30 essay skill
- ✅ Markdown/HTML artifact viewer
- ✅ HTML sanitization (XSS protection)
- ✅ Docker Compose one-command start

### Excluded (Post-MVP)
- ❌ Multi-user auth (OAuth, JWT)
- ❌ Real-time streaming tokens (SSE/WebSocket)
- ❌ Transcript auto-sync from RSS
- ❌ Evaluation harness (LangSmith)
- ❌ Fine-tuned embedding model
- ❌ Mobile-native app
- ❌ Team workspaces/sharing

### Why Excluded
- **Auth**: Adds complexity without core value demo
- **Streaming**: Ollama streaming less reliable; batch acceptable
- **Auto-sync**: Manual ingestion sufficient for demo corpus
- **Eval harness**: Manual test plan covers acceptance criteria

---

## 5. Risks and Trade-offs

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Hallucination** | Medium | High | Strict RAG grounding; "I don't know" fallback; citation enforcement |
| **Local model quality** | Medium | High | 8B model + good prompts; cloud fallback documented |
| **Latency (Ollama)** | High | Medium | Async streaming; loading states; model size trade-off doc |
| **XSS in artifacts** | Low | Critical | Bleach sanitization; CSP headers; iframe sandbox |
| **Data leakage** | Low | High | No external API calls in local mode; env var config |
| **Vector DB sync** | Low | Medium | Versioned ingestion; refresh endpoint |
| **Cost (cloud)** | Low | Low | Local-first; cloud keys optional |

### Key Trade-offs
1. **Local vs Cloud**: Default to Ollama for demo reliability; cloud as opt-in
2. **Chunk size**: 1000 tokens balances recall/precision; configurable
3. **Session scope**: Single-user, no auth — simplifies handoff
4. **Artifact security**: Sanitize + iframe sandbox over complex CSP

---

## 6. User Flows

### Flow 1: New User Ask Question
1. User opens app → sees empty state with examples
2. Types question → hits Enter
3. System creates session → retrieves context → generates answer
4. Response shows with citations → user can follow up

### Flow 2: Generate Ship 30 Essay
1. User types "Write a Ship 30 essay on activation"
2. System detects skill trigger → routes to Ship30Skill
3. Skill retrieves relevant transcripts → generates ~1250 word essay
4. Essay renders in chat + opens in artifact viewer

### Flow 3: Create HTML Artifact
1. User asks "Create a growth experiment template"
2. Artifact skill generates HTML/CSS → sanitizes → saves
3. Artifact viewer opens side-by-side with chat
4. User toggles render/source view

### Flow 4: Switch LLM Provider
1. User opens sidebar → selects "Anthropic" → enters API key
2. System validates key → updates session config
3. Subsequent messages use Claude

---

## 7. Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| AC-1 | App starts with `docker-compose up` | Fresh clone runs in <5 min |
| AC-2 | New chat creates session in DB | POST /sessions → 201, UUID returned |
| AC-3 | Question returns cited answer | Response contains `Sources:` section |
| AC-4 | Follow-up uses context | Second message references first |
| AC-5 | Ship 30 skill produces ~1250 words | Word count 1100-1400 |
| AC-6 | Artifact renders in viewer | HTML loads in iframe without errors |
| AC-7 | HTML sanitized (no scripts) | `<script>` stripped from output |
| AC-8 | Provider switch works | Model badge updates in header |
| AC-9 | Health endpoint reports status | GET /health → JSON with db/llm status |
| AC-10 | Transcripts ingested on startup | Chroma collection has >0 docs |

---

## 8. Implementation Plan

| Phase | Tasks | Duration |
|-------|-------|----------|
| **0. Setup** | Repo, Docker, FastAPI skeleton, DB models | Day 1 |
| **1. Core** | Sessions, messages, PostgreSQL, health check | Day 1-2 |
| **2. LLM Layer** | Provider abstraction, Ollama, Anthropic, OpenAI | Day 2 |
| **3. RAG** | ChromaDB, embeddings, ingestion, retrieval | Day 2-3 |
| **4. Agent** | Conversation loop, skill routing, citations | Day 3 |
| **5. Skills** | Ship30Skill, ArtifactSkill, registry | Day 3-4 |
| **6. Frontend** | Chat UI, artifact viewer, sidebar, model selector | Day 4 |
| **7. Security** | HTML sanitization, sandbox, CSP | Day 4 |
| **8. Polish** | Tests, docs, demo video, README | Day 5 |

---

## 9. Handoff Notes

- **Run**: `docker-compose up --build` (first time pulls images)
- **Ollama model**: Auto-pulls `llama3.1:8b` on first run (~5GB)
- **Transcripts**: Place JSON files in `data/transcripts/` before start
- **Cloud keys**: Add to `.env` to enable Anthropic/OpenAI
- **Logs**: Structured JSON in Docker; `docker-compose logs -f backend`
- **Extend**: Add skills in `backend/app/skills/`; register in `__init__.py`