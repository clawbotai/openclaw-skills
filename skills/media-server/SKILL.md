---
name: media-server
description: Media server stack management — Plex, Radarr, Sonarr, Prowlarr, qBittorrent, Jellyseerr on QNAP NAS
---

# Media Server Skill

Manages the *arr stack + Plex on a QNAP NAS (TBS-h574TX, QuTS Hero h6.0.0 Beta) at `192.168.10.233`. Everything runs as Docker containers with `--network host`.

## Architecture Overview

```
Jellyseerr (requests) → Radarr / Sonarr (management)
                              ↓
Prowlarr (indexers) ──fullSync──→ Radarr + Sonarr
                              ↓
                        qBittorrent (downloads)
                              ↓
                     Plex (streaming)
```

### Service Map

| Service      | Port  | Purpose              | API Base                              |
|-------------|-------|----------------------|---------------------------------------|
| Plex        | 32400 | Media streaming      | `http://192.168.10.233:32400`         |
| Radarr      | 7878  | Movie management     | `http://192.168.10.233:7878/api/v3`   |
| Sonarr      | 8989  | TV management        | `http://192.168.10.233:8989/api/v3`   |
| Prowlarr    | 9696  | Indexer management   | `http://192.168.10.233:9696/api/v1`   |
| qBittorrent | 8085  | Torrent client       | `http://192.168.10.233:8085/api/v2`   |
| Jellyseerr  | 5055  | Request management   | `http://192.168.10.233:5055/api/v1`   |
| SearXNG     | 8888  | Search engine        | `http://192.168.10.233:8888`          |

### Library Layout

| Plex Library | Section ID | Root Folder    | Managed By |
|-------------|-----------|----------------|------------|
| Movies      | 1         | `/movies`      | Radarr     |
| TV          | 2         | `/tv`          | Sonarr     |
| Kids Movies | 5         | `/kids-movies` | Radarr     |
| Kids TV     | 6         | `/kids-tv`     | Sonarr     |

### API Keys

API keys live in `TOOLS.md`. Reference pattern:
- **Radarr/Sonarr:** `X-Api-Key` header or `?apikey=` query param
- **Prowlarr:** `X-Api-Key: 1b84ce72887243de80dee26c5daf61c7`
- **Plex:** `X-Plex-Token=n1uheT35no4W9NJ5szFR` as query param

---

## 1. Container Lifecycle

### The QNAP Docker Reality

Docker is installed via Container Station but **not in PATH**. Always use the full path:

```bash
DOCKER=/share/ZFS2_DATA/.qpkg/container-station/bin/docker
```

All containers share the same base flags:
```
--network host --restart unless-stopped -e PUID=0 -e PGID=0 -e TZ=America/Bogota
```

### Update Pattern

There is no in-place update for Docker containers. The cycle is: pull → stop → rm → run.

```bash
DOCKER=/share/ZFS2_DATA/.qpkg/container-station/bin/docker

# 1. Pull new image
$DOCKER pull linuxserver/radarr:latest

# 2. Stop and remove
$DOCKER stop radarr
$DOCKER rm radarr

# 3. Recreate with same args (keep your run command documented!)
$DOCKER run -d --name radarr \
  --network host --restart unless-stopped \
  -e PUID=0 -e PGID=0 -e TZ=America/Bogota \
  -v /share/ZFS2_DATA/Public/Container/radarr/config:/config \
  -v /share/ZFS2_DATA/Public/Library/movies:/movies \
  -v /share/ZFS2_DATA/Public/Library/kids/movies:/kids-movies \
  -v /share/ZFS2_DATA/Public/Downloads:/downloads \
  linuxserver/radarr:latest

# 4. Clean up old images
$DOCKER image prune -f
```

**Before updating:** Back up the config directory. The *arr apps store their database in `/config` — if an update goes wrong, you can roll back by restoring it and running the old image tag.

### Health Check (SSH)

```bash
ssh admin@192.168.10.233 '/share/ZFS2_DATA/.qpkg/container-station/bin/docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
```

### Inspecting a Container

Container Station API v1 inspect endpoints **return 404 on QuTS Hero h6** — the docs are for v2.4 and don't match. Always use SSH + docker inspect:

