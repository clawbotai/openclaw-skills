---
name: master-docs
description: Documentation engine with Diátaxis scaffolding, GitHub Gold Standard templates, strict quality scoring, and active documentation generation.
---

# Master Documentation v2.0 📚

An active **Documentation Engine** — not a passive analyzer. Scaffolds a complete documentation structure from scratch, enforces the GitHub Gold Standard, and scores quality with real teeth.

**Philosophy:** Documentation is a product feature, not an afterthought. If it isn't scaffolded on day one, it never gets written.

---

## The GitHub Gold Standard

Every project and skill managed by this system MUST have these artifacts. No exceptions.

### Root Files (Required)

| File | Purpose | Standard |
|------|---------|----------|
| `README.md` | Front door of the project | Badges, one-liner, quick start, documentation index |
| `CONTRIBUTING.md` | How to contribute | Fork → Branch → Commit → PR workflow, Conventional Commits |
| `CHANGELOG.md` | Version history | [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format + SemVer |
| `LICENSE` | Legal terms | SPDX identifier, full license text |

### Documentation Structure (Required for projects, recommended for skills)

```
docs/
├── tutorials/          Learning-oriented: "Build your first X"
│   └── getting-started.md
├── how-to/             Problem-oriented: "How to configure Y"
│   └── .gitkeep
├── reference/          Information-oriented: API docs, CLI reference
│   └── .gitkeep
└── explanations/       Understanding-oriented: "Why we chose Z"
    └── .gitkeep
```

This structure implements the **Diátaxis framework** — the industry standard for organizing technical documentation, used by Django, Canonical/Ubuntu, Cloudflare, Gatsby, and NumPy.

---

## Diátaxis Framework

Four types of documentation, each serving a fundamentally different need. Mixing them is the #1 cause of bad docs.

```
                    PRACTICAL                          THEORETICAL
              ┌──────────────────┐              ┌──────────────────┐
  LEARNING    │   TUTORIALS      │              │  EXPLANATIONS    │
  (study)     │                  │              │                  │
              │  "Follow me and  │              │  "Here's why     │
              │   we'll build X" │              │   things work    │
              │                  │              │   this way"      │
              │  → Learning by   │              │  → Understanding │
              │    doing         │              │    context       │
              └──────────────────┘              └──────────────────┘

              ┌──────────────────┐              ┌──────────────────┐
  WORKING     │   HOW-TO GUIDES  │              │   REFERENCE      │
  (work)      │                  │              │                  │
              │  "To achieve X,  │              │  "Class Foo      │
              │   do 1, 2, 3"   │              │   accepts args   │
              │                  │              │   bar, baz"      │
              │  → Solving       │              │  → Precise       │
              │    problems      │              │    information   │
              └──────────────────┘              └──────────────────┘
```

### Key Rules

1. **Never mix types in one document.** A tutorial that suddenly becomes a reference is bad at both.
2. **Tutorials take the reader's hand.** The instructor is responsible for success. Every step must work.
3. **How-tos assume competence.** The reader knows the basics; they need to solve a specific problem.
4. **Reference is neutral.** No opinions, no guidance — just accurate, complete facts.
5. **Explanations give context.** Why decisions were made, how things connect, trade-offs considered.

### Placing Your Documentation

| You're writing... | Put it in... | Test: Does it... |
|-------------------|-------------|-------------------|
| A walkthrough for beginners | `docs/tutorials/` | Take the reader from zero to a working result? |
| Steps to accomplish a task | `docs/how-to/` | Solve a specific real-world problem? |
| API/CLI/config reference | `docs/reference/` | Describe things accurately and completely? |
| Architecture decisions, design rationale | `docs/explanations/` | Help the reader understand WHY? |

---

## Modes

### 1. Scaffold Mode (NEW in v2.0)

The flagship feature. Creates the entire Gold Standard structure from templates in one command.

```bash
bash scripts/document.sh <path> scaffold
```

**What it does:**
1. Creates `docs/{tutorials,how-to,reference,explanations}/` with starter files
2. Checks for missing root files (`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`)
3. Copies templates for any missing files — customized with the project name
4. Reports what was created vs. what already existed
5. Never overwrites existing files

**When to use:**
- Starting a new project
- Bringing an existing project up to Gold Standard
- After `scaffold.sh` from project-structure (adds docs layer on top)

### 2. Inline Documentation Mode

Analyzes source files and reports inline comment coverage by language.

```bash
bash scripts/document.sh <path> inline [-v]
```

Reports per-file comment percentage, total coverage, and identifies files that need attention. Supports: Python, JavaScript/TypeScript, Go, Rust, Ruby, Java, Shell.

### 3. Reference Documentation Mode

Scans source code and generates function/command reference skeletons.

```bash
bash scripts/document.sh <path> reference [-o docs/reference/api.md]
```

Extracts: shell functions, Python `def`s, JS/TS exports. Outputs Markdown with parameter tables, return types, and example placeholders.

### 4. Help System Mode

Injects `--help` support into shell scripts following POSIX conventions.

```bash
bash scripts/document.sh <path> help
# Or directly:
bash scripts/inject-help.sh <path>
```

Adds `show_help()` function + `--help`/`-h` flag parsing. Skips scripts that already have help. Uses standard NAME/SYNOPSIS/DESCRIPTION/OPTIONS/EXAMPLES/EXIT STATUS format.

### 5. Project Overview Mode

Generates an architectural overview from directory analysis.

```bash
bash scripts/document.sh <path> overview [-o docs/explanations/architecture.md]
```

Detects languages, key files, directory structure. Outputs a skeleton with TODO sections for components, data flow, and getting started.

### 6. Documentation Quality Score (v2.0 — Stricter)

Audits documentation health. Scoring redesigned with stricter criteria and new Gold Standard checks.

```bash
bash scripts/document.sh <path> score
# Or directly:
bash scripts/score-docs.sh <path> [--json] [-q]
```

---

## Scoring System (v2.0)

Total: 100 points. Deductions for missing Gold Standard artifacts.

| Check | Points | Criteria |
|-------|--------|----------|
| README/SKILL.md exists | 10 | Must exist and be ≥10 lines |
| README quality | 10 | Has description (≥20 chars), code examples, ≥3 sections |
| README not template | 0 / -10 | **PENALTY** if still contains `[Project Name]` or `TODO:` placeholder text |
| CONTRIBUTING.md | 10 | Must exist |
| CHANGELOG.md | 10 | Must exist |
| Diátaxis docs/ structure | 10 | Must have `docs/` with ≥2 of the 4 subdirectories |
| Inline comment ratio | 15 | % of source files with ≥5% comment lines |
| Docstrings/JSDoc | 15 | % of functions with doc comments |
| --help in scripts | 10 | % of shell scripts with `--help` support |
| Examples in docs | 10 | % of Markdown files containing code blocks |

**Ratings:**
- ★★★★★ EXCELLENT: ≥85
- ★★★★☆ GOOD: 70-84
- ★★★☆☆ FAIR: 55-69
- ★★☆☆☆ POOR: 40-54
- ★☆☆☆☆ FAILING: <40

**Exit codes:** 0 (≥80), 1 (50-79), 2 (<50)

---

## Templates

### README.md Template

Professional README with:
- Shields.io badges (version, license, build status)
- One-line description + longer overview
- Quick Start (install → configure → run)
- Documentation index linking to Diátaxis folders
- Contributing link, license, acknowledgments

### CONTRIBUTING.md Template

Standard open-source contribution guide:
- Prerequisites and setup
- Fork → Branch → Commit → PR workflow
- Conventional Commits specification
- Code style and testing requirements
- Issue and PR templates guidance
- Code of Conduct reference

### CHANGELOG.md Template

[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format:
- Unreleased section for staging
- Version sections with dates
- Categories: Added, Changed, Deprecated, Removed, Fixed, Security
- SemVer adherence note

### Diátaxis Starter Files

- `docs/tutorials/getting-started.md` — Tutorial template with step-by-step structure
- `docs/how-to/.gitkeep`, `docs/reference/.gitkeep`, `docs/explanations/.gitkeep` — Directory stubs

---

## Scripts Reference

| Script | Purpose | Modes |
|--------|---------|-------|
| `scripts/document.sh` | Main dispatcher | scaffold, inline, reference, help, overview, score |
| `scripts/inject-help.sh` | Inject --help into .sh files | (standalone) |
| `scripts/score-docs.sh` | Quality audit with scoring | (standalone, --json, -q) |

All scripts support `--help` for detailed usage.

---

## Workflows

### "Set up a new project's docs"
```bash
# 1. Scaffold the Gold Standard
bash scripts/document.sh ./my-project scaffold

# 2. Check the score
bash scripts/document.sh ./my-project score

# 3. Edit the generated templates — replace TODOs with real content
```

### "Bring an existing project up to standard"
```bash
# 1. Score current state
bash scripts/document.sh ./my-project score

# 2. Scaffold missing pieces (won't overwrite existing files)
bash scripts/document.sh ./my-project scaffold

# 3. Generate reference docs
bash scripts/document.sh -o docs/reference/api.md ./my-project reference

# 4. Add --help to scripts
bash scripts/document.sh ./my-project help

# 5. Re-score
bash scripts/document.sh ./my-project score
```

### "Audit all skills"
```bash
for skill in skills/*/; do
    score=$(bash scripts/score-docs.sh -q "$skill" 2>/dev/null || echo "ERR")
    printf "%-40s %s\n" "$(basename "$skill")" "$score"
done | sort -t' ' -k2 -n
```

---

## Theoretical Foundations

| Theory | Application in This Skill |
|--------|--------------------------|
| **Diátaxis** (Procida) | docs/ folder structure: tutorials, how-to, reference, explanations |
| **Keep a Changelog** (Langlois) | CHANGELOG.md format with SemVer |
| **Conventional Commits** | CONTRIBUTING.md commit message standard |
| **Literate Programming** (Knuth) | Inline mode: code as narrative, explain WHY not WHAT |
| **Docs-as-Code** (Gentle) | Everything in the repo, versioned with git |
| **Living Documentation** (Martraire) | Scaffold + score = generate early, audit continuously |
| **README Driven Development** (Holman) | README template forces you to describe the product before building it |
| **Developer Experience (DX)** | Badges, quick start, copy-pasteable examples reduce time-to-first-success |

---

## AI-Optimized Documentation Tips

When writing docs that LLMs will consume (SKILL.md, AGENTS.md, prompts):

1. **Structured headers** — LLMs navigate by headings
2. **Tables over nested lists** — Easier to parse and reference
3. **Examples over rules** — Models learn patterns from examples
4. **Explicit > implicit** — Don't rely on context outside the window
5. **Front-load key info** — Purpose and usage first, theory after
6. **Clear boundaries** — `---` separators, code fences, section breaks
