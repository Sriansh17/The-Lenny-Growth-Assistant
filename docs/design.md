# Design Document: The Lenny Growth Assistant

## 1. UI/UX Principles

### Core Principles
1. **Chat-First**: Primary interaction is conversation; everything else supports it
2. **Grounded Trust**: Every answer shows its sources; uncertainty is explicit
3. **Progressive Disclosure**: Advanced features (skills, artifacts) discoverable but not intrusive
4. **Local-First Feel**: Fast, private, no loading spinners for simple actions
5. **Accessibility by Default**: Semantic HTML, keyboard nav, screen reader support

### Design Tokens
| Token | Value | Usage |
|-------|-------|-------|
| Primary/Accent | `#10b981` (Emerald 500) | Actions, active states, send button |
| Surface | `#111827` (Gray 900) | Cards, sidebar, input background |
| Background | `#030712` (Gray 950) | Page background |
| Text Primary | `#f9fafb` (Gray 50) | Headings, body |
| Text Muted | `#6b7280` (Gray 500) | Metadata, placeholders |
| Border | `#1f2937` (Gray 800) | Dividers, input borders |
| Success | `#34d399` (Emerald 400) | Connected status |
| Error | `#f87171` (Red 400) | Disconnected, errors |
| User Bubble | `#059669` (Emerald 600) | User message background |
| Assistant Bubble | `#1f2937` (Gray 800) | Assistant message background |

### Typography
- **UI Font**: Inter (400, 500, 600, 700)
- **Mono Font**: JetBrains Mono (400, 500)
- **Scale**: 12px base, 1.25 ratio
  - xs: 12px / 16px
  - sm: 14px / 20px
  - base: 16px / 24px
  - lg: 20px / 28px
  - xl: 24px / 32px
  - 2xl: 30px / 36px

### Spacing
- Base unit: 4px
- Scale: 1, 2, 3, 4, 5, 6, 8, 10, 12, 16

### Border Radius
- sm: 4px (inputs, badges)
- md: 8px (cards, buttons)
- lg: 12px (modals, panels)
- xl: 16px (sheets)
- full: 9999px (avatars, pills)

---

## 2. Information Architecture

### Primary Navigation (Sidebar)
```
Lenny Assistant
├── New Chat
├── Model Selector
│   ├── Provider: [Ollama ▼]
│   └── Model: [llama3.1:8b ▼]
├── Skills
│   ├── ship30 - Ship 30 for 30 essays
│   └── artifact - Generate documents
└── Recent Sessions
    ├── Session 1 (12 msgs · 2h ago)
    ├── Session 2 (5 msgs · 1d ago)
    └── ...
```

### Chat View (Main)
```
┌─────────────────────────────────────────┐
│ Header: Title | Model Badge | Status    │
├─────────────────────────────────────────┤
│                                         │
│  [Welcome State OR Message History]    │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Artifact Viewer (conditional)  │   │
│  │ [Render | Source] [✕]          │   │
│  └─────────────────────────────────┘   │
├─────────────────────────────────────────┤
│ [Textarea] [/ Skills] [Send ▶]         │
└─────────────────────────────────────────┘
```

---

## 3. Key Interaction States

### 3.1 Empty State (No Session)
- Centered illustration + headline + 3 example prompts
- Click example → creates session + sends message
- "New Chat" button in sidebar always available

### 3.2 Active Conversation
- Messages render bottom-up (newest at bottom)
- Auto-scroll to bottom on new message
- User messages: right-aligned, primary background
- Assistant messages: left-aligned, white with border
- Streaming: token-by-token with typing indicator

### 3.3 Citations Display
- Collapsible `<details>` under assistant message
- Summary shows count: "Sources (3)"
- Expanded: numbered list with title, source, URL
- Click source → opens in new tab

### 3.4 Artifact Viewer
- **Trigger**: Skill generates artifact → auto-opens panel
- **Desktop**: Right sidebar (400px), resizable
- **Mobile**: Bottom sheet (60% height), swipe to dismiss
- **Tabs**: Render | Source (code view)
- **Security**: Iframe sandbox, no external resources

### 3.5 Model Selector
- Dropdown for provider (Ollama/Anthropic/OpenAI)
- Dropdown for model (filtered by provider)
- Connection indicator: green/red dot + label
- Local badge for Ollama

