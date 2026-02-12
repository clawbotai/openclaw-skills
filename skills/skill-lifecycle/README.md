# skill-lifecycle

Unified skill lifecycle management: Research→Build→Reflect evolutionary loop with AIOps runtime monitoring, error classification, circuit breakers, and self-healing repair tickets.

## Overview

The skill-lifecycle skill provides a complete framework for managing OpenClaw skills from inception through production. It combines an evolutionary development loop (Research → Build → Reflect) with runtime AIOps monitoring to ensure skills are continuously improved and self-healing.

## Usage

Trigger the evolutionary loop with natural language:

```bash
# Start a research-build-reflect cycle
openclaw run skill-lifecycle --trigger "evo loop" --skill my-skill

# Monitor runtime health
openclaw run skill-lifecycle --trigger "aiops check" --skill my-skill
```

## Key Features

- **Evolutionary Loop**: Automated Research → Build → Reflect cycles
- **Error Classification**: Categorize and prioritize runtime errors
- **Circuit Breakers**: Prevent cascading failures across skills
- **Self-Healing**: Automatic repair ticket generation for known issues
- **Runtime Monitoring**: AIOps-driven health checks and alerting

## Architecture

The skill operates in two modes:

1. **Development Mode** — runs the evolutionary loop for skill improvement
2. **Runtime Mode** — monitors deployed skills with AIOps patterns

## References

- [SKILL.md](SKILL.md) for full configuration and trigger documentation
- [Getting Started Tutorial](docs/tutorials/getting-started.md)
