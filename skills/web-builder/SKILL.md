---
name: web-builder
description: Full web development lifecycle — from PRD to live URL. Scaffold SvelteKit apps, bundle single-file HTML, deploy to GitHub Pages, Vercel, or Cloudflare. Use when building any web application, static site, or HTML artifact.
---

# Web Builder

Web apps are the most common deliverable an AI agent builds. This skill covers the full lifecycle from "I want a thing" to "here's the live URL" — scaffolding, building, testing, and deploying. It encodes opinionated defaults so you spend time on the product, not on tooling decisions.

Every web project follows the same arc: understand what's needed, choose the right architecture, build it, make it look right, and ship it somewhere people can use it. Most failures happen at the first and last steps — a vague spec produces a vague app, and a project that only works on localhost is unfinished.

---

## Choosing Your Path

Before writing any code, decide the architecture. This is the single most consequential decision.

| Signal | Path | Why |
|--------|------|-----|
| Multiple pages, routing, server-side logic, database, auth | **SvelteKit App** | Full framework with SSR, API routes, middleware |
| Single interaction: calculator, game, demo, visualization | **Single HTML File** | Zero infrastructure, instant sharing, works offline |
| Documentation, landing page, portfolio, blog | **Static Site** | Minimal JS, fast loads, GitHub Pages or Cloudflare |
| Telegram Mini App, itch.io game, embedded widget | **Single HTML Bundle** | Must be one file, all assets inlined |

### Decision Tree

```
Does it need routing between pages?
  YES → Does it need a database or auth?
    YES → SvelteKit App (full stack)
    NO  → SvelteKit App (static adapter) or Static Site
  NO  → Is it a single interaction/screen?
    YES → Will it be distributed as a file?
      YES → Single HTML Bundle
      NO  → Single HTML (can host normally)
    NO  → Static Site
```

**The 5-minute rule:** If you can describe the entire UI in one sentence with no "and then the user goes to..." — it's a single HTML file.

---

## Phase 0: The PRD

This is where most web projects fail. A bad spec produces a bad app. Spend the time here.

### Gathering Requirements

Start with: "What do you want to build?"

Then fill gaps systematically:

| Gap | Question | Why It Matters |
|-----|----------|----------------|
| Users unclear | "Who's the primary user?" | Determines complexity, auth needs |
| Core action unclear | "What's the ONE thing they must do?" | Prevents scope creep |
| Design unclear | "Show me 1-3 sites you like the feel of" | Anchors visual decisions |
| Data unclear | "What data exists? What needs to persist?" | Determines database needs |
| Deploy unclear | "Where should this live?" | Affects architecture choices |

### Writing the PRD

The PRD is a `prd.json` containing user stories. Each story must fit in one context window. Standard sequence:

1. **Scaffold** — Project creation, dependencies
2. **Configure** — Tailwind, component library, adapters
3. **Mock Data** — Seed data for development
4. **Foundation** — Index page, layout, navigation → **CHECKPOINT: pause for user review**
5. **Features** — Core functionality, one story per feature
6. **Infrastructure** — Auth, database, API routes
7. **Polish** — Responsive design, loading states, error pages
8. **Tests** — Unit + E2E tests

**The checkpoint at step 4 is non-negotiable.** Show the user a working shell before building features. Changing direction after the foundation is cheap; changing direction after features is expensive.

### Design Preferences

Capture these early and enforce them throughout:

| Preference | Options | Default |
|------------|---------|---------|
| Color scheme | Light / Dark / System-adaptive | System-adaptive |
| Visual density | Spacious / Balanced / Compact | Balanced |
| Style | Minimalist / Rich / Playful | Minimalist |
| Component library | Skeleton / shadcn-svelte / Custom | Skeleton |

Store design decisions in the PRD. Reference them in every feature story: "Use the established design system. Do not add new colors or spacing values."

---

## SvelteKit Apps

### Prerequisites

