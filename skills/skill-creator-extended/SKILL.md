---
name: skill-creator-extended
description: Autonomous skill generator — creates complete OpenClaw skills from a natural-language prompt via a 4-phase LLM pipeline (Research → Architecture → Implementation → Validation). Use when building a new skill from a description.
---

# Skill Creator Extended

Building skills from scratch costs 50–200K tokens. This tool automates the scaffolding — researching patterns, designing the architecture, generating code, and validating the output — all from a single prompt. But the quality of the output is directly proportional to the quality of the input. A vague prompt produces a vague skill. A precise prompt with explicit constraints produces something you can actually use.

This tool is for **scaffolding**, not architecture. It generates a working starting point. Complex systems (monitoring pipelines, multi-phase workflows, anything with intricate state management) need hand-crafting. Use this to get 70% of the way there, then refine.

---

## Quick Start

```bash
python3 scripts/architect_skill.py \
  --prompt "Build a skill for parsing financial PDFs and extracting line items into structured JSON" \
  --output-path ./skills
```

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--prompt, -p` | *required* | Natural-language skill description |
| `--model, -m` | `gpt-4o` | OpenAI model to use |
| `--output-path, -o` | `./skills` | Parent directory for generated skill |
| `--max-retries` | `3` | Max retries for API calls and validation |
| `--verbose, -v` | off | Enable debug logging |

**Requires:** `OPENAI_API_KEY` environment variable.

---

## The Four Phases

### Phase 1: Research (Senior Researcher)

**What happens:** DuckDuckGo searches for relevant libraries, patterns, and prior art. An LLM synthesizes findings into a structured report: recommended libraries, design patterns, risks, and constraints.

**What can go wrong:**
- Search returns outdated or irrelevant results → the skill recommends deprecated libraries
- Constraint extraction misses implicit requirements → generated code violates workspace rules
- Research is too shallow for niche domains → generic patterns applied to specific problems

**Your lever:** Be explicit about constraints in the prompt. "stdlib-only", "Python 3.9", "no external APIs" — these are extracted and enforced across all subsequent phases.

### Phase 2: Architecture (Principal Architect)

**What happens:** Evaluates four OpenClaw skill structures (Workflow, Task, Reference, Capabilities) and picks the best fit. Produces a complete SKILL.md with real content — not TODOs — and a file manifest for scripts/ and references/.

**What can go wrong:**
- Wrong structure type selected → a Reference skill when you needed a Workflow
- SKILL.md is too generic → reads like a template, not a protocol
- File manifest is over-scoped → plans for 10 scripts when 3 would do

**Your lever:** State the skill type explicitly if you know it. "This should be a Workflow skill with 3 phases" gives better results than letting the model guess.

### Phase 3: Implementation (Senior Developer)

**What happens:** Scaffolds the skill directory, generates each script via separate LLM calls (structured output), generates reference docs, and aggregates dependencies into requirements.txt.

**What can go wrong:**
- Each script is generated in isolation → they don't share types or interfaces cleanly
- Generated code pulls in unnecessary dependencies → bloated requirements.txt
- Scripts are ~300 LOC each (GPT-4o limit) → may be insufficient for complex logic
- Reference docs are plausible but inaccurate → LLM hallucination in documentation

**Your lever:** Keep individual scripts focused. A prompt asking for "one script that does everything" produces worse results than "three scripts with clear responsibilities."

### Phase 4: Validation & Self-Correction (Code Reviewer)

**What happens:** Runs `quick_validate.py` on the generated skill. On failure, feeds the error back to a reviewer LLM for correction. Retries up to N times.

**What can go wrong:**
- Validation catches structural issues but not logic errors → skill passes validation but doesn't actually work
- Self-correction loops can diverge → fix one issue, introduce another
- Validation is syntactic, not semantic → a valid YAML frontmatter doesn't mean the skill makes sense

**Your lever:** Treat validation as a gate, not a guarantee. Always review the output yourself.

---

## Prompt Engineering for Skills

The prompt is the most important input. Here's what makes a good one:

### Good Prompt Anatomy

```
"Build a skill for [WHAT] that [HOW/CONSTRAINTS].
It should [KEY BEHAVIORS].
Use [SPECIFIC TOOLS/LIBRARIES] if applicable.
Output format: [EXPECTED OUTPUT]."
```

### Examples

**Weak:** "Build a skill for working with APIs"
→ Too vague. Which APIs? What operations? What output?

**Strong:** "Build a skill for making authenticated REST API calls with retry logic. Should support Bearer token and API key auth. Use httpx for async requests. Include rate limiting (respect Retry-After headers). Output structured response objects with status, headers, and parsed JSON body."

### Principles

1. **Scope explicitly.** "Parsing PDFs" is vague. "Extracting tables from PDF invoices into CSV" is specific.
2. **State constraints up front.** "stdlib-only", "Python 3.9", "no network access" — these shape every phase.
3. **Name the outputs.** "Produces a JSON report" beats "processes data."
4. **Provide examples** of desired behavior when possible.
5. **Set boundaries.** "This skill does NOT handle X" prevents scope creep.

---

## When NOT to Use This

| Situation | Why | What Instead |
|-----------|-----|-------------|
| Complex multi-phase systems (monitoring, lifecycle) | Too much interdependent state | Hand-craft the architecture, use this for individual scripts |
| Skills that wrap specific APIs with auth | Generated auth code is usually wrong | Write the auth integration manually |
| Skills requiring precise error handling | Generated error handling is generic | Scaffold structure, then rewrite error paths |
| Rebuilding/improving an existing skill | Tool doesn't read existing code | Edit the skill directly |
| Skills under 50 lines | Overhead exceeds value | Just write it |

---

## Constraints System

Constraints are extracted automatically from the prompt and enforced across all phases:

| Constraint Phrase | Effect |
|-------------------|--------|
| "stdlib-only" / "no dependencies" | Blocks external library recommendations |
| "Python 3.9" | Enforces version-compatible syntax |
| "JSON output" / "structured JSON" | Enforces output format |
| "no network" / "offline" | Blocks API-dependent patterns |

---

## Post-Generation Checklist

Run through this after every generation. Do not skip items.

- [ ] **Read the SKILL.md entirely.** Does it describe what you actually wanted?
- [ ] **Check the frontmatter.** Only `name` and `description` — nothing else.
- [ ] **Review each script.** Do they share consistent types/interfaces?
- [ ] **Check imports.** Any unnecessary dependencies? Any missing ones?
- [ ] **Test the happy path.** Run the main script with sample input.
- [ ] **Test an error path.** Feed it bad input. Does it fail gracefully?
- [ ] **Check Python 3.9 compat.** Search for `X | None`, `match/case`, `type X = ...`
- [ ] **Review requirements.txt.** Pin versions. Remove unused packages.
- [ ] **Check reference docs.** Are they accurate or hallucinated?
- [ ] **Run validation:** `python3 scripts/quick_validate.py skills/<name>`

---

## Anti-Patterns

### The Vague Prompt

**Pattern:** "Build a skill for data processing."

**Reality:** Garbage in, garbage out. The generator produces a generic skill that processes undefined data in undefined ways with undefined outputs.

**Fix:** Specify the data format, the processing steps, the output format, and the error cases. Every ambiguity in the prompt becomes a coin flip in the output.

### The Kitchen Sink

**Pattern:** "Build a skill that handles API calls, database operations, file parsing, email sending, and report generation."

**Reality:** The generator produces shallow implementations of five things instead of a deep implementation of one thing. Each script is 100 lines of boilerplate.

**Fix:** One skill, one responsibility. If you need five capabilities, generate five skills and compose them.

### The Trust Without Verify

**Pattern:** Generate a skill, see it passes validation, ship it without reading the code.

**Reality:** Validation checks structure, not correctness. The skill might import a library that doesn't exist, handle errors by swallowing them, or implement the wrong algorithm entirely.

**Fix:** The post-generation checklist exists for a reason. Read every file. Test the happy path and at least one error path.

### The Dependency Creep

**Pattern:** Generated requirements.txt includes 15 packages for a skill that could work with 3.

**Reality:** Each dependency is a maintenance burden, a security surface, and a potential breakage point.

**Fix:** Review requirements.txt. For each package, ask: "Is this actually used? Could I replace it with stdlib?" Remove everything that isn't essential.

---

## Sub-Agent Constraints

- **Sandbox filesystem:** Sub-agents write to `/workspace/` sandbox, NOT the host filesystem. File-heavy skill creation should be done in the main session, or results must be copied from the sandbox after the sub-agent completes.
- **Single depth only:** Sub-agents cannot spawn their own sub-agents. If a skill generation task needs sub-agent orchestration, the main session must coordinate it.
- **Review before commit:** When a sub-agent generates a skill, the main session must review and correct paths/details against actual infrastructure before committing. Sub-agents don't have access to the real filesystem state and may use placeholder or incorrect paths.

## Skill Composition Patterns

When combining generated skills:

- **Sequential:** Skill A output feeds Skill B input (research → architecture)
- **Parallel:** Multiple skills process different aspects of the same request
- **Conditional:** Route to different skills based on request type
- **Hierarchical:** Meta-skill orchestrates sub-skills

---

## Quick Reference Card

```
GENERATE:   python3 scripts/architect_skill.py -p "prompt" -o ./skills
VALIDATE:   python3 scripts/quick_validate.py skills/<name>

PHASES:     1. Research (web search + synthesis)
            2. Architecture (structure + SKILL.md)
            3. Implementation (scripts + references)
            4. Validation (auto-correct loop)

PROMPT TIPS:
  ✓ Specific scope ("parse PDF invoices" not "work with PDFs")
  ✓ Explicit constraints ("stdlib-only", "Python 3.9")
  ✓ Named outputs ("JSON report with fields X, Y, Z")
  ✓ Boundaries ("does NOT handle authentication")
  ✗ Vague scope ("data processing")
  ✗ Multiple responsibilities in one skill
  ✗ No constraints stated

POST-GEN:   Read SKILL.md → Review scripts → Check imports →
            Test happy path → Test error path → Pin deps →
            Verify 3.9 compat → Run validation

DON'T USE FOR: Complex systems, API auth wrappers,
               existing skill rewrites, skills under 50 lines
```
