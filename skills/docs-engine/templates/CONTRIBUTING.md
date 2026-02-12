# Contributing to [Project Name]

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Commit Convention](#commit-convention)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

---

## Getting Started

1. **Fork** this repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/[project-name].git
   cd [project-name]
   ```
3. **Add the upstream remote:**
   ```bash
   git remote add upstream https://github.com/OWNER/[project-name].git
   ```

---

## Development Setup

```bash
# Install dependencies
# [TODO: Replace with actual setup commands]
# npm install / pip install -e ".[dev]" / go mod download

# Verify your setup
# [TODO: Replace with actual test command]
# npm test / pytest / go test ./...
```

---

## Making Changes

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make your changes.** Follow existing code style and conventions.

3. **Write or update tests** for any new functionality.

4. **Run the test suite** and ensure all tests pass:
   ```bash
   # [TODO: Replace with actual commands]
   # npm test && npm run lint && npm run typecheck
   ```

5. **Commit your changes** using the Conventional Commits format (see below).

6. **Push** to your fork and **open a Pull Request.**

---

## Commit Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for clear, automated changelogs and semantic versioning.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | When to Use |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Formatting, missing semicolons (no code change) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `build` | Build system or external dependency changes |
| `ci` | CI/CD configuration changes |
| `chore` | Other changes that don't modify src or test files |

### Examples

```
feat(auth): add OAuth2 login support
fix(api): handle null response from upstream service
docs: update installation instructions for Windows
refactor!: rename UserService to AccountService

BREAKING CHANGE: UserService import path has changed.
```

### Rules

- Use the **imperative mood** ("add" not "added" or "adds")
- Do **not** capitalize the first letter of the description
- Do **not** end the description with a period
- Use `!` after the type/scope for **breaking changes**

---

## Pull Request Process

1. **Update documentation** if your change affects public behavior
2. **Update CHANGELOG.md** under the `[Unreleased]` section
3. **Ensure CI passes** — all tests, linting, and type checks must be green
4. **Request a review** from at least one maintainer
5. **Squash commits** if requested (or if the PR has many small fixup commits)

### PR Title Format

Use the same Conventional Commits format for the PR title:
```
feat(scope): brief description of the change
```

### PR Description Template

```markdown
## What

[Brief description of what this PR does]

## Why

[Why is this change needed? Link to issue if applicable]

## How

[How was this implemented? Any technical details worth noting]

## Testing

[How was this tested? What should reviewers verify?]
```

---

## Reporting Issues

### Bug Reports

Include:
- **Description:** What happened?
- **Expected behavior:** What should have happened?
- **Steps to reproduce:** Minimal steps to trigger the bug
- **Environment:** OS, runtime version, relevant configuration
- **Logs/screenshots:** If applicable

### Feature Requests

Include:
- **Problem:** What problem does this solve?
- **Proposed solution:** How should it work?
- **Alternatives considered:** What else did you think about?

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).
