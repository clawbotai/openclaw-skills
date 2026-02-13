---
name: web-builder
description: Full web development lifecycle — scaffold SvelteKit PWAs, bundle single-file HTML apps, and deploy to GitHub Pages or Vercel. Use when building any web application, static site, or HTML artifact.
---

# Web Builder

Full web development lifecycle skill covering three main use cases: SvelteKit full-stack apps, single-file HTML bundling, and static site deployment to GitHub Pages or Vercel.

## Overview

Use this skill when:
- Building a new web application (SvelteKit PWA)
- Creating a self-contained single HTML file (games, demos, artifacts)
- Deploying a static site to GitHub Pages
- Deploying any web app to Vercel

**Choose your path:**

| Use Case | Section |
|----------|---------|
| Full web app with routing, state, DB | [SvelteKit Apps](#sveltekit-apps) |
| Single-file HTML game/demo/artifact | [Single HTML Bundling](#single-html-bundling) |
| Deploy static site to GitHub Pages | [GitHub Pages Deploy](#github-pages-deploy) |
| Deploy SvelteKit app to Vercel | [Vercel Deploy](#vercel-deploy) |

---

## SvelteKit Apps

Scaffold production-ready SvelteKit PWAs with opinionated defaults and autonomous execution.

### Quick Start

1. **Describe your app** — Tell me what you want to build
2. **Review the PRD** — I'll generate a plan with user stories
3. **Approve** — I build, test, and deploy autonomously
4. **Done** — Get a live URL + admin documentation

> "Build me a task tracker with due dates and priority labels"

That's all I need to start.

### Prerequisites

| CLI | Purpose | Install |
|-----|---------|---------|
| `sv` | SvelteKit scaffolding | `npm i -g sv` (or use via `pnpx`) |
| `pnpm` | Package manager | `npm i -g pnpm` |
| `gh` | GitHub repo creation | [cli.github.com](https://cli.github.com) |
| `vercel` | Deployment | `npm i -g vercel` |

### Opinionated Defaults

- **Component library:** Skeleton (Svelte 5 native) + Bits UI fallback
- **Package manager:** pnpm
- **Deployment:** Vercel
- **Add-ons:** ESLint, Prettier, Vitest, Playwright, mdsvex, MCP
- **State:** Svelte 5 runes ($state, $derived, $effect)

All defaults can be overridden via `SKILL-CONFIG.json`.

### User Configuration

Check `~/.openclaw/workspace/SKILL-CONFIG.json` for user-specific defaults before using skill defaults. User config overrides skill defaults for:
- Deployment provider (e.g., vercel, cloudflare, netlify)
- Package manager (pnpm, npm, yarn)
- Add-ons to always include
- MCP IDE configuration
- Component library preferences

### Workflow

1. **Gather**: Freeform description + design references + targeted follow-ups
2. **Plan**: Generate complete PRD (scaffold, configure, features, tests as stories)
3. **Iterate**: Refine PRD with user until confirmed
4. **Preflight**: Verify all required auths and credentials
5. **Execute**: Autonomous build-deploy-verify cycle (development → staging → production)

#### Phase 1: Gather Project Description

Start with an open question: "What do you want to build?"

Ask for design inspiration (1–3 reference sites). Then fill gaps with targeted follow-ups:

| Gap | Question |
|-----|----------|
| Users unclear | "Who's the primary user?" |
| Core action unclear | "What's the ONE thing they must be able to do?" |
| Scale unknown | "How many users do you expect?" |

Confirm understanding with a structured summary before proceeding.

#### Phase 2: Generate PRD

**Technical Stack (always included):**
```
CLI:              pnpx sv
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
```

**Inferred from description:**
- `drizzle` → if needs database
- `lucia` → if needs auth
- `paraglide` → if needs i18n

**User stories** in `prd.json` — each story must fit in one context window. Standard sequence:
1. Scaffold → 2. Configure → 3. Mock Data → 4. Foundation (INDEX PAGE CHECKPOINT — pause for user review) → 5. Features → 6. Infrastructure → 7. Polish → 8. Tests

#### Phase 3: Iterate Until Confirmed

Present PRD, refine until user explicitly approves.

#### Phase 4: Preflight

```bash
gh auth status 2>/dev/null && echo "✓ GitHub" || echo "✗ GitHub"
command -v pnpm &>/dev/null && echo "✓ pnpm" || echo "⚠ pnpm (will use npm)"
vercel whoami 2>/dev/null && echo "✓ Vercel" || echo "✗ Vercel"
```

Development can start with mocks; staging needs real credentials.

#### Phase 5: Execute

Three stages:
- **Stage 1: Development** — Local, dev branch, mock data. Execute stories via sub-agents in parallel waves. Exit criteria: `pnpm check && pnpm test && pnpm test:e2e`
- **Stage 2: Staging** — Main branch, Vercel preview URL, real data. Fix environment issues with smart retry (3 attempts).
- **Stage 3: Production** — `vercel --prod`, final E2E verification.

#### Phase 6: Handoff

Generate `ADMIN.md` with: local dev instructions, env vars, project structure, adding pages, DB migrations, deployment workflow, troubleshooting.

### State Management

- `$state()` runes for reactive state
- `$derived()` for computed values
- Context API (`setContext`/`getContext`) for cross-component state
- Server state through `load` functions → `data` prop
- **Never** store user-specific state in module-level variables

### Code Style

- Prefer `bind:` over callbacks
- `$effect()` over `onMount`
- Runes everywhere
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

### Error Handling

1. Diagnose → 2. Categorize (dependency/type/test/network) → 3. Retry (up to 3) → 4. Escalate to user

**Never leave the project broken.** If Stage 2/3 fails, dev branch still works.

### Quick Reference

```bash
pnpx sv create [name]   # Scaffold
pnpx sv add [addon]     # Add functionality
pnpm check              # TypeScript check
pnpm test               # Unit tests
pnpm test:e2e           # E2E tests
pnpm build              # Production build
```

### Default Adapter

`adapter-auto` detects: Vercel, Cloudflare, Netlify, or falls back to adapter-node.

### Database Options (drizzle)
- PostgreSQL + postgres.js or neon
- SQLite + better-sqlite3 or libsql
- Turso + @libsql/client

---

## Single HTML Bundling

Bundle web applications into a single self-contained HTML file for distribution.

### When to Use

- Telegram Mini App games
- itch.io HTML5 games
- Single-file demos/prototypes
- Portfolio artifacts
- Any context requiring offline-capable single-file delivery

### Bundling Patterns

#### Simple (No Framework)

If already a single HTML file, just inline everything:
- CSS inside `<style>` tags
- JS inside `<script>` tags
- Images as base64 data URIs

#### React/Vite App → Single HTML

**Stack:** React 18 + TypeScript + Vite + Parcel + Tailwind CSS

```bash
# 1. Build with Vite
npm run build

# 2. Bundle into single file with Parcel
npx parcel build dist/index.html --no-source-maps

# 3. Inline all assets
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

<!-- Audio → base64 (small sound effects only) -->
<audio src="data:audio/mp3;base64,..."></audio>
```

### Distribution Checklist

- [ ] Bundled into single HTML file
- [ ] No external CDN dependencies (works offline)
- [ ] Mobile touch support (for Telegram Mini App)
- [ ] Safe-area considerations (WebView environments)
- [ ] File size optimized (compressed images, minified code)
- [ ] No console errors

### Distribution Channels

1. **Telegram Mini App** — Host on your domain
2. **itch.io** — Upload HTML file directly
3. **GitHub Pages** — Push to repo (see [GitHub Pages Deploy](#github-pages-deploy))
4. **CrazyGames/Poki** — Check platform requirements

---

## GitHub Pages Deploy

Create and deploy static websites to GitHub Pages with automated workflows.

### Quick Workflow

```bash
# 1. Initialize project structure
bash scripts/init_project.sh <project-name>

# 2. Build your site (see templates in assets/templates/)

# 3. Deploy to GitHub Pages
bash scripts/deploy_github_pages.sh <project-name> <github-username>
```

### Project Structure (generated)

```
project-name/
├── index.html
├── styles.css
├── script.js
├── README.md
└── .github/
    └── workflows/
        └── deploy.yml
```

### Templates

Available in `assets/templates/`:
- `base-html/` — Minimal HTML5 boilerplate
- `portfolio/` — Portfolio/CV template with sections
- `landing/` — Landing page with hero and CTA

### Development Principles

- **Single-page first**: One-page layouts unless multiple pages explicitly required
- **No dependencies**: Pure HTML/CSS/JS when possible
- **Modern CSS**: Flexbox, Grid, responsive design, dark mode support
- **Semantic HTML5**: Proper elements, meta tags for SEO/social sharing
- **Performance**: Optimized images, minified assets, lazy loading

### Deployment

GitHub Actions automatically deploys on push to main:
- Deploys to `gh-pages` branch
- Live at `https://<username>.github.io/<project-name>/`

### Troubleshooting

- **Not deploying**: Check Settings → Pages → Source is `gh-pages` branch
- **Permission errors**: Run `gh auth status` to verify authentication
- **Build failures**: Review Actions logs, verify workflow YAML syntax

### Scripts

- `scripts/init_project.sh` — Initialize project structure with GitHub Actions workflow
- `scripts/deploy_github_pages.sh` — Create GitHub repo and deploy to Pages

### References

- `references/workflow.md` — Detailed workflow documentation
- `references/design-patterns.md` — Design best practices

---

## Vercel Deploy

Deploy SvelteKit apps (or any static site) to Vercel.

### Prerequisites

```bash
npm i -g vercel
vercel login
```

### Deploy Flow

```bash
# Link project to Vercel
vercel link

# Deploy to preview
vercel

# Deploy to production
vercel --prod

# Custom domain (optional)
vercel domains add <domain>
```

### Environment Variables

Set in Vercel dashboard or via CLI:
```bash
vercel env add DATABASE_URL production
```

### Common Issues

- **OAuth callbacks**: Must match deployed domain
- **CORS**: Configure for deployed environment
- **Env vars**: Ensure all are set in Vercel dashboard
- **API endpoints**: Don't use localhost in production

### SvelteKit Adapter

Use `adapter-auto` — automatically detects Vercel and uses `adapter-vercel`. No manual configuration needed.
