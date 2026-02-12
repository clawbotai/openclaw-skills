# Getting Started with web-builder

This tutorial walks you through creating and deploying a web application.

## Prerequisites

- Node.js 18+ installed
- Git configured with GitHub access

## Step 1: Initialize a Project

```bash
bash skills/web-builder/scripts/init_project.sh my-web-app
cd my-web-app
```

## Step 2: Develop Locally

```bash
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## Step 3: Deploy to GitHub Pages

```bash
bash skills/web-builder/scripts/deploy_github_pages.sh .
```

This sets up GitHub Actions for automated deployment on push.

## Next Steps

- See [SKILL.md](../../SKILL.md) for SvelteKit, HTML bundling, and Vercel workflows
- Check [deployment reference](../../references/deployment.md) for advanced options
