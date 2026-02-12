---
name: skill-creator-extended
description: Autonomous AI-powered skill generator. Creates complete OpenClaw skills from a single natural-language prompt via a 4-phase pipeline (Research → Architecture → Implementation → Validation). Use when the user asks to build, create, or generate a new skill from a description.
---

# Skill Creator Extended

Generates complete, validated OpenClaw skills from a single prompt using a multi-phase LLM pipeline.

## Quick Start

```bash
python3 scripts/architect_skill.py --prompt "Build a skill for parsing financial PDFs" --output-path ./skills
```

## Pipeline Phases

### Phase 1: Research (Senior Researcher)
- Web search via DuckDuckGo for relevant libraries and patterns
- LLM synthesis into structured report (libraries, patterns, risks, recommendations)
- Constraint extraction from prompt (stdlib-only, Python version, output format)

### Phase 2: Architecture (Principal Architect)
- Evaluates 4 OpenClaw skill structures (Workflow, Task, Reference, Capabilities)
- Produces complete SKILL.md with real content (no TODOs)
- Generates file manifest for scripts/ and references/

### Phase 3: Implementation (Senior Developer)
- Scaffolds skill directory via init_skill.py
- Generates each script file via separate LLM call (structured output)
- Generates reference docs via LLM (not stubs)
- Aggregates dependencies into requirements.txt

### Phase 4: Validation & Self-Correction (Code Reviewer)
- Runs quick_validate.py on generated skill
- On failure: feeds error back to reviewer LLM for fix
- Auto-correction loop up to N retries

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--prompt, -p` | *required* | Natural-language skill description |
| `--model, -m` | `gpt-4o` | OpenAI model to use |
| `--output-path, -o` | `./skills` | Parent directory for generated skill |
| `--max-retries` | `3` | Max retries for API calls and validation |
| `--verbose, -v` | off | Enable debug logging |

## Requirements

- `OPENAI_API_KEY` environment variable
- Dependencies: `openai>=1.0.0`, `pydantic>=2.0.0`, `rich>=13.0.0`, `duckduckgo-search>=4.0.0`

## Constraints System

The tool automatically extracts constraints from your prompt and enforces them across all LLM phases:

- "stdlib-only" / "no dependencies" → blocks external library recommendations
- "Python 3.9" → enforces version compatibility
- "JSON output" / "structured JSON" → enforces output format

## Known Limitations

- Output quality depends on the model — GPT-4o produces ~300 LOC per script, which may be insufficient for complex systems
- Best suited for scaffolding new skills, not rebuilding existing complex ones
- Reference files are generated but may need manual review for accuracy
