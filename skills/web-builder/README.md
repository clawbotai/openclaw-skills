# web-builder

Full web development lifecycle — scaffold SvelteKit PWAs, bundle single-file HTML apps, and deploy to GitHub Pages or Vercel.

## Overview

The web-builder skill provides end-to-end tooling for building and deploying modern web applications. It supports SvelteKit full-stack apps, single-file HTML bundling, and automated deployment workflows.

## Usage

```bash
# Scaffold a new SvelteKit project
bash skills/web-builder/scripts/init_project.sh my-app

# Deploy to GitHub Pages
bash skills/web-builder/scripts/deploy_github_pages.sh ./my-app
```

## Use Cases

- **SvelteKit Apps**: Full-stack PWA scaffolding with autonomous build-deploy workflow
- **Single HTML Bundling**: Bundle web apps into self-contained HTML files for distribution
- **GitHub Pages**: Deploy static sites with automated GitHub Actions
- **Vercel**: Deploy SvelteKit apps to production

## Configuration

Configure deployment targets in your project's `_meta.json` or pass options directly to the scripts. See [SKILL.md](SKILL.md) for all available triggers and parameters.

## References

- [SKILL.md](SKILL.md) — Full skill specification
- [Getting Started](docs/tutorials/getting-started.md) — Tutorial