```bash
ssh admin@192.168.10.233 '/share/ZFS2_DATA/.qpkg/container-station/bin/docker inspect radarr'
```

### QTS Web Authentication

If you need to authenticate against the QNAP web UI API:

```bash
# Password MUST be base64-encoded — plaintext fails silently (authPassed=0)
PWD_B64=$(echo -n 'ranger2023' | base64)
curl -s "http://192.168.10.233:8080/cgi-bin/authLogin.cgi" \
  -d "user=admin&pwd=$PWD_B64"
```

---

## 2. Media Management

### Radarr API Patterns

All Radarr endpoints use `http://192.168.10.233:7878/api/v3` with `X-Api-Key` header.

#### Lookup a Movie (by TMDB ID or search)

```bash
# By TMDB ID
curl -s "http://192.168.10.233:7878/api/v3/movie/lookup/tmdb?tmdbId=550" \
  -H "X-Api-Key: $RADARR_KEY"

# By search term
curl -s "http://192.168.10.233:7878/api/v3/movie/lookup?term=fight+club" \
  -H "X-Api-Key: $RADARR_KEY"
```

#### Add a Movie

```bash
curl -s -X POST "http://192.168.10.233:7878/api/v3/movie" \
  -H "X-Api-Key: $RADARR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fight Club",
    "tmdbId": 550,
    "qualityProfileId": 1,
    "rootFolderPath": "/movies",
    "monitored": true,
    "addOptions": { "searchForMovie": true }
  }'
```

For kids movies, use `"rootFolderPath": "/kids-movies"` and add the kids tag: `"tags": [1]`.

#### Move a Movie Between Root Folders

**Critical quirk:** Setting `moveFiles: true` alone does NOT work. You must explicitly set the `path` field to the new full path.

```bash
# First GET the movie to get its current data
MOVIE=$(curl -s "http://192.168.10.233:7878/api/v3/movie/123" -H "X-Api-Key: $RADARR_KEY")

# Then PUT with BOTH path and moveFiles
curl -s -X PUT "http://192.168.10.233:7878/api/v3/movie/123?moveFiles=true" \
  -H "X-Api-Key: $RADARR_KEY" \
  -H "Content-Type: application/json" \
  -d '{ ...movie data..., "path": "/kids-movies/Frozen (2013)", "rootFolderPath": "/kids-movies" }'
```

#### Radarr Quick Reference

| Action | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| List all | GET | `/movie` | |
| Get one | GET | `/movie/{id}` | |
| Add | POST | `/movie` | Include `addOptions.searchForMovie` |
| Update/Move | PUT | `/movie/{id}?moveFiles=true` | Must set `path` explicitly |
| Delete | DELETE | `/movie/{id}?deleteFiles=true` | ⚠️ Destructive |
| Search | POST | `/command` | `{"name":"MoviesSearch","movieIds":[id]}` |
| Queue | GET | `/queue` | Active downloads |
| Quality profiles | GET | `/qualityprofile` | |
| Tags | GET | `/tag` | Kids tag = id 1 |
| Root folders | GET | `/rootfolder` | |
| Custom formats | GET | `/customformat` | |

### Sonarr API Patterns

Same structure as Radarr at `http://192.168.10.233:8989/api/v3`.

#### Add a Series

```bash
curl -s -X POST "http://192.168.10.233:8989/api/v3/series" \
  -H "X-Api-Key: $SONARR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Breaking Bad",
    "tvdbId": 81189,
    "qualityProfileId": 1,
    "rootFolderPath": "/tv",
    "monitored": true,
    "addOptions": { "searchForMissingEpisodes": true }
  }'
```

Kids TV → `"rootFolderPath": "/kids-tv"` + `"tags": [1]`.

#### Sonarr Quick Reference

| Action | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| List all | GET | `/series` | |
| Add | POST | `/series` | Include `addOptions` |
| Update/Move | PUT | `/series/{id}?moveFiles=true` | Must set `path` explicitly |
| Delete | DELETE | `/series/{id}?deleteFiles=true` | ⚠️ Destructive |
| Search season | POST | `/command` | `{"name":"SeasonSearch","seriesId":id,"seasonNumber":N}` |
| Episode list | GET | `/episode?seriesId={id}` | |
| Queue | GET | `/queue` | |
| Calendar | GET | `/calendar?start=&end=` | Upcoming episodes |

### Custom Formats (TRaSH-Style)

These are configured in Radarr to score releases and prefer quality:

| Custom Format | Score | Rationale |
|--------------|-------|-----------|
| Remux | +2000 | Best quality, untouched stream |
| Dolby Vision | +2000 | Premium HDR format |
| HDR10+ | +1500 | Dynamic HDR metadata |
| Atmos | +1500 | Object-based spatial audio |
| HEVC/x265 | +1000 | Better compression, saves space |
| Multi-Audio | +500 | Multiple language tracks |

Higher aggregate score wins during grabs. The quality profile sets the floor; custom formats determine which release wins among acceptable qualities.

---

## 3. Indexer Management (Prowlarr)

Prowlarr manages indexers centrally and syncs them to Radarr and Sonarr via **fullSync**. You don't configure indexers in Radarr/Sonarr directly.

### Current Indexers

| Indexer | Type | Syncs To |
|---------|------|----------|
| BroadcasTheNet | TV (private) | Sonarr |
| PassThePopcorn | Movies (private) | Radarr |

### Prowlarr API

```bash
# List indexers
curl -s "http://192.168.10.233:9696/api/v1/indexer" \
  -H "X-Api-Key: 1b84ce72887243de80dee26c5daf61c7"

# Trigger sync to apps
curl -s -X POST "http://192.168.10.233:9696/api/v1/command" \
  -H "X-Api-Key: 1b84ce72887243de80dee26c5daf61c7" \
  -H "Content-Type: application/json" \
  -d '{"name":"AppIndexerSync"}'

# Test an indexer
curl -s -X POST "http://192.168.10.233:9696/api/v1/indexer/test" \
  -H "X-Api-Key: 1b84ce72887243de80dee26c5daf61c7" \
  -H "Content-Type: application/json" \
  -d '{"id": 1}'
```

### Sync Troubleshooting

If indexers aren't showing in Radarr/Sonarr:
1. Check Prowlarr → Settings → Apps — ensure Radarr/Sonarr apps are configured with correct URLs and API keys
2. Trigger manual sync via `AppIndexerSync` command above
3. Check Prowlarr logs: `ssh admin@192.168.10.233 'cat /share/ZFS2_DATA/Public/Container/prowlarr/config/logs/prowlarr.txt | tail -50'`
4. Verify the indexer itself works: test it in Prowlarr UI or via API

---

## 4. Library Organization

### Kids Content Strategy

Kids content uses **separate root folders** and **dedicated Plex libraries** — not just tags or filters. This is deliberate:

- `/movies` → Plex "Movies" library (section 1)
- `/kids-movies` → Plex "Kids Movies" library (section 5)
- `/tv` → Plex "TV" library (section 2)
- `/kids-tv` → Plex "Kids TV" library (section 6)

The kids tag (id=1) in Radarr/Sonarr is for filtering within the *arr UI, but the real separation is at the filesystem level.

**Why not use Disney+ network as a kids filter?** It's too broad — Disney+ hosts Marvel, Star Wars live-action, and other non-kids content. Filter by **animation genre** or use a **curated title list** instead.

### Plex Library Scans

After adding/moving content, trigger a Plex library scan:

```bash
# Scan specific library
curl -s -X POST "http://192.168.10.233:32400/library/sections/1/refresh?X-Plex-Token=n1uheT35no4W9NJ5szFR"

# Scan all libraries
for id in 1 2 5 6; do
  curl -s -X POST "http://192.168.10.233:32400/library/sections/$id/refresh?X-Plex-Token=n1uheT35no4W9NJ5szFR"
done
```

### Plex API Quick Reference

| Action | Method | Endpoint |
|--------|--------|----------|
| List libraries | GET | `/library/sections?X-Plex-Token=TOKEN` |
| Scan library | POST | `/library/sections/{id}/refresh?X-Plex-Token=TOKEN` |
| Recently added | GET | `/library/recentlyAdded?X-Plex-Token=TOKEN` |
| Server identity | GET | `/identity` |
| Active sessions | GET | `/status/sessions?X-Plex-Token=TOKEN` |

