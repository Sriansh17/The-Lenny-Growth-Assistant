# Manual UI Test Plan

## Prerequisites
- Application running via `docker-compose up --build`
- Frontend at http://localhost:5173
- Backend at http://localhost:8000
- Ollama model pulled and ready
- At least 5+ transcripts ingested

---

## Test 1: Health & Initial Load

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | Open http://localhost:5173 | Page loads with "Lenny Growth Assistant" title |
| 1.2 | Check header | Model selector shows "ollama" + "llama3.1:8b" |
| 1.3 | Check status indicator | Green dot (connected) |
| 1.4 | Check sidebar | Empty session list, "New Chat" button visible |

---

## Test 2: Session Management

| Step | Action | Expected Result |
|------|--------|-----------------|
| 2.1 | Click "New Chat" | New session created, input field focused |
| 2.2 | Send a message | Session appears in sidebar with auto-title |
| 2.3 | Create 3+ sessions | All appear in sidebar, most recent first |
| 2.4 | Click a different session | Messages load for that session |
| 2.5 | Delete a session | Session removed from list, messages cleared |

---

## Test 3: Grounded Conversational Assistant (RAG)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1 | Ask: "How does Gokul define product-market fit?" | Response cites Episode 1, mentions 40% disappointed test |
| 3.2 | Follow-up: "What example did he give?" | Uses session context, mentions DoorDash |
| 3.3 | Ask about non-transcript topic: "What's the weather today?" | Assistant acknowledges it can't answer from transcripts |
| 3.4 | Ask: "What growth strategies are discussed?" | Response with citations from multiple episodes |
| 3.5 | Check citations | "Sources:" section with episode titles/speakers |

---

## Test 4: Ship 30 for 30 Content Skill

| Step | Action | Expected Result |
|------|--------|-----------------|
| 4.1 | Send: "Write a Ship 30 for 30 essay about product-market fit" | ~1,250 word essay generated |
| 4.2 | Check essay structure | Has hook, headings, bullets, bold emphasis |
| 4.3 | Check grounding | Claims reference transcript sources |
| 4.4 | Check artifact | Markdown artifact created and viewable |
| 4.5 | Alternatively use skill picker to select "ship30" | Same behavior as keyword trigger |

---

## Test 5: Artifact Generation & Viewer

| Step | Action | Expected Result |
|------|--------|-----------------|
| 5.1 | Send: "Create an artifact about growth loops" | Artifact panel opens beside chat |
| 5.2 | Check render mode | Markdown/HTML renders correctly |
| 5.3 | Toggle to "Source" view | Raw markdown/HTML visible |
| 5.4 | Close artifact panel | Panel hides, chat returns to full width |
| 5.5 | Request HTML artifact | Renders in sandboxed iframe |
| 5.6 | Inject `<script>alert('xss')</script>` in request | Script tags stripped/not executed |

---

## Test 6: Model Toggle

| Step | Action | Expected Result |
|------|--------|-----------------|
| 6.1 | Check model selector in header/sidebar | Shows current provider + model |
| 6.2 | Switch to Anthropic (if API key set) | New messages use Claude |
| 6.3 | Switch back to Ollama | Reverts to local model |
| 6.4 | Send message with new provider | Response includes model_used field |

---

## Test 7: Error Handling & Resilience

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | Stop Ollama container | Health shows degraded, error message on chat |
| 7.2 | Restart Ollama | Service recovers, chat works again |
| 7.3 | Send empty message | Validation error (input required) |
| 7.4 | Send very long message (>10000 chars) | Handled gracefully (truncated or error) |
| 7.5 | Open app with DB down | Health endpoint shows disconnected |

---

## Test 8: Responsive Design

| Step | Action | Expected Result |
|------|--------|-----------------|
| 8.1 | Resize to mobile (< 768px) | Sidebar collapses, hamburger menu appears |
| 8.2 | Open sidebar on mobile | Overlays content |
| 8.3 | View artifact on mobile | Full-screen overlay with close button |
| 8.4 | Test on tablet (768-1024px) | Layout adjusts appropriately |

---

## Test 9: Accessibility

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9.1 | Tab through UI | Focus visible on all interactive elements |
| 9.2 | Enter key on chat input | Sends message |
| 9.3 | Shift+Enter | Creates newline (no send) |
| 9.4 | Screen reader (NVDA/VoiceOver) | Buttons have labels, messages are announced |
| 9.5 | High contrast mode | All text readable |

---

## Test 10: API Direct (curl)

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Create session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "llm_provider": "ollama", "llm_model": "llama3.1:8b"}'

# Send chat message (replace SESSION_ID)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "message": "What is product-market fit?"}'

# List skills
curl http://localhost:8000/api/v1/skills
```

---

## Pass Criteria

- All Test 1-5 steps pass ✅
- Test 6 passes if cloud API key configured
- Test 7 demonstrates graceful degradation
- Test 8-9 for polish points
- No console errors during normal usage