### 3.6 Skill Discovery
- **Explicit**: Type `/` in input → skill picker dropdown
- **Implicit**: Keywords trigger auto-route (e.g., "ship 30")
- **Sidebar**: List all skills with descriptions/triggers

---

## 4. Responsive Behavior

### Breakpoints
| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 640px | Stacked: Sidebar drawer, full-width chat |
| Tablet | 640-1024px | Sidebar collapsible, chat + artifact stacked |
| Desktop | > 1024px | Three-pane: Sidebar | Chat | Artifact |

### Mobile Adaptations
- Sidebar → slide-in drawer (hamburger menu)
- Artifact viewer → bottom sheet
- Model selector → collapsed in header
- Touch targets: 44x44px minimum
- No hover-only interactions

### Tablet Adaptations
- Sidebar: collapsible rail (icons only) or full
- Artifact: stacked below chat or side-by-side
- Two-column option at 900px+

---

## 5. Accessibility (WCAG 2.1 AA)

### Keyboard Navigation
- `Tab` / `Shift+Tab`: Focus order (sidebar → header → messages → input)
- `Enter` / `Space`: Activate buttons, links
- `Escape`: Close drawers, modals, artifact viewer
- `Arrow keys`: Navigate session list, skill dropdown
- `Ctrl/Cmd + K`: Focus chat input (global shortcut)

### Screen Reader Support
- Semantic HTML: `<main>`, `<aside>`, `<header>`, `<article>`
- ARIA labels on icon buttons
- `aria-live="polite"` on message list for new messages
- `role="log"` for chat history
- `aria-expanded` on collapsible sections

### Color & Contrast
- All text: 4.5:1 minimum (AA)
- UI elements: 3:1 minimum
- Focus indicators: 2px solid primary, offset 2px
- No color-only information (status has icon + text)

### Reduced Motion
- Respects `prefers-reduced-motion`
- Disables: auto-scroll animation, pulse loaders, transitions

---

## 6. Component Specifications

### 6.1 Message Bubble
```
┌─────────────────────────────────────┐
│ 👤  Assistant          10:30 AM     │  ← Avatar + timestamp
├─────────────────────────────────────┤
│ Based on Episode 45, Lenny defines  │  ← Markdown content
│ PMF as "when users..." [1][2]       │
│                                     │
│ ▼ Sources (2)                       │  ← Collapsible citations
│  1. Episode 45 - Lenny & Fareed     │
│  2. Episode 12 - Lenny & Gokul      │
└─────────────────────────────────────┘
```
- Max width: 85% of container
- Border radius: 1.5rem / 0.5rem (asymmetric)
- Code blocks: dark theme, copy button (future)
- Links: external icon, `target="_blank" rel="noopener"`

### 6.2 Chat Input
```
┌──────────────────────────────────────────────────┐
│ Ask about product, growth, startups...  [/] [▶] │  ← Textarea + actions
├──────────────────────────────────────────────────┤
│ Press Enter to send, Shift+Enter for new line    │  ← Hint
└──────────────────────────────────────────────────┘
```
- Auto-resize (52px - 200px)
- `/` key → skill dropdown (if focused)
- Disabled during streaming
- Enter = send, Shift+Enter = newline

### 6.3 Artifact Viewer
```
┌─────────────────────────────────────────────┐
│ Growth Experiment Template    [Render ▼] [✕] │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ <iframe sandboxed>                 │   │
│  │ Rendered HTML/CSS                  │   │
│  │                                    │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Source view: <pre><code>...</code></pre>  │
└─────────────────────────────────────────────┘
```
- Iframe: `sandbox="allow-scripts allow-same-origin"`
- Height: 600px desktop, 400px mobile
- Source view: monospace, syntax highlighting (future)

### 6.4 Session List Item
```
┌────────────────────────────────────┐
│ ✏️  Product-Market Fit Deep Dive   │  ← Title (editable on hover)
│ 12 messages · 2 hours ago          │  ← Meta
│         [✏️] [🗑️]                  │  ← Hover actions
└────────────────────────────────────┘
```
- Active: primary-50 bg, primary-700 text, checkmark
- Hover: actions appear (rename, delete)
- Click: loads session
- Keyboard: Enter/Space to select

