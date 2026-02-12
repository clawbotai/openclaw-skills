---
name: email-manager
version: 1.0.0
description: "Full IMAP/SMTP email client optimized for autonomous AI agents. Structured JSON output, priority detection, smart triage, threaded conversations, and batch operations."
triggers:
  - check email
  - read email
  - send email
  - email
  - inbox
  - triage
metadata:
  openclaw:
    emoji: "📧"
    category: "communication"
---

# Email Manager 📧

Full email access optimized for autonomous AI operation. Every command returns structured JSON. Credentials live in the macOS Keychain — never in files.

---

## Setup

### 1. Store Credentials in Keychain

iCloud (and Gmail with 2FA) require **app-specific passwords**:

1. Go to https://appleid.apple.com → Sign-In and Security → App-Specific Passwords
2. Generate a password, name it "OpenClaw Email"
3. Store it:

```bash
security add-generic-password -a "clawaibot@icloud.com" -s "icloud-email" -w '<app-specific-password>' -U
```

### 2. Verify Access

```bash
python3 scripts/email_client.py count
```

Expected: `{"status": "ok", "inbox": {"total": N, "unread": N, "flagged": N}}`

### 3. Configure (Optional)

```bash
python3 scripts/email_client.py config --show
python3 scripts/email_client.py config --set provider=icloud
python3 scripts/email_client.py config --set signature="— Sent via OpenClaw"
```

---

## Commands

All commands output JSON. The agent parses the output directly.

### Read Operations

| Command | What it does |
|---------|-------------|
| `count` | Inbox stats: total, unread, flagged |
| `inbox [--limit N] [--unread]` | List messages with metadata |
| `read <uid>` | Full message: body, headers, attachments |
| `search <query> [--limit N]` | Search by subject, from, or body |
| `folders` | List all mailbox folders |
| `thread <uid>` | Get full conversation thread |
| `digest [--hours N]` | Activity summary for last N hours |
| `triage [--limit N]` | **Smart triage**: classify unread by priority |

### Write Operations

| Command | What it does |
|---------|-------------|
| `send --to X --subject X --body X [--html] [--attach file]` | Send email |
| `reply <uid> --body X` | Reply to a message |
| `forward <uid> --to X [--body X]` | Forward a message |
| `mark <uid> --read\|--unread\|--flag\|--unflag\|--archive` | Change message flags |
| `batch-mark --uids 1,2,3 --read` | Mark multiple at once |
| `delete <uid>` | Move to trash |

---

## Autonomous Workflows

### Heartbeat Email Check

During heartbeat, run this sequence:

```bash
# 1. Quick stats
python3 scripts/email_client.py count

# 2. If unread > 0, triage them
python3 scripts/email_client.py triage --limit 20

# 3. Report urgent/important to user, auto-archive low-priority newsletters
```

### Smart Triage

The `triage` command classifies every unread message:

**Priority levels:**
- `urgent` — Contains "ASAP", "emergency", "deadline", "action required"
- `important` — Contains "please review", "invoice", "meeting", "contract"
- `normal` — Default for personal emails
- `low` — Newsletters, no-reply addresses, marketing

**Categories:**
- `personal` — From a real person
- `transactional` — Receipts, confirmations, shipping
- `newsletter` — Contains "unsubscribe"
- `notification` — From no-reply addresses

### Auto-Response Pattern

```bash
# Read the urgent message
python3 scripts/email_client.py read <uid>

# Reply
python3 scripts/email_client.py reply <uid> --body "Acknowledged. I'll handle this by EOD."

# Mark as flagged for follow-up
python3 scripts/email_client.py mark <uid> --flag
```

### Batch Cleanup

```bash
# Mark all newsletter UIDs as read
python3 scripts/email_client.py batch-mark --uids 101,102,103 --read
```

---

## JSON Output Format

Every command returns structured JSON:

```json
{
  "status": "ok",
  "messages": [...],
  "count": 5
}
```

Errors:
```json
{
  "status": "error",
  "code": "AUTH_FAILED",
  "message": "Authentication failed. iCloud requires an app-specific password..."
}
```

Error codes: `AUTH_FAILED`, `AUTH_KEYCHAIN`, `AUTH_PLATFORM`, `IMAP_ERROR`, `SMTP_ERROR`, `NOT_FOUND`, `FILE_NOT_FOUND`, `INVALID_ARG`

---

## Provider Support

| Provider | IMAP | SMTP | Notes |
|----------|------|------|-------|
| iCloud | ✅ | ✅ | Requires app-specific password |
| Gmail | ✅ | ✅ | Requires app-specific password |
| Outlook | ✅ | ✅ | OAuth may be required for some orgs |
| Custom | ✅ | ✅ | Set host/port via config |

Switch provider:
```bash
python3 scripts/email_client.py config --set provider=gmail
python3 scripts/email_client.py config --set keychain_account=user@gmail.com
```

---

## Configuration

Stored in `scripts/config.json`. Defaults:

| Key | Default | Description |
|-----|---------|-------------|
| `provider` | `icloud` | Email provider preset |
| `keychain_service` | `icloud-email` | macOS Keychain service name |
| `keychain_account` | `clawaibot@icloud.com` | Keychain account |
| `default_from` | `clawaibot@icloud.com` | Sender address |
| `signature` | `""` | Appended to outgoing emails |
| `max_body_chars` | `10000` | Body truncation limit |
| `triage_keywords_urgent` | `[...]` | Keywords that trigger "urgent" |
| `triage_keywords_important` | `[...]` | Keywords that trigger "important" |
| `triage_keywords_low` | `[...]` | Keywords that trigger "low" |

---

## Security

- **Credentials**: macOS Keychain only. Never in files, env vars, or logs.
- **No plaintext passwords** anywhere in this skill.
- **App-specific passwords** are scoped — they can't change your Apple ID.
- **JSON output** never includes credentials.
- **Read-only by default** — `inbox`, `search`, `triage` use IMAP `readonly=True`.

---

## File Structure

```
email-manager/
├── SKILL.md             # This file
├── _meta.json           # Skill metadata
└── scripts/
    ├── email_client.py  # Full client (36KB, zero external dependencies)
    └── config.json      # Runtime config (auto-created on first --set)
```
