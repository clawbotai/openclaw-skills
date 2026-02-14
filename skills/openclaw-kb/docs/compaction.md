# Compaction

## What it is
Compaction summarizes older conversation into a compact summary, keeping recent messages intact. Persists in session JSONL history.

## Auto-compaction (default on)
Triggers when session nears context window. May run a memory flush turn first (to save durable notes to disk).

## Manual compaction
`/compact [instructions]` — force a compaction pass with optional focus instructions.

## Configuration
agents.defaults.compaction:
- mode: default | safeguard (chunked summarization for long histories)
- memoryFlush.enabled: true — silent turn before compaction to store memories

## Compaction vs pruning
- Compaction: summarizes and persists in JSONL
- Session pruning: trims old tool results in-memory only, per request

## Tips
- Use /compact when sessions feel stale
- Large tool outputs are truncated; pruning further reduces buildup
- /new or /reset starts fresh session
