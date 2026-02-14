# OpenClaw Dashboard Redesign — Architecture

## Current State
- **Location:** `/opt/homebrew/lib/node_modules/openclaw/dist/control-ui/`
- **Tech:** Single-page web component app (`<openclaw-app>`), bundled Vite build
- **Stack:** Vanilla JS web components, CSS custom properties, Space Grotesk + JetBrains Mono fonts
- **Theme:** Already dark-mode with light toggle. Red accent (#ff5c5c), dark bg (#12141a)
- **Size:** 543KB JS (minified), 84KB CSS
- **⚠️ Problem:** Files are in `node_modules` — any changes get overwritten on `npm update`

## What Steven Wants
1. **More aesthetic** — dark, minimalist, industrial (his TØrr brand style)
2. **Thinking indicator** — show when agent is processing
3. **Progress tracking** — show how far along on current request

## Architecture Plan

### Approach: CSS Override + JS Injection
Since we can't modify the bundled source (it'll be overwritten), we inject a custom stylesheet and script:
- Custom CSS file loaded after the bundle CSS
- Custom JS that hooks into the WebSocket/SSE events to track agent state

### 1. Aesthetic Overhaul (CSS Override)
**File:** `~/.openclaw/ui/custom.css`

Changes:
- Swap accent from red (#ff5c5c) to something more refined (muted teal or white)
- Tighten spacing, reduce border-radius for sharper industrial feel
- Adjust card backgrounds for more contrast depth
- Consider IBM Plex Mono (TØrr brand) instead of JetBrains Mono
- Subtle grid/scan-line background texture

### 2. Thinking Indicator (JS + CSS)
**Current:** Already has `.chat-reading-indicator` with bouncing dots and `.chat-bubble.streaming` with pulsing border
**Enhancement:**
- Add a top-bar or bottom-bar persistent indicator: "Processing..." with elapsed time
- Animate the OpenClaw logo/brand element while thinking
- Add subtle glow pulse to the entire chat compose area while waiting

### 3. Progress Tracking (JS)
**Challenge:** LLM responses are streamed — there's no "50% done" signal
**Realistic options:**
- **Token counter:** Show tokens generated in real-time (if available via SSE/WS)
- **Tool call tracker:** Show "Executed 3 of N tools" when agent makes sequential tool calls
- **Elapsed time + stage:** "Thinking... (12s)" → "Executing tools... (3 calls)" → "Composing response..."
- **Activity feed:** Mini log showing what the agent is doing (reading file, searching web, etc.)

### Implementation Priority
1. CSS aesthetic overhaul (quick win, pure CSS)
2. Thinking indicator with timer (needs JS hook)
3. Activity/stage tracker (needs deeper integration)

## Open Question
Does OpenClaw support custom UI injection (custom CSS/JS loading from ~/.openclaw/ui/)? If not, we'd need to either:
- Patch index.html to add a `<link>` and `<script>` tag
- Create a proxy/wrapper that serves the modified UI
- Submit a PR to OpenClaw to support custom UI theming
