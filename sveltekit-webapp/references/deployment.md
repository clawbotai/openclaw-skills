# Deployment Configuration

## Check Available Targets

```bash
# Check Vercel auth
vercel whoami 2>/dev/null && echo "✓ Vercel authenticated" || echo "✗ Vercel not available"

# Check GitHub auth (needed for all deployments)
gh auth status 2>/dev/null && echo "✓ GitHub authenticated" || echo "✗ GitHub not available"
```

## Vercel (Recommended)

### Setup
```bash
npx sv add sveltekit-adapter  # choose: vercel
```

### Deploy
```bash
vercel link        # Link to Vercel project
vercel --prod      # Deploy to production
```

### svelte.config.js
```javascript
import adapter from '@sveltejs/adapter-vercel';

export default {
  kit: {
    adapter: adapter({
      runtime: 'nodejs22.x'  // or 'edge'
    })
  }
};
```

### Environment Variables
Set in Vercel dashboard or via CLI:
```bash
vercel env add DATABASE_URL production
```

---

## Cloudflare Pages

### Setup
```bash
npx sv add sveltekit-adapter  # choose: cloudflare, target: pages
```

### svelte.config.js
```javascript
import adapter from '@sveltejs/adapter-cloudflare';

export default {
  kit: {
    adapter: adapter({
      routes: {
        include: ['/*'],
        exclude: ['<all>']
      }
    })
  }
};
```

### Deploy via GitHub
1. Connect repo to Cloudflare Pages dashboard
2. Build command: `npm run build`
3. Output directory: `.svelte-kit/cloudflare`

### Wrangler CLI
```bash
npm install -D wrangler
npx wrangler pages deploy .svelte-kit/cloudflare
```

---

## Netlify

### Setup
```bash
npx sv add sveltekit-adapter  # choose: netlify
```

### svelte.config.js
```javascript
import adapter from '@sveltejs/adapter-netlify';

export default {
  kit: {
    adapter: adapter({
      edge: false,
      split: false
    })
  }
};
```

### netlify.toml
```toml
[build]
  command = "npm run build"
  publish = "build"

[functions]
  node_bundler = "esbuild"
```

### Deploy
```bash
npm install -g netlify-cli
netlify login
netlify init
netlify deploy --prod
```

---

## Node.js Server

### Setup
```bash
npx sv add sveltekit-adapter  # choose: node
```

### svelte.config.js
```javascript
import adapter from '@sveltejs/adapter-node';

export default {
  kit: {
    adapter: adapter({
      out: 'build',
      precompress: true
    })
  }
};
```

### Run
```bash
npm run build
node build/index.js
```

### Environment Variables
```bash
PORT=3000
HOST=0.0.0.0
ORIGIN=https://yourdomain.com
```

### Docker
```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY build ./build
EXPOSE 3000
CMD ["node", "build/index.js"]
```

---

## Static Site

### Setup
```bash
npx sv add sveltekit-adapter  # choose: static
```

### svelte.config.js
```javascript
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: '404.html',  // or 'index.html' for SPA
      precompress: true
    }),
    prerender: {
      entries: ['*']
    }
  }
};
```

### Deploy Anywhere
The `build/` directory can be deployed to any static host:
- GitHub Pages
- Cloudflare Pages
- Netlify
- AWS S3 + CloudFront
- Any web server

---

## CI/CD with GitHub Actions

### Vercel (via GitHub integration)
No action needed—Vercel auto-deploys on push when connected.

### Manual Deployment Action

`.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      
      - run: npm ci
      - run: npm run build
      - run: npm run test
      
      # Add deployment step based on target
      # Example for Cloudflare Pages:
      - name: Deploy to Cloudflare
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: your-project
          directory: .svelte-kit/cloudflare
```
