# planning-with-files

> Implements Manus-style file-based planning for complex tasks. Creates task_plan.md, findings.md, and progress.md. Use when starting complex multi-step tasks, research projects, or any task requiring >5 tool calls. Now with automatic session recovery after /clear.

---

## Quick Start

### Prerequisites

- OpenClaw gateway running (`openclaw gateway status`)
- Workspace with skills directory

### Installation

Part of the OpenClaw skills collection — no separate install needed.

```bash
ls skills/planning-with-files/SKILL.md
```

## Usage Examples

```bash
bash skills/planning-with-files/scripts/check-complete.sh --help
```
## Scripts

### `check-complete.sh`

```bash
bash skills/planning-with-files/scripts/check-complete.sh --help
```

### `init-session.sh`

```bash
bash skills/planning-with-files/scripts/init-session.sh --help
```

### `session-catchup.py`

```bash
python3 skills/planning-with-files/scripts/session-catchup.py --help
```
## Key Features

- **FIRST: Check for Previous Session (v2.2.0)**
- **Important: Where Files Go**
- **Layer 0 Integrations (2026 refresh)**
- **Quick Start**
- **The Core Pattern**
- **File Purposes**
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