---

## 5. Download Pipeline

### Flow

1. **Request** → Jellyseerr (user) or direct add in Radarr/Sonarr
2. **Search** → Radarr/Sonarr query indexers (via Prowlarr-synced configs)
3. **Grab** → Best release selected by quality profile + custom format scoring
4. **Download** → Sent to qBittorrent with category (`radarr` or `tv-sonarr`)
5. **Import** → Radarr/Sonarr detect completion, hardlink/move to library folder
6. **Scan** → Plex detects new files (or manual scan trigger)

### qBittorrent

Categories are pre-configured:
- `radarr` — Radarr sends movie downloads here
- `tv-sonarr` — Sonarr sends TV downloads here

```bash
# Login (cookie-based auth)
curl -s -c /tmp/qbt.cookie "http://192.168.10.233:8085/api/v2/auth/login" \
  -d "username=admin&password=adminadmin"

# List active torrents
curl -s -b /tmp/qbt.cookie "http://192.168.10.233:8085/api/v2/torrents/info?filter=active"

# Get transfer info
curl -s -b /tmp/qbt.cookie "http://192.168.10.233:8085/api/v2/transfer/info"
```

### Hardlinks

The *arr apps prefer hardlinks over copies when source and destination are on the same filesystem. This saves disk space — the download and the organized library file point to the same data on disk. The download can seed indefinitely without doubling storage.

For hardlinks to work, downloads and library folders must be on the same volume (they are — both on ZFS2_DATA).

---

## 6. Request Management (Jellyseerr)

Jellyseerr provides a user-friendly request interface that connects to Radarr, Sonarr, and Plex.

```bash
# List pending requests
curl -s "http://192.168.10.233:5055/api/v1/request?filter=pending" \
  -H "X-Api-Key: $JELLYSEERR_KEY"

# Approve a request
curl -s -X POST "http://192.168.10.233:5055/api/v1/request/{id}/approve" \
  -H "X-Api-Key: $JELLYSEERR_KEY"

# Get request count
curl -s "http://192.168.10.233:5055/api/v1/request/count" \
  -H "X-Api-Key: $JELLYSEERR_KEY"
```

Jellyseerr auto-sends approved requests to the appropriate *arr app based on media type.

---

## 7. Monitoring & Health

### Health Endpoints

```bash
# Radarr system status
curl -s "http://192.168.10.233:7878/api/v3/health" -H "X-Api-Key: $RADARR_KEY"
curl -s "http://192.168.10.233:7878/api/v3/system/status" -H "X-Api-Key: $RADARR_KEY"

# Sonarr system status
curl -s "http://192.168.10.233:8989/api/v3/health" -H "X-Api-Key: $SONARR_KEY"
curl -s "http://192.168.10.233:8989/api/v3/system/status" -H "X-Api-Key: $SONARR_KEY"

# Prowlarr health
curl -s "http://192.168.10.233:9696/api/v1/health" \
  -H "X-Api-Key: 1b84ce72887243de80dee26c5daf61c7"

# Plex server identity (simple alive check)
curl -s "http://192.168.10.233:32400/identity"
```

### Queue Monitoring

```bash
# Radarr download queue
curl -s "http://192.168.10.233:7878/api/v3/queue?page=1&pageSize=50" \
  -H "X-Api-Key: $RADARR_KEY"

# Sonarr download queue
curl -s "http://192.168.10.233:8989/api/v3/queue?page=1&pageSize=50" \
  -H "X-Api-Key: $SONARR_KEY"
```

### Disk Space

```bash
# Via Radarr
curl -s "http://192.168.10.233:7878/api/v3/diskspace" -H "X-Api-Key: $RADARR_KEY"

# Via SSH
ssh admin@192.168.10.233 'df -h /share/ZFS2_DATA'
```

### Comprehensive Health Check Script

