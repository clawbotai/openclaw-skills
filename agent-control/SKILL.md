---
name: agent-control
description: Restart or reconfigure agents directly from chat. Use when the user wants to switch models, stop the current session, or restart the OpenClaw gateway without leaving the conversation.
---

# Agent Control Skill

Use this skill whenever the user asks to:
- Check which model an agent is using.
- Change the default/main agent model or its fallbacks.
- Kill/reset the current session so a new one starts with fresh settings.
- Restart the OpenClaw gateway from within the chat.

## Core Workflow

1. **Confirm intent + scope.** Clarify which agent (`main`, `anthropic`, etc.) and action (change model, restart gateway, stop session) the user wants. Log the request in `progress.md` before taking action.
2. **Gather current state.** Run `session_status` (for the active chat) and/or `openclaw sessions` via `exec` to capture the current model and session id. Note the session key (usually `agent:main:main`).
3. **Choose the action path:**
   - *Change model only:* Update `~/.openclaw/openclaw.json` using the helper script below, then inform the user to restart/stop the session.
   - *Stop current session:* Remove the stored session entry so the next message spins up a fresh session with new defaults.
   - *Restart gateway:* Issue a gateway restart when the user wants a clean slate across all sessions.
4. **Verify + report.** After any action, re-run `session_status` or `openclaw sessions` to confirm the change. Summarize what changed and any remaining steps for the user (e.g., “open a new chat now to pick up the Anthropic model”).
5. **Log the action.** Append a short note to `progress.md` (and `findings.md` if this introduces a new lesson) covering what you changed and why. This keeps Layer 0 telemetry consistent.

## Helper Script

`skills/agent-control/scripts/agent_control.py` wraps the common control actions so you do not need to hand-edit config files or session stores. Run it via `python3` or execute it directly.

### Commands

```bash
# Show current defaults + per-agent model assignments
python3 skills/agent-control/scripts/agent_control.py status

# Set the main agent (and defaults) to Claude Opus, overwrite fallbacks
python3 skills/agent-control/scripts/agent_control.py set-model --agent main --model anthropic/claude-opus-4-6 --fallbacks "openai/gpt-5.1-codex,voyage/*"

# Stop the current main session (forces new session on next message)
python3 skills/agent-control/scripts/agent_control.py stop-session --agent main --key agent:main:main

# Restart the OpenClaw gateway service
python3 skills/agent-control/scripts/agent_control.py restart-gateway
```

Each command prints a short status message. The script automatically:
- Updates both `agents.defaults.model.primary` and the specific agent entry in `openclaw.json`.
- Removes the JSONL transcript + lock file for the specified session key when stopping a session.
- Calls `openclaw gateway restart` for gateway restarts (watch for transient disconnects).

## Safety & Approvals

- **Zero-trust reminder:** Confirm the user’s explicit approval before modifying models or restarting services. Note their confirmation in `progress.md`.
- **Back up before destructive steps:** If you need to preserve session transcripts, copy the JSONL file before running `stop-session`.
- **Communicate downtime:** A gateway restart briefly disconnects all channels. Warn the user and wait for the reconnect log before proceeding.

## Post-Action Checklist

After executing any control action:
1. Run `openclaw sessions` (or `session_status`) to ensure the session list matches expectations (old entry removed, new session id once the user sends another message).
2. If you changed models, re-open the chat (or have the user do so) and confirm the new model via `session_status`.
3. Update planning files (`task_plan.md` + `progress.md`) so Layer 0 history reflects what changed and why.
4. If the change addressed a recurring pain point, capture the lesson in `findings.md` and flag for `reflect-learn` ingestion.

By following this workflow, you can restart the agent or switch models entirely within the chat, no GUI/CLI hopping required.
