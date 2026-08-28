# Manual Test Plan

## Prerequisites
- Docker & Docker Compose installed
- 8GB+ RAM available
- Ports 5173, 8000, 5432, 11434 available

## Test Environment Setup
```bash
git clone <repo>
cd The-Lenny-Growth-Assistant
cp .env.example .env
docker-compose up --build
```

Wait for all services to show `healthy` status (5-10 min first run).

---

## Test Cases

### TC-01: Application Startup
**Steps**:
1. Run `docker-compose up --build`
2. Wait for all containers healthy
3. Open http://localhost:5173

**Expected**:
- Frontend loads without errors
- Sidebar shows "New Chat" button
- Model selector shows "Ollama (Local)" with "llama3.1:8b"
- Health indicator shows green "Connected"

---

### TC-02: Create New Session
**Steps**:
1. Click "New Chat" button
2. Verify URL updates with session ID

**Expected**:
- New session created in sidebar
- Chat area shows welcome state
- Session title "Untitled Session" or timestamp

---

### TC-03: Basic Chat with Citations
**Steps**:
1. In chat input, type: "How does Gokul define product-market fit?"
2. Press Enter
3. Wait for response

**Expected**:
- Assistant responds with answer
- Response includes "Sources" section with citations
- Citations reference Episode 1 (Gokul Rajaram)
- Timestamp and model badge shown

---

### TC-04: Follow-up Question (Context Retention)
**Steps**:
1. After TC-03 response, type: "What about his advice for early-stage PMs?"
2. Press Enter

**Expected**:
- Assistant answers using conversation context
- References same episode/speaker
- Session message count increases

---

### TC-05: Ship 30 for 30 Skill Trigger
**Steps**:
1. Type: "Write a Ship 30 for 30 essay on user activation"
2. Press Enter

**Expected**:
- Skill auto-detected (or use `/skill ship30`)
- Generates ~1250 word essay
- Essay has: hook, headings, bullets, bold emphasis, key takeaway
- Artifact viewer opens automatically
- Citations reference relevant transcripts

---

### TC-06: Artifact Skill - Markdown
**Steps**:
1. Type: "Create a markdown checklist for product launch"
2. Press Enter

**Expected**:
- Generates markdown document
- Artifact viewer opens in Render mode
- Toggle to Source view shows raw markdown

---

### TC-07: Artifact Skill - HTML
**Steps**:
1. Type: "Create an HTML growth experiment template with CSS"
2. Press Enter

**Expected**:
- Generates complete HTML with embedded CSS
- Artifact viewer renders styled HTML in iframe
- Source view shows sanitized HTML
- No script tags or external resources

---

### TC-08: Model Switching
**Steps**:
1. Open sidebar
2. Change Provider to "Anthropic" (requires API key in .env)
3. Select "claude-3-5-sonnet-20241022"
4. Create new chat
5. Ask a question

**Expected**:
- Header model badge updates
- New session uses selected model
- Response shows model in badge

---

### TC-09: Session Persistence
**Steps**:
1. Have an active session with messages
2. Refresh browser (F5)
3. Check sidebar

**Expected**:
- Session list persists
- Current session remains selected
- Messages reload

---

### TC-10: Session Management
**Steps**:
1. Hover over session in sidebar → click rename → enter new title
2. Click delete on another session → confirm

**Expected**:
- Rename updates title in sidebar and header
- Delete removes session and messages

---

### TC-11: Artifact Viewer Interactions
**Steps**:
1. Generate an artifact (TC-05/06/07)
2. Toggle Render/Source
3. Close artifact viewer (X button)
4. Reopen from session artifacts (future: artifacts list)

**Expected**:
- Smooth transitions
- Content preserved
- Mobile: bottom sheet behavior

---

### TC-12: Skill Discovery via Slash Command
**Steps**:
1. Click in chat input
2. Type `/`
3. Select "ship30" from dropdown
4. Complete prompt

**Expected**:
- Dropdown shows available skills
- Selection pre-fills input
- Skill executes correctly

---

### TC-13: Error Handling - Unknown Topic
**Steps**:
1. Ask: "What is the capital of Mars?"

**Expected**:
- Response: "Based on the available transcripts, I don't have enough information..."
- No hallucinated answer

---

### TC-14: HTML Sanitization Security
**Steps**:
1. Create artifact with: `<script>alert('xss')</script><h1>Safe</h1>`
2. View in artifact viewer

**Expected**:
- Script tag removed
- Only `<h1>Safe</h1>` renders
- Browser console shows no alert

---

### TC-15: Responsive Layout
**Steps**:
1. Resize browser to mobile width (<640px)
2. Test sidebar hamburger menu
3. Test artifact bottom sheet

**Expected**:
- Sidebar becomes drawer
- Artifact viewer becomes bottom sheet
- All touch targets ≥44px

---

### TC-16: Keyboard Navigation
**Steps**:
1. Tab through interface
2. Use Escape to close drawers
3. Use Enter to send message
4. Use Shift+Enter for newline

**Expected**:
- Logical focus order
- All interactive elements reachable
- Shortcuts work

---

### TC-17: API Health Check
**Steps**:
1. Call GET http://localhost:8000/api/v1/health

**Expected**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "llm_provider": "ollama",
  "llm_model": "llama3.1:8b"
}
```

---

### TC-18: Transcript Ingestion Verification
**Steps**:
1. Check ChromaDB stats via API or logs
2. Verify 3 sample transcripts loaded

**Expected**:
- Logs show "ingestion_complete" with 3 transcripts
- Vector DB has >0 documents

---

### TC-19: Concurrent Sessions
**Steps**:
1. Open two browser tabs
2. Create different sessions in each
3. Chat in both simultaneously

**Expected**:
- Independent session contexts
- No cross-contamination

---

### TC-20: Long Conversation
**Steps**:
1. Have 20+ message conversation
2. Verify scrolling, context retention

**Expected**:
- Auto-scroll works
- Context maintained (within token limits)
- Performance acceptable

---

## Test Results Template

| Test Case | Status | Notes |
|-----------|--------|-------|
| TC-01 | Pass/Fail | |
| TC-02 | Pass/Fail | |
| TC-03 | Pass/Fail | |
| TC-04 | Pass/Fail | |
| TC-05 | Pass/Fail | |
| TC-06 | Pass/Fail | |
| TC-07 | Pass/Fail | |
| TC-08 | Pass/Fail | |
| TC-09 | Pass/Fail | |
| TC-10 | Pass/Fail | |
| TC-11 | Pass/Fail | |
| TC-12 | Pass/Fail | |
| TC-13 | Pass/Fail | |
| TC-14 | Pass/Fail | |
| TC-15 | Pass/Fail | |
| TC-16 | Pass/Fail | |
| TC-17 | Pass/Fail | |
| TC-18 | Pass/Fail | |
| TC-19 | Pass/Fail | |
| TC-20 | Pass/Fail | |

---

## Known Limitations (Acceptable for MVP)

1. **Streaming**: Token-by-token streaming not implemented (batch response)
2. **Auth**: No multi-user authentication
3. **Transcript Sync**: Manual JSON placement only
4. **Evaluation**: No automated eval harness
5. **Mobile Polish**: Some responsive edge cases

---

## Troubleshooting During Testing

| Issue | Resolution |
|-------|------------|
| Frontend blank | Check browser console, verify Vite proxy |
| Backend 500 | Check `docker-compose logs backend` |
| Ollama slow | First request pulls model, subsequent faster |
| No citations | Verify transcripts in data/transcripts/ |
| Artifact not rendering | Check sanitized_content in DB |