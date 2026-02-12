# SPECIFICATION.md — Email Manager Rebuild
*Generated: 2026-02-12 | Confidence: High (based on source review + domain knowledge)*

## Objective

Rebuild the email-manager skill to be production-grade: robust error handling, connection management with retries, context manager patterns, proper IMAP UID handling, and integration with the skill-lifecycle monitor. The current implementation works but has reliability gaps that cause failures in autonomous (heartbeat) operation.

## Current State Analysis

### What Works
- Full IMAP/SMTP command coverage (count, inbox, read, send, reply, forward, search, triage, etc.)
- Structured JSON output for all commands
- macOS Keychain credential management
- Multi-provider support (iCloud, Gmail, Outlook)
- Priority/category classification for triage
- Clean CLI with argparse

### Problems Found

1. **No connection retry logic** — Any transient network/auth failure crashes the whole command. IMAP connections are fragile.
2. **No context managers** — `connect_imap()` returns a raw connection with no cleanup guarantee. If an exception occurs mid-command, the connection leaks.
3. **`output_error` calls `sys.exit(1)`** — This means errors can't be caught programmatically. The monitor can only see exit codes, not structured errors.
4. **IMAP UID inconsistency** — Some commands use `conn.fetch(uid, ...)` but UIDs from `conn.search()` are sequence numbers unless `conn.uid()` is used. This can cause wrong-message bugs.
5. **No connection timeout** — `IMAP4_SSL()` can hang indefinitely on DNS or network issues.
6. **Body preview in triage is fragile** — The `BODY.PEEK[TEXT]<0.500>` fetch may return encoded content that doesn't decode cleanly.
7. **Thread detection is subject-only** — Misses threads where subject changes. Should use References/In-Reply-To headers.
8. **HTML-to-text is basic** — Regex-based, misses tables, nested structures.
9. **No rate limiting** — Rapid successive calls could hit provider limits.
10. **`cmd_reply` uses a mock class** — The `SendArgs` pattern is fragile and won't survive refactoring.

## Requirements

### Functional (same as current — no feature changes)
- All existing commands remain: count, inbox, read, send, reply, forward, search, folders, mark, delete, triage, thread, batch-mark, digest, config
- JSON output format unchanged (backward compatible)
- Error codes unchanged

### Non-Functional (the rebuild targets)

| Requirement | Current | Target |
|-------------|---------|--------|
| Connection retry | None | 3 retries with exponential backoff |
| Connection cleanup | Manual logout | Context manager (`with` statement) |
| Connection timeout | None | 30s connect, 60s operation |
| Error handling | sys.exit(1) | Raise exceptions, catch at top-level |
| IMAP UID mode | Inconsistent | Use `conn.uid()` for all operations |
| Body decoding | Best-effort | Graceful fallback chain with charset detection |
| Logging | None | stderr debug logging (off by default, `--debug` flag) |

## Technical Decisions

### Decision 1: Context Manager for IMAP
- **Chosen:** `IMAPConnection` context manager class
- **Rationale:** Guarantees cleanup on exception, enables retry logic in one place
- **Trade-offs:** Slightly more code, but eliminates connection leak class of bugs

### Decision 2: Exception-Based Error Flow
- **Chosen:** Custom `EmailError` exception hierarchy, caught at CLI boundary
- **Rationale:** Functions become composable (reply calls send internally). `sys.exit()` only at the outermost CLI layer.
- **Trade-offs:** Need to catch exceptions at the top level

### Decision 3: IMAP UID Commands
- **Chosen:** Use `conn.uid('SEARCH', ...)` and `conn.uid('FETCH', ...)` throughout
- **Rationale:** Sequence numbers change between sessions. UIDs are stable identifiers.
- **Trade-offs:** Minor API difference, but correct behavior

### Decision 4: Retry with Backoff
- **Chosen:** 3 retries, backoff [1s, 2s, 4s], only for connection/transient errors
- **Rationale:** iCloud IMAP occasionally drops connections. Retries fix 90%+ of transient failures.
- **Trade-offs:** Slower failure for genuine auth errors (but we detect AUTH_FAILED and skip retries)

## Acceptance Criteria

- [ ] All existing commands produce identical JSON output format
- [ ] `python3 scripts/email_client.py count` works with valid credentials
- [ ] Connection failures retry 3 times before failing
- [ ] IMAP connections are cleaned up even on exception
- [ ] All IMAP operations use UID mode
- [ ] Error codes in JSON output match existing set
- [ ] `--debug` flag enables stderr logging
- [ ] No external dependencies (stdlib only)
- [ ] Python 3.9 compatible

## Open Questions
- Should we add IDLE support for push notifications? (Deferred — not needed for heartbeat polling)
- OAuth2 for Gmail/Outlook? (Deferred — app passwords work, OAuth adds significant complexity)

## Sources
1. [Python imaplib docs](https://docs.python.org/3/library/imaplib.html) — Official reference
2. Current email_client.py source (1115 lines) — Reviewed in full
3. iCloud IMAP requirements — App-specific passwords required, standard IMAP4 compliance