```python
#!/usr/bin/env python3
"""Media server health check — stdlib only, Python 3.9 compatible."""
import json
import urllib.request
import sys
from typing import Dict, List, Tuple

NAS = "192.168.10.233"
PLEX_TOKEN = "n1uheT35no4W9NJ5szFR"
PROWLARR_KEY = "1b84ce72887243de80dee26c5daf61c7"

SERVICES = [
    ("Plex", f"http://{NAS}:32400/identity", None),
    ("Radarr", f"http://{NAS}:7878/api/v3/health", "RADARR_KEY"),
    ("Sonarr", f"http://{NAS}:8989/api/v3/health", "SONARR_KEY"),
    ("Prowlarr", f"http://{NAS}:9696/api/v1/health", PROWLARR_KEY),
    ("qBittorrent", f"http://{NAS}:8085/api/v2/app/version", None),
    ("Jellyseerr", f"http://{NAS}:5055/api/v1/status", None),
]

def check_service(name: str, url: str, api_key: str = None) -> Tuple[str, bool, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        if api_key:
            req.add_header("X-Api-Key", api_key)
        if "Plex" in name:
            url += f"?X-Plex-Token={PLEX_TOKEN}" if "?" not in url else f"&X-Plex-Token={PLEX_TOKEN}"
            req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            return (name, True, f"HTTP {resp.status}")
    except Exception as e:
        return (name, False, str(e)[:80])

def main():
    results = []
    for name, url, key in SERVICES:
        results.append(check_service(name, url, key))

    all_ok = all(ok for _, ok, _ in results)
    for name, ok, detail in results:
        status = "✅" if ok else "❌"
        print(f"{status} {name}: {detail}")

    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
```

---

## 8. Troubleshooting

### Decision Tree

```
Problem?
├── Container won't start
│   ├── Check: $DOCKER ps -a --filter name=X
│   ├── Check: $DOCKER logs X --tail 50
│   └── Fix: Recreate with correct volume mounts
│
├── Movie/show not downloading
│   ├── Check: Is it monitored? GET /movie/{id} → monitored: true
│   ├── Check: Indexer working? Prowlarr health endpoint
│   ├── Check: Manual search → POST /command {"name":"MoviesSearch"}
│   └── Check: Queue for errors → GET /queue
│
├── Content in wrong library
│   ├── Check: Root folder path in *arr
│   ├── Fix: Move via PUT with path AND moveFiles=true
│   └── Then: Trigger Plex scan on both old and new library
│
├── Plex not showing new content
│   ├── Fix: Trigger library scan (POST /library/sections/{id}/refresh)
│   ├── Check: File permissions (should be root/PUID=0)
│   └── Check: File is in correct root folder
│
├── Indexer not in Radarr/Sonarr
│   ├── Check: Prowlarr → Settings → Apps
│   ├── Fix: Trigger AppIndexerSync in Prowlarr
│   └── Verify: Prowlarr logs for sync errors
│
└── Disk space low
    ├── Check: /api/v3/diskspace
    ├── Fix: docker image prune -f
    ├── Fix: Clear completed downloads in qBittorrent
    └── Fix: Review and delete unwanted media
```

### Known Gotchas

1. **QNAP busybox `ln -sf` bug:** When targeting a directory, `ln -sf /target /link` creates an empty directory instead of a symlink. Fix: `rm /link && ln -s /target /link`.

2. **Container Station API v1 inspect = 404:** Don't waste time on it. Use `ssh + docker inspect` instead.

3. **QTS auth silent failure:** If `authPassed=0` with no error, your password isn't base64-encoded. `echo -n 'password' | base64` → use that.

4. **Radarr/Sonarr move doesn't move:** You MUST set `"path": "/new-root/Title (Year)"` explicitly in the PUT body, not just `moveFiles=true`. This has burned hours.

5. **Disney+ ≠ Kids:** Disney+ network includes Marvel Cinematic Universe, Star Wars, and mature content. Don't use it as a kids content filter. Use animation genre filtering or a curated list.

6. **Docker not in PATH on QNAP:** Always use `/share/ZFS2_DATA/.qpkg/container-station/bin/docker`. Alias it in your SSH session or scripts.

