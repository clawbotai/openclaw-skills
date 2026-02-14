# Session Management

## DM scope (session.dmScope)
- **main** (default): all DMs share the main session (fine for single-user)
- **per-peer**: isolate by sender id across channels
- **per-channel-peer**: isolate per channel + sender (recommended for multi-user)
- **per-account-channel-peer**: isolate per account + channel + sender (recommended for multi-account)

⚠️ **Security Warning**: Without dmScope isolation, all users share the same conversation context — can leak private info between users.

## Session keys
- Direct chats: agent:<agentId>:<mainKey> (default main)
- Groups: agent:<agentId>:<channel>:group:<groupId>
- Cron: cron:<jobId>
- Hooks: hook:<hookId>
- Nodes: node-<nodeId>

## identityLinks
Map provider-prefixed peer ids to canonical identity for cross-channel session sharing.

## Lifecycle
- **Daily reset**: defaults to 4:00 AM local time
- **Idle reset**: optional sliding window (idleMinutes)
- Both configured: whichever expires first wins
- **resetByType**: per direct/group/thread overrides
- **resetByChannel**: per-channel overrides
- **Reset triggers**: /new, /reset (plus extras in resetTriggers)

## Send policy
Block delivery for specific session types:
```json
{
  "sendPolicy": {
    "rules": [
      { "action": "deny", "match": { "channel": "discord", "chatType": "group" } }
    ],
    "default": "allow"
  }
}
```
Runtime: /send on|off|inherit

## Where state lives
- Store: ~/.openclaw/agents/<id>/sessions/sessions.json
- Transcripts: ~/.openclaw/agents/<id>/sessions/<sessionId>.jsonl
- Gateway is the source of truth (not local clients)

## Inspecting
- `openclaw status` — store path + recent sessions
- `openclaw sessions --json` — dump all entries
- `/status` in chat — session context usage
- `/context list|detail` — system prompt contents
- `/stop` — abort current run
- `/compact` — summarize older context
