# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## Email

- **Address:** clawaibot@icloud.com
- **Credentials:** macOS Keychain → service: `icloud-email`, account: `clawaibot@icloud.com`
- **Retrieve:** `security find-generic-password -a "clawaibot@icloud.com" -s "icloud-email" -w`
- **IMAP quirk:** iCloud requires `BODY.PEEK[]` not `RFC822` — iCloud returns empty body for RFC822 fetch

## Cloudflare

- **Account ID:** `467a2bd281c1d03aa46c1dc520262826`
- **API Token (Pages + D1 + Workers):** Keychain service `cloudflare`, account `CLOUDFLARE_API_TOKEN` — token: `7X2zL0iiOpZuKW_6NOKtT2UEvRIVJ0l_FwBMKrs2`
- **DNS Edit Token:** Keychain service `CLOUDFLARE_DNS_TOKEN` — token: `hF_fOeKB4LM62NVAhTnACl8E_PuVzpsDOodrYfGh`
- **torrstatics.com Zone ID:** `f88c522f6e336f3488e6374bc414ecb9`
- **Pages project:** `torr-statics` (project ID: `a7d1c2d6-b39b-47d1-a688-501a9e912f59`)
- **D1 database:** `torr-orders` (ID: `6f241383-60fb-45d9-a75b-b0d4ead7ee2a`, region: ENAM)
- **KV namespace:** `ORDERS` (ID: `9fcb14464b6a4ee595e0226efa4eff97`)
- **Secrets bound:** `XPUB`, `ETHERSCAN_KEY`, `ADMIN_KEY` (`761355...a2ec`)
- **Deploy command:** `./torr-statics-site/deploy.sh` (runs `npx wrangler pages deploy . --project-name torr-statics --commit-dirty true`)
- **Deployment docs:** `torr-statics-site/DEPLOYMENT.md`
- **⚠️ Pages Functions 405 issue:** After adding D1 binding, all Pages Functions return 405. Even old code returns 405. Under investigation — may need to redeploy without `wrangler.toml` or debug via `wrangler pages functions tail`.

## Crypto / Payments

- **Wallet:** `0xA010807fAeef36c957CA80F17bA01b3922f7901C`
- **XPUB:** Stored as CF Pages secret `XPUB`
- **Etherscan API key:** `UQ42RKXAPVNZPRVU7S7VRVQSTX1AF4IE8C` (Keychain: `etherscan`)
- **Payment flow:** BIP-32 HD wallet derivation → unique address per order → on-chain verification via Etherscan

## Hetzner

- **Account:** clawaibot@icloud.com (Keychain: `hetzner-login`)
- **Status:** Manual verification pending (auto-verification failed)

## Etherscan

- **Account:** clawaibot@icloud.com (Keychain: `etherscan-login`)

## GitHub Repos

- **Workspace:** `clawbotai/openclaw-skills` (public)
- **TØrr Statics:** `clawbotai/torr-statics` (private)
- **MPMP:** `clawbotai/mpmp` (private)

## Monitored Skill Execution

All skill script invocations should go through the monitored runner:

```bash
bin/skillrun <skill-name> [--timeout N] -- <command...>
```

- Exit code 98 = skill is quarantined (circuit breaker OPEN)
- Errors auto-logged to `memory/skill-errors.json`
- Check health: `OPENCLAW_WORKSPACE=. python3 skills/skill-lifecycle/scripts/monitor.py status`

## Salesforce

- **Auth quirk:** Agentforce/orgfarm dev orgs have SOAP API disabled by default — no headless login works
- **Workaround:** Get browser cookie `sid=` value → use as `Authorization: Bearer <sid>` for REST API
- **Anonymous Apex won't help:** `UserInfo.getSessionId()` returns `SESSION_ID_REMOVED` in debug logs
- **SF CLI:** installed at `/opt/homebrew/bin/sf` (v2.122.6)
- **simple_salesforce:** installed (`pip3`)

## QNAP NAS (MediaCenter)

- **Model:** TBS-h574TX, QuTS Hero h6.0.0 Build 20260122 Beta
- **IP:** 192.168.10.233, login: admin / ranger2023
- **SSH:** Enabled (must be toggled on via QTS web UI → Control Panel → Network & File Services → Telnet/SSH)
- **Docker binary:** `/share/ZFS2_DATA/.qpkg/container-station/bin/docker` (NOT in PATH — must use full path)
- **QTS auth:** POST to `/cgi-bin/authLogin.cgi` with `pwd=` **base64-encoded** — plaintext fails silently (`authPassed=0`)
- **Container Station API:** v1 at `:8080/container-station/api/v1/` — login, list containers, list apps work; **inspect endpoints return 404** on QuTS Hero h6 (docs are for v2.4, doesn't match)
- **Container config:** All containers use `--network host`, `--restart unless-stopped`, `PUID=0 PGID=0`
- **Prowlarr API Key:** `1b84ce72887243de80dee26c5daf61c7`
- **Plex Token:** `n1uheT35no4W9NJ5szFR`
- **Plex sections:** 1=Movies(/movies), 2=TV(/tv), 5=Kids Movies(/kids-movies), 6=Kids TV(/kids-tv)
- **Indexers:** BroadcasTheNet (TV/Sonarr), PassThePopcorn (Movies/Radarr) — synced via Prowlarr fullSync
- **Radarr/Sonarr move quirk:** PUT with `moveFiles=true` alone doesn't move files — must also set `path` field explicitly to new location (e.g., `/kids-movies/Title (Year)`)
- **Disney+ network filter:** Too broad for kids content — catches Marvel, Star Wars live-action. Filter by animation genre or curated title list instead.

## Gemini CLI

- **Install:** `npm install -g @google/gemini-cli`
- **Auth:** `gemini auth login` (Google OAuth, one-time browser flow)
- **Settings:** `~/.gemini/settings.json` — key is `selectedAuthType` (NOT `authMethod`)
- **Gemini 3 access:** Requires `"previewFeatures": true` in settings.json AND toggled via `/settings` in interactive mode
- **Model names:** `gemini-3-pro-preview`, `gemini-3-flash-preview`, `gemini-2.5-pro`, `gemini-2.5-flash`
- **Headless mode:** `cat prompt.md | gemini --output-format json --model gemini-3-pro-preview`
- **JSON output:** Response wrapped in `{ "response": "...", "stats": {...} }` — parse `.response` field
- **Installed on:** Mac mini (clawaibot.local) + Steven's MacBook Pro
- **Auth shared:** OAuth creds copied from MacBook → Mac mini via scp
- **⚠️ antigravity-claude-proxy:** BANNED — Google actively banning accounts that use it. Do NOT use.

## TTS

- Preferred voice: default (no custom TTS configured yet)

## Brand Assets (TØrr Statics)

- Brand book: `assets/torr_hd_brandbook.pdf` (32MB)
- Manufacturing drawings: `assets/isobar/isobar1.pdf`, `assets/poise/poise27.pdf`
- Web images: `torr-statics-site/img/isobar-drawing.png`, `torr-statics-site/img/poise-drawing.png`