7. **Cross-seed setup:** Image `ghcr.io/cross-seed/cross-seed:6`, config at `/share/ZFS2_DATA/Public/Container/cross-seed/config/config.js`. Uses `linkDirs` not `savePath`.

8. **PTP rate limit awareness:** Rapid API calls during container cycling can trigger indexer auto-disable (escalation). Space out bulk operations — don't restart multiple containers that all hit indexers simultaneously.

9. **Hardlink verification after mount migration:** After migrating to unified `/data` mount, existing files keep link count=1 (were copied under different mounts). Only NEW downloads hardlink correctly. Verify with `stat` after first completed download.

10. **Plex SQLite path migration:** Stop Plex, copy `com.plexapp.plugins.library.db`, update `section_locations` and `media_parts` tables with new paths, upload back, restart. Works for bulk path changes without re-scanning.

11. **Jellyseerr init:** Use `mediaServerType=1` for Plex. Needs web UI login to verify Radarr/Sonarr connections after fresh setup — API-only init is insufficient.

---

## 9. Backup & Recovery

### Config Backup

All *arr apps store their config (database, settings) in `/config` volumes mapped to `/share/ZFS2_DATA/Public/Container/{app}/config/`.

```bash
# Backup all configs
ssh admin@192.168.10.233 'cd /share/ZFS2_DATA/Public/Container && tar czf /share/ZFS2_DATA/Public/backups/media-configs-$(date +%Y%m%d).tar.gz radarr sonarr prowlarr plex jellyseerr qbittorrent'
```

### Container Recreation Reference

Keep the exact `docker run` commands documented. If you lose a container, you need the exact volume mounts and env vars to recreate it. Use `docker inspect` to capture the current state:

```bash
DOCKER=/share/ZFS2_DATA/.qpkg/container-station/bin/docker

# Capture current container config for disaster recovery
mkdir -p /share/ZFS2_DATA/Public/backups
for c in plex radarr sonarr prowlarr qbittorrent jellyseerr searxng redis; do
  $DOCKER inspect $c > /share/ZFS2_DATA/Public/backups/container-$c.json
done
```

### Recovery Priority Order

If multiple services go down, restore in this order:
1. **qBittorrent** — so active downloads don't stall
2. **Prowlarr** — indexer management (others depend on it)
3. **Radarr + Sonarr** — media management
4. **Plex** — streaming (works with existing files even without *arr)
5. **Jellyseerr** — nice-to-have, not critical
6. **SearXNG + Redis** — lowest priority

---

## 10. Integration Points

### With devops skill
- Container lifecycle follows the same patterns (pull → stop → rm → run)
- Use `bin/skillrun media-server` for monitored execution of media scripts

### With agent-guardrails
- **Always confirm before:** `docker rm`, `deleteFiles=true` on *arr API, clearing download queue
- These are destructive and irreversible

### With healthcheck skill
- The health check script above is cron-compatible (exit 0 = healthy, exit 1 = degraded)
- Run periodically to catch issues before users notice

### With agent-memory
- Store learned container run commands, API quirks, and troubleshooting resolutions
- Reference `TOOLS.md` for current credentials and connection details

---

## Common Command Cheat Sheet

```bash
# Variables
DOCKER=/share/ZFS2_DATA/.qpkg/container-station/bin/docker
NAS=192.168.10.233

# Container status
ssh admin@$NAS "$DOCKER ps --format 'table {{.Names}}\t{{.Status}}'"

# Restart a service
ssh admin@$NAS "$DOCKER restart radarr"

# View logs
ssh admin@$NAS "$DOCKER logs --tail 100 radarr"

# Plex scan all libraries
for id in 1 2 5 6; do curl -sX POST "http://$NAS:32400/library/sections/$id/refresh?X-Plex-Token=n1uheT35no4W9NJ5szFR"; done

# Check disk space
curl -s "http://$NAS:7878/api/v3/diskspace" -H "X-Api-Key: $RADARR_KEY" | python3 -m json.tool

# Active Plex streams
curl -s "http://$NAS:32400/status/sessions?X-Plex-Token=n1uheT35no4W9NJ5szFR"

# Image cleanup
ssh admin@$NAS "$DOCKER image prune -f"
```
