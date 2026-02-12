# quarter-hour-updates

> Provides structured progress updates every 15 minutes (at :00, :15, :30, :45) while a task is running. Each update includes a short synopsis plus the next two planned steps, stays under 150 words, and continues until the user marks the task complete.

---

## Quick Start

### Prerequisites

- OpenClaw gateway running (`openclaw gateway status`)
- Workspace with skills directory

### Installation

Part of the OpenClaw skills collection — no separate install needed.

```bash
ls skills/quarter-hour-updates/SKILL.md
```

## Usage Examples

```bash
python3 skills/quarter-hour-updates/scripts/cerebro_tick.py --help
```
## Scripts

### `cerebro_tick.py`

```bash
python3 skills/quarter-hour-updates/scripts/cerebro_tick.py --help
```

### `daemon.py`

```bash
python3 skills/quarter-hour-updates/scripts/daemon.py --help
```

### `log_progress.py`

```bash
python3 skills/quarter-hour-updates/scripts/log_progress.py --help
```

### `migrate.py`

```bash
python3 skills/quarter-hour-updates/scripts/migrate.py --help
```

### `start_task.py`

```bash
python3 skills/quarter-hour-updates/scripts/start_task.py --help
```

### `state.py`

```bash
python3 skills/quarter-hour-updates/scripts/state.py --help
```

### `stop_task.py`

```bash
python3 skills/quarter-hour-updates/scripts/stop_task.py --help
```
## Key Features

- **Overview**
- **Folder Structure**
- **Command Cheatsheet**
- **Workflow**
- **Observability & Guardrails**
- **Testing**
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
