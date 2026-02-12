# skill-runtime-monitor

> AIOps observability layer for skill execution. Intercepts failures, classifies errors (transient vs deterministic), maintains a deduplicated error ledger with circuit breaker logic, surfaces reliability analytics, and exports LLM-optimized repair tickets for the Evolutionary Loop.

---

## Quick Start

### Prerequisites

- OpenClaw gateway running (`openclaw gateway status`)
- Workspace with skills directory

### Installation

Part of the OpenClaw skills collection — no separate install needed.

```bash
ls skills/skill-monitor/SKILL.md
```

## Usage Examples

```bash
python3 skills/skill-monitor/scripts/monitor.py --help
```
## Scripts

### `monitor.py`

```bash
python3 skills/skill-monitor/scripts/monitor.py --help
```

### `schemas.py`

```bash
python3 skills/skill-monitor/scripts/schemas.py --help
```

### `usage_example.py`

```bash
python3 skills/skill-monitor/scripts/usage_example.py --help
```
## Key Features

- **Architecture**
- **How to Use**
- **Error Classification**
- **Circuit Breaker**
- **Error Fingerprinting**
- **The Ledger (`memory/skill-errors.json`)**
## Configuration

Configured via `SKILL.md` frontmatter. Review and customize per deployment.

## Documentation

| Section | Description | Link |
|---------|-------------|------|
| **Tutorials** | Step-by-step learning | [docs/tutorials/](docs/tutorials/) |
| **How-To Guides** | Task solutions | [docs/how-to/](docs/how-to/) |
| **Reference** | Technical specs | [docs/reference/](docs/reference/) |
| **Explanations** | Design decisions | [docs/explanations/](docs/explanations/) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

Part of the OpenClaw project.
