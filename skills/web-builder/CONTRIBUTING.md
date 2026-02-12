# Contributing to web-builder

Contributions welcome! This skill covers web scaffolding, bundling, and deployment.

## Development Setup

1. Clone the repo and navigate to the skill:
   ```bash
   cd skills/web-builder
   ```
2. Review `SKILL.md` for the full specification
3. Ensure you have Node.js installed for testing SvelteKit workflows

## Making Changes

- Create a feature branch: `git checkout -b feat/my-change`
- Follow existing script conventions (bash with `set -euo pipefail`)
- Test deployment scripts in a sandbox environment
- Update docs if adding new features or changing behavior

## Pull Request Workflow

1. Push your branch and open a PR against `main`
2. Include a clear description of what changed and why
3. Verify all scripts still pass `--help` and basic smoke tests
4. Request review from a maintainer
5. Merge after approval