---

## 7. Visual Design Details

### Color Usage in Components
| Component | Background | Text | Border | Accent |
|-----------|------------|------|--------|--------|
| User Bubble | Primary-600 | White | - | - |
| Assistant Bubble | White | Gray-900 | Gray-200 | - |
| Sidebar | White | Gray-900 | Gray-200 (right) | - |
| Input | Gray-50 | Gray-900 | Gray-300 → Primary-500 (focus) | Primary-600 (send) |
| Artifact | White | Gray-900 | Gray-200 | - |
| Skill Badge | Gray-100 | Gray-600 | - | - |
| Status Dot | Green-500/Red-500 | - | - | - |

### Shadows
- **sm**: `0 1px 2px rgba(0,0,0,0.05)` - Inputs, badges
- **md**: `0 4px 6px rgba(0,0,0,0.07)` - Cards, artifact viewer
- **lg**: `0 10px 15px rgba(0,0,0,0.1)` - Dropdowns, sheets

### Transitions
- **Fast**: 100ms (hover, focus)
- **Normal**: 200ms (panels, drawers)
- **Slow**: 300ms (sheet enter/exit)
- **Easing**: `cubic-bezier(0.4, 0, 0.2, 1)` (Material default)

---

## 8. Error & Edge Cases

### Error States
| Scenario | UI Treatment |
|----------|--------------|
| Network error | Toast + inline retry in message |
| Ollama disconnected | Header badge red, sidebar warning |
| Empty retrieval | "No relevant transcripts found" in context |
| Skill failure | Fallback to standard RAG + error toast |
| Sanitization stripped content | Warning badge on artifact |

### Empty States
- No sessions: "Create your first chat"
- No messages: Welcome screen with examples
- No artifacts: Hidden (only shows when exists)
- No skills: Section hidden

### Loading States
- Session list: Skeleton cards
- Messages: None (optimistic UI)
- Artifact: Spinner in viewer
- Model pull: Progress in sidebar (future)

---

## 9. Animation & Micro-interactions

| Trigger | Animation |
|---------|-----------|
| New message | Fade in + slide up (150ms) |
| Sidebar toggle | Slide + fade (200ms) |
| Artifact open | Slide from right (mobile: bottom) |
| Citation expand | Height auto + fade (150ms) |
| Button hover | Scale 1.02 + color transition |
| Focus ring | Fade in (100ms) |
| Typing indicator | Pulse dots (1.5s loop) |

---

## 10. Future Enhancements

### Phase 2 (Post-MVP)
- [ ] Streaming token rendering (SSE)
- [ ] Message branching/editing
- [ ] Export conversation (PDF, Markdown)
- [ ] Custom prompt templates
- [ ] Team workspaces
- [ ] Transcript search UI
- [ ] Dark mode
- [ ] Voice input (Web Speech API)

### Design System
- Extract tokens to `@lenny-assistant/design-tokens`
- Storybook for component documentation
- Figma library for handoff


---

## 7. Design Decisions & Rationale

### Dark Theme
The UI uses a dark theme (Gray 950 background) for several reasons:
- **Reduced eye strain** during extended research sessions — PMs often spend hours analyzing content
- **Modern aesthetic** aligned with developer/power-user tools (VS Code, Linear, Arc)
- **Better contrast** for code blocks, citations, and artifact content
- **Focus on content** — dark backgrounds push text/cards forward visually

### Single-Screen Layout
The entire interface fits within the viewport (`h-screen`, `overflow-hidden`):
- **No page scroll** — messages scroll within their container, input is always visible
- **Immediate access** to chat input without scrolling
- **Split-panel architecture** — sidebar, chat, and artifact viewer coexist without navigation

### Emerald Accent Color
Chose emerald (#10b981) over blue/sky for:
- **Differentiation** from generic ChatGPT-style blue interfaces
- **Growth connotation** — green evokes growth, fitting the product's domain
- **High contrast** against dark backgrounds for accessibility

### Compact Information Density
- Small text (10-12px) for metadata, timestamps, model badges
- Truncated session titles with full text on hover
- Skills shown inline rather than in a separate panel
- Model selector condensed into two dropdowns