| CLI | Purpose | Install |
|-----|---------|---------|
| `sv` | SvelteKit scaffolding | `npm i -g sv` (or `pnpx`) |
| `pnpm` | Package manager | `npm i -g pnpm` |
| `gh` | GitHub repo creation | [cli.github.com](https://cli.github.com) |
| `vercel` | Deployment | `npm i -g vercel` |

### Opinionated Defaults

- **Component library:** Skeleton (Svelte 5 native) + Bits UI fallback
- **Package manager:** pnpm
- **Deployment:** Vercel
- **Add-ons:** ESLint, Prettier, Vitest, Playwright, mdsvex, MCP
- **State:** Svelte 5 runes (`$state`, `$derived`, `$effect`)
- **Adapter:** `adapter-auto` (detects Vercel, Cloudflare, Netlify, falls back to adapter-node)

All defaults can be overridden via `SKILL-CONFIG.json`. Check `~/.openclaw/workspace/SKILL-CONFIG.json` for user-specific overrides before using skill defaults.

### Technical Stack

```
CLI:              pnpx sv create [name]
Template:         minimal
TypeScript:       yes
Package manager:  pnpm

Core add-ons (via sv add):
  ✓ eslint, prettier, mcp, mdsvex
  ✓ tailwindcss (+ typography, forms plugins)
  ✓ vitest, playwright

Post-scaffold:
  ✓ Skeleton + Bits UI
  ✓ vite-plugin-pwa
  ✓ Svelte 5 runes mode
  ✓ adapter-auto

Inferred from description:
  drizzle  → if needs database
  lucia    → if needs auth
  paraglide → if needs i18n
```

### Execution Workflow

**Preflight:**
```bash
gh auth status 2>/dev/null && echo "✓ GitHub" || echo "✗ GitHub"
command -v pnpm &>/dev/null && echo "✓ pnpm" || echo "⚠ pnpm (will use npm)"
vercel whoami 2>/dev/null && echo "✓ Vercel" || echo "✗ Vercel"
```

**Three stages:**
1. **Development** — Local, dev branch, mock data. Execute stories via sub-agents in parallel waves. Exit: `pnpm check && pnpm test && pnpm test:e2e`
2. **Staging** — Main branch, Vercel preview URL, real data. Smart retry (3 attempts) for environment issues.
3. **Production** — `vercel --prod`, final E2E verification.

**Handoff:** Generate `ADMIN.md` with local dev instructions, env vars, project structure, adding pages, DB migrations, deployment workflow, troubleshooting.

### Code Patterns

- `$state()` runes for reactive state
- `$derived()` for computed values
- Context API (`setContext`/`getContext`) for cross-component state
- Server state through `load` functions → `data` prop
- **Never** store user-specific state in module-level variables
- Prefer `bind:` over callbacks
- `$effect()` over `onMount`
- ~200 line soft limit per component

### Directory Structure

```
src/
├── routes/              # SvelteKit routes
├── lib/
│   ├── components/      # Skeleton + Bits UI components
│   ├── server/          # Server-only code (db, auth)
│   ├── stores/          # State (.svelte.ts for runes)
│   ├── utils/           # Helpers
│   └── types/           # TypeScript types
static/
└── icons/               # PWA icons
```

### Database Options (drizzle)

- PostgreSQL + postgres.js or neon
- SQLite + better-sqlite3 or libsql
- Turso + @libsql/client

---

## Single HTML Bundling

### When to Use

- Telegram Mini App games
- itch.io HTML5 games
- Single-file demos/prototypes
- Portfolio artifacts
- Any context requiring offline-capable single-file delivery

### Bundling Patterns

**Simple (no framework):** Inline everything — CSS in `<style>`, JS in `<script>`, images as base64 data URIs.

**React/Vite → Single HTML:**
```bash
npm run build
npx parcel build dist/index.html --no-source-maps
npx html-inline dist/index.html -o bundle.html
```

### Asset Inlining

```html
<!-- Images → base64 -->
<img src="data:image/png;base64,iVBOR..." />

<!-- Fonts → base64 @font-face -->
<style>
@font-face {
  font-family: 'GameFont';
  src: url(data:font/woff2;base64,...) format('woff2');
}
</style>

<!-- Audio → base64 (small effects only, <500KB) -->
<audio src="data:audio/mp3;base64,..."></audio>
```

### Distribution Checklist

- [ ] Single HTML file, no external dependencies
- [ ] Works offline (no CDN links)
- [ ] Mobile touch support
- [ ] Safe-area insets (WebView environments)
- [ ] File size optimized
- [ ] No console errors

---

## GitHub Pages Deploy

### Quick Workflow

```bash
bash scripts/init_project.sh <project-name>
# Build your site
bash scripts/deploy_github_pages.sh <project-name> <github-username>
```

GitHub Actions deploys on push to main → live at `https://<username>.github.io/<project-name>/`

### Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Site not deploying | Pages source wrong | Settings → Pages → Source = `gh-pages` branch |
| 404 on all pages | Base path missing | Set `base` in svelte.config.js to `/<repo-name>` |
| 404 on refresh (SPA) | No fallback for client routes | Add `404.html` that redirects to `index.html` |
| Permission errors | Auth expired | `gh auth status`, re-login if needed |
| Assets not loading | Relative paths broken | Use absolute paths from base: `{base}/img/logo.png` |
| Build failures | YAML syntax | Check Actions logs, validate workflow file |

---

## Vercel Deploy

### Deploy Flow

```bash
npm i -g vercel && vercel login
vercel link          # Link project
vercel               # Preview deploy
vercel --prod        # Production deploy
vercel domains add <domain>  # Custom domain
```

### Environment Variables

```bash
vercel env add DATABASE_URL production
```

### Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Build fails | Missing env vars | Check Vercel dashboard → Settings → Environment Variables |
| Build fails | Node version mismatch | Set `engines.node` in package.json, or use Vercel settings |
| OAuth callbacks broken | Wrong redirect URI | Update OAuth provider with deployed domain |
| CORS errors | API on different origin | Configure CORS in server hooks or API routes |
| Functions timeout | Cold start or heavy computation | Increase `maxDuration` in vercel.json, optimize code |
| `adapter-auto` not detected | Missing vercel.json | Usually works without it; if not, `npm i @sveltejs/adapter-vercel` explicitly |

---

## Anti-Patterns

### The Framework Overkill

**Pattern:** User asks for a calculator. You scaffold a SvelteKit app with routing, a database, and auth.

**Reality:** A single HTML file with 50 lines of JavaScript is the correct answer. The user gets their calculator in 2 minutes instead of 20.

**Fix:** Use the decision tree. If it fits on one screen with no persistence, it's a single HTML file. Always.

### The Infinite PRD

**Pattern:** Spending 30 minutes refining user stories for a weekend project. Asking 15 clarifying questions before writing a line of code.

**Reality:** Some projects need a one-line spec: "Build a pomodoro timer, dark theme, deploys to GitHub Pages." Done.

**Fix:** Scale PRD effort to project complexity. Toy project = 1-paragraph spec. Production app = full PRD with stories. If in doubt, scaffold the foundation and show it — feedback on a working prototype beats feedback on a document.

### The Deployment Afterthought

**Pattern:** Building everything locally, then discovering the app can't deploy because it depends on local file paths, localhost URLs, or missing environment variables.

**Reality:** If it doesn't deploy, it doesn't exist.

**Fix:** Deploy the scaffold (empty app) in Stage 1 before building features. Catch deployment issues when they're cheap to fix. Every feature story should work in the deployed environment, not just localhost.

### The Style Drift

**Pattern:** Start with a clean design system. Skeleton components, consistent spacing, design tokens. By feature 5, there are inline styles, hardcoded colors, and three different button variants.

**Reality:** Every new component is an opportunity to break visual consistency.

**Fix:** Define the design system in the PRD. Reference it in every feature story. When adding a component, check if an existing component already handles this pattern. Never add a new color or spacing value without updating the design tokens.

---

## Error Handling

1. **Diagnose** — Read the actual error, don't guess
2. **Categorize** — dependency / type / test / network / deploy
3. **Retry** — Up to 3 attempts with targeted fixes
4. **Escalate** — Show the user the error and what was tried

**Never leave the project broken.** If staging or production fails, the dev branch still works.

---

## Quick Reference Card

```
DECIDE:    One screen, no persistence? → Single HTML
           Multiple pages or server logic? → SvelteKit
           Docs/landing/portfolio? → Static site

SCAFFOLD:  pnpx sv create [name]
           pnpx sv add [addon]
           pnpm install

BUILD:     pnpm dev          # Local server
           pnpm check        # TypeScript
           pnpm test         # Unit tests
           pnpm test:e2e     # E2E tests
           pnpm build        # Production build

DEPLOY:    vercel             # Preview
           vercel --prod      # Production
           gh-pages branch    # GitHub Pages

PRD:       Gather → Plan → Iterate → Preflight → Execute → Handoff
           CHECKPOINT at foundation (step 4) — always pause for review

DESIGN:    Capture preferences early. Enforce throughout.
           Never add colors/spacing outside the design system.

BUNDLE:    npx html-inline dist/index.html -o bundle.html
           All assets base64-inlined. No CDN dependencies.
```

## Platform-Specific Patterns

### OpenClaw Control-UI Customization

The `gateway.controlUi.root` config option copies the control-ui to `~/.openclaw/control-ui/` so customizations survive npm updates. To customize:

1. Set `gateway.controlUi.root` in config to trigger the copy
2. Add `custom.css` and `custom.js` to `~/.openclaw/control-ui/`
3. Patch `index.html` to load them (`<link>` and `<script>` tags)
4. Changes persist across OpenClaw updates since the files live outside `node_modules`

### MutationObserver for Thinking Indicators

When building UIs that need to detect agent processing state (e.g., showing an elapsed timer while the agent thinks):

```js
const observer = new MutationObserver((mutations) => {
  // Watch for DOM changes that indicate agent is processing
  // Show/hide elapsed timer based on state transitions
});
observer.observe(targetNode, { childList: true, subtree: true });
```

This pattern is useful for any real-time UI that wraps an async agent interaction.

## Cross-Skill Integration

- **cloudflare-deploy** → Push static builds to CF Pages
- **devops** → CI/CD pipeline for automated builds
- **security** → CSP headers, dependency audit
- **task-planner** → Kanban HTML dashboard generation
- **data-analysis** → Self-contained HTML dashboards
