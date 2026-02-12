# master-data

> - **Connection pooling** is mandatory for production: use **PgBouncer** (transaction mode) or **pgpool-II**

---

## Quick Start

### Prerequisites

- OpenClaw gateway running (`openclaw gateway status`)
- Workspace with skills directory

### Installation

Part of the OpenClaw skills collection — no separate install needed.

```bash
ls skills/data-engineering/SKILL.md
```

## Usage

This skill activates when the agent detects relevant user intent. See SKILL.md for triggers.

```bash
cat skills/data-engineering/SKILL.md
```
## Key Features

- **1. Schema Design**
- **2. PostgreSQL Operations**
- **3. Migrations**
- **4. Backup & Recovery**
- **5. AI-Assisted Schema Design**
- **6. Advanced Patterns**
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
