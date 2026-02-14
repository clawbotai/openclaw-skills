# Updating

OpenClaw is pre-1.0. Update → checks → restart → verify.

## Recommended: re-run website installer
```bash
curl -fsSL https://openclaw.ai/install.sh | bash
# Add --no-onboard to skip wizard
# For source: --install-method git --no-onboard
```

## Update (global install)
```bash
npm i -g openclaw@latest   # or pnpm add -g openclaw@latest
openclaw doctor
openclaw gateway restart
openclaw health
```

## Update channels
```bash
openclaw update --channel beta|dev|stable
openclaw update --tag <dist-tag|version>
```

## Update (from source)
```bash
openclaw update  # preferred (git pull + deps + build + doctor + restart)
# Manual equivalent:
git pull && pnpm install && pnpm build && pnpm ui:build && openclaw doctor
```

## Always run: openclaw doctor
Repairs config, migrates deprecated keys, audits DM policies, checks gateway health, detects legacy services.

## Rollback / pinning
```bash
# Global: install specific version
npm i -g openclaw@<version>
# Source: pin by date
git checkout "$(git rev-list -n 1 --before="2026-01-01" origin/main)"
pnpm install && pnpm build && openclaw gateway restart
```

## Start / stop / restart
```bash
openclaw gateway status|stop|restart
openclaw logs --follow
# macOS: launchctl kickstart -k gui/$UID/bot.molt.gateway
# Linux: systemctl --user restart openclaw-gateway.service
```
