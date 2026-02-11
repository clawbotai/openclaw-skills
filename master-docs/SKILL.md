# Master Documentation

Generate comprehensive, layperson-friendly documentation for any codebase — inline comments, CLI help systems, reference docs, and quality audits.

---

## Why This Exists

Good documentation is the difference between a project someone can use and a project that dies in obscurity. But writing docs is tedious, so they rot. This skill treats documentation like a first-class deliverable: auto-generated, always current, and written for humans — not just other programmers.

**Philosophy:** Explain code like you're talking to a smart friend who isn't a programmer. Cover the WHY, not just the WHAT.

---

## Foundations

This skill draws from established documentation theory and adapts it for AI-assisted workflows:

### Diátaxis Framework

All documentation falls into four categories. Know which one you're writing:

| Type | Purpose | Example |
|------|---------|---------|
| **Tutorial** | Learning-oriented, hands-on | "Build your first widget" |
| **How-to** | Task-oriented, practical | "How to deploy to production" |
| **Reference** | Information-oriented, exact | "API endpoint list with parameters" |
| **Explanation** | Understanding-oriented, conceptual | "Why we chose event sourcing" |

Most codebases over-index on reference and under-index on explanation. This skill balances all four.

### Literate Programming (Knuth)

Code should read like a narrative. When you can't make the code self-explanatory, comments fill the gap — not describing *what* the code does (the code already says that), but *why* it does it and *how* it connects to the bigger picture.

### Docs-as-Code

Documentation lives next to code, versioned together, reviewed together, tested together. If the docs aren't in the repo, they don't exist.

### Living Documentation

Auto-generated docs that stay current with the code. No "last updated 2019" README files. Scripts in this skill can re-run anytime to refresh docs.

---

## Modes

### 1. Inline Documentation Mode

Analyzes every file in a project and adds narrative comments explaining:
- **Purpose** of each file, section, function, and critical line
- **Why** decisions were made (not just what the code does)
- **How** pieces connect to each other and the broader system
- Written so a non-programmer can follow the intent and flow

**Rules:**
- Follows language-appropriate conventions (JSDoc for JS/TS, docstrings for Python, GoDoc for Go, `///` for Rust)
- Preserves all original code — only adds documentation
- Uses section headers to create a narrative flow through the file
- Explains magic numbers, regex patterns, non-obvious logic
- Links related functions/files when relevant

**Language conventions:**

| Language | Style | Example |
|----------|-------|---------|
| JavaScript/TypeScript | JSDoc (`/** */`) | `/** Validates user input before saving to DB. Returns null if invalid. */` |
| Python | Google-style docstrings | `"""Validates user input before saving to DB.\n\nArgs:\n    data: Raw form submission dict\n"""` |
| Go | GoDoc (comment above func) | `// ValidateUser checks input constraints before persistence.` |
| Rust | `///` doc comments | `/// Validates user input before saving to DB.` |
| Shell/Bash | `#` with section headers | `# --- Validation ---\n# Make sure the user provided a valid email` |

### 2. Reference Documentation Mode

Generates complete command/function references:
- Every public function, class, method, CLI command
- All parameters with types, defaults, and constraints
- Return values and error conditions
- At least one usage example per function
- Edge cases and gotchas

Output format: Markdown files using the `templates/function-reference.md` template.

### 3. Help System Mode

Generates `--help` output for shell scripts and CLI tools following POSIX and modern conventions:

**Standard help structure:**
```
NAME
    tool-name — one-line description

SYNOPSIS
    tool-name [OPTIONS] <required-arg> [optional-arg]

DESCRIPTION
    What this tool does, in plain language. A paragraph or two
    covering the main use case and any important context.

OPTIONS
    -h, --help          Show this help message and exit
    -v, --verbose       Enable verbose output
    -o, --output FILE   Write output to FILE (default: stdout)

EXAMPLES
    tool-name input.txt
        Process input.txt with default settings

    tool-name -v -o result.txt input.txt
        Process with verbose output, write to result.txt

EXIT STATUS
    0   Success
    1   General error
    2   Invalid arguments
```

**Implementation:** The `inject-help.sh` script adds a `show_help()` function and `--help`/`-h` flag parsing to any shell script automatically.

### 4. Project Overview Mode

Generates high-level architectural documentation:
- What the project does (one paragraph)
- Architecture diagram (text-based)
- Key components and how they connect
- Data flow description
- Dependencies and requirements
- Getting started guide

Output format: Markdown using `templates/project-overview.md` template.

### 5. Documentation Quality Scoring

Audits a project's documentation health and outputs a score (0–100):

| Check | Weight | What it measures |
|-------|--------|-----------------|
| README exists | 15 | Does the project have a README? |
| README quality | 10 | Has description, usage, examples? |
| Inline comment ratio | 20 | % of code files with meaningful comments |
| Docstrings/JSDoc | 20 | % of functions with doc comments |
| --help support | 15 | % of shell scripts responding to --help |
| CHANGELOG exists | 5 | Version history present? |
| Examples present | 15 | Do docs include usage examples? |

**Exit codes:** 0 (score ≥ 80), 1 (50–79), 2 (< 50)

---

## Workflows

### "Document this skill"

Full inline + reference documentation for a skill directory:

```bash
bash skills/master-docs/scripts/document.sh ./skills/my-skill inline
bash skills/master-docs/scripts/document.sh ./skills/my-skill reference
```

### "Document this project"

Full project documentation (overview + inline + reference):

```bash
bash skills/master-docs/scripts/document.sh ./my-project overview
bash skills/master-docs/scripts/document.sh ./my-project inline
bash skills/master-docs/scripts/document.sh ./my-project reference
```

### "Add help to scripts"

Inject `--help` into all shell scripts:

```bash
bash skills/master-docs/scripts/inject-help.sh ./scripts/
# Or a single file:
bash skills/master-docs/scripts/inject-help.sh ./scripts/deploy.sh
```

### "Score documentation"

Quality audit with improvement suggestions:

```bash
bash skills/master-docs/scripts/score-docs.sh ./my-project
```

### "Generate README"

Auto-generate a README from code analysis (AI-assisted — provide this skill as context and ask the agent to generate a README for a target project).

---

## Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/document.sh` | Main documentation dispatcher | `bash document.sh <path> <mode>` |
| `scripts/inject-help.sh` | Inject --help into shell scripts | `bash inject-help.sh <path>` |
| `scripts/score-docs.sh` | Documentation quality audit | `bash score-docs.sh <path>` |

All scripts support `--help` for detailed usage.

---

## Templates

| Template | Use for |
|----------|---------|
| `templates/function-reference.md` | Documenting functions and commands |
| `templates/project-overview.md` | High-level project documentation |
| `templates/inline-guide.md` | Guide for writing good inline docs |

---

## AI-Optimized Documentation Tips

When writing docs that LLMs will consume (like SKILL.md files, AGENTS.md):

1. **Use structured headers** — LLMs navigate by headings
2. **Include examples** — Models learn patterns from examples better than rules
3. **Be explicit** — Don't rely on context that might be outside the model's window
4. **Use tables for structured data** — Easier to parse than nested lists
5. **Mark boundaries clearly** — `---` separators, section headers, code fences
6. **Front-load the important stuff** — Purpose and key info first, details after
