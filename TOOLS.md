# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Email

- **Address:** clawaibot@icloud.com
- **Credentials:** macOS Keychain → service: `icloud-email`, account: `clawaibot@icloud.com`
- **Retrieve:** `security find-generic-password -a "clawaibot@icloud.com" -s "icloud-email" -w`

## Monitored Skill Execution

All skill script invocations should go through the monitored runner so errors are logged, classified, and fed into the evolutionary loop's repair pipeline.

```bash
# Via convenience wrapper
bin/skillrun <skill-name> [--timeout N] -- <command...>

# Direct
python3 skills/skill-lifecycle/scripts/run_monitored.py <skill-name> -- <command...>
```

- Exit code 98 = skill is quarantined (circuit breaker OPEN)
- Errors auto-logged to `memory/skill-errors.json`
- Check health: `OPENCLAW_WORKSPACE=. python3 skills/skill-lifecycle/scripts/monitor.py status`
- View repair tickets: `OPENCLAW_WORKSPACE=. python3 skills/skill-lifecycle/scripts/monitor.py tickets`

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
