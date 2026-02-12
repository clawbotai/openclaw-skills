#!/usr/bin/env python3
"""
Email Manager — Autonomous AI Email Client (v2)
=================================================
Full IMAP/SMTP access optimized for AI agent consumption.
Rebuilt with: connection retries, context managers, UID mode,
exception-based error flow, and debug logging.

All commands output structured JSON for reliable parsing.
Credentials are pulled from macOS Keychain at runtime.

Supports: iCloud, Gmail, Outlook, any IMAP/SMTP provider.
Zero external dependencies (stdlib only). Python 3.9+.
"""

from __future__ import annotations

import argparse
import email as email_lib
import email.mime.multipart
import email.mime.text
import email.mime.application
import email.utils
import html as html_lib
import imaplib
import json
import logging
import mimetypes
import os
import re
import smtplib
import socket
import ssl
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

logger = logging.getLogger("email-manager")


# ---------------------------------------------------------------------------
# Cross-skill integration (optional — gracefully degrades if unavailable)
# ---------------------------------------------------------------------------

def _try_import_integration():
    """Attempt to import shared integration clients.

    Returns (memory_client, guardrails_client) — either may be None.
    """
    _mem = None  # type: Any
    _guard = None  # type: Any
    try:
        # Add workspace root to path for lib/ imports
        workspace = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if workspace not in sys.path:
            sys.path.insert(0, workspace)
        from lib import memory_client as _mem
    except ImportError:
        pass
    try:
        from lib import guardrails_client as _guard
    except ImportError:
        pass
    return _mem, _guard


def _guardrails_check_send(to: str, subject: str) -> None:
    """Check send_email action against guardrails before sending.

    Raises EmailError if the action is denied. Silently passes if
    guardrails is unavailable.
    """
    _, guard = _try_import_integration()
    if guard is None:
        return
    try:
        result = guard.check_action(
            "send_email",
            target=to,
            context=f"Subject: {subject}",
        )
        if not result.get("allowed", True):
            raise EmailError(
                f"Guardrails blocked send to {to}: {result.get('reasons', [])}",
                code="GUARDRAILS_DENIED",
            )
        if result.get("requires_confirmation", False):
            logger.warning(
                "Guardrails: send to %s is %s risk — %s",
                to, result.get("tier_label", "?"), result.get("reasons", [])
            )
    except RuntimeError as exc:
        logger.debug("Guardrails check unavailable: %s", exc)


def _memory_log_email(action: str, to: str, subject: str, **extra: Any) -> None:
    """Log an email action to agent-memory for future recall.

    Silently no-ops if agent-memory is unavailable.
    """
    mem, _ = _try_import_integration()
    if mem is None:
        return
    try:
        text = f"Email {action}: to={to}, subject={subject}"
        if extra:
            text += ", " + ", ".join(f"{k}={v}" for k, v in extra.items())
        mem.remember(text, memory_type="episodic")
    except Exception as exc:
        logger.debug("Memory log failed (non-fatal): %s", exc)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class EmailError(Exception):
    """Base email error with structured code."""
    def __init__(self, message: str, code: str = "ERROR"):
        super().__init__(message)
        self.code = code


class AuthError(EmailError):
    """Authentication failure."""
    def __init__(self, message: str, code: str = "AUTH_FAILED"):
        super().__init__(message, code)


class IMAPError(EmailError):
    """IMAP operation failure."""
    def __init__(self, message: str):
        super().__init__(message, "IMAP_ERROR")


class NotFoundError(EmailError):
    """Message not found."""
    def __init__(self, uid: str):
        super().__init__(f"Message {uid} not found.", "NOT_FOUND")


# ---------------------------------------------------------------------------
# Provider Configurations
# ---------------------------------------------------------------------------

PROVIDERS = {
    "icloud": {
        "imap_host": "imap.mail.me.com",
        "imap_port": 993,
        "smtp_host": "smtp.mail.me.com",
        "smtp_port": 587,
        "smtp_tls": "starttls",
    },
    "gmail": {
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_tls": "starttls",
    },
    "outlook": {
        "imap_host": "outlook.office365.com",
        "imap_port": 993,
        "smtp_host": "smtp.office365.com",
        "smtp_port": 587,
        "smtp_tls": "starttls",
    },
}

DEFAULT_CONFIG = {
    "provider": "icloud",
    "keychain_service": "icloud-email",
    "keychain_account": "clawbotai@icloud.com",
    "default_from": "clawbotai@icloud.com",
    "signature": "",
    "max_body_chars": 10000,
    "connect_timeout": 30,
    "operation_timeout": 60,
    "max_retries": 3,
    "retry_backoff": [1, 2, 4],
    "triage_keywords_urgent": [
        "urgent", "asap", "emergency", "critical", "immediate",
        "deadline", "action required", "time sensitive",
    ],
    "triage_keywords_important": [
        "important", "please review", "follow up", "reminder",
        "invoice", "payment", "contract", "meeting", "schedule",
    ],
    "triage_keywords_low": [
        "newsletter", "unsubscribe", "no-reply", "noreply",
        "notification", "digest", "promotional", "marketing",
    ],
}


def get_config() -> dict:
    """Load config from file or return defaults."""
    config_path = Path(__file__).parent / "config.json"
    config = DEFAULT_CONFIG.copy()
    if config_path.exists():
        try:
            with open(config_path) as f:
                user_config = json.load(f)
            config.update(user_config)
        except Exception:
            pass
    return config


def save_config(config: dict) -> None:
    """Save config to file."""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------

def output(data: Any) -> None:
    """Print structured JSON output for the agent."""
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def output_error(message: str, code: str = "ERROR") -> None:
    """Print structured error and exit."""
    output({"status": "error", "code": code, "message": message})
    sys.exit(1)


def output_ok(message: str, **extra) -> None:
    """Print structured success."""
    data = {"status": "ok", "message": message}
    data.update(extra)
    output(data)


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

def get_credentials(config: dict) -> Tuple[str, str]:
    """Retrieve email credentials from macOS Keychain or environment."""
    address = os.environ.get("EMAIL_ADDRESS", config["keychain_account"])
    password = os.environ.get("EMAIL_PASSWORD")

    if not password:
        try:
            result = subprocess.run(
                ["security", "find-generic-password",
                 "-a", config["keychain_account"],
                 "-s", config["keychain_service"], "-w"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                password = result.stdout.strip()
            else:
                raise AuthError(
                    "Could not retrieve password from macOS Keychain. "
                    f"Run: security add-generic-password -a '{config['keychain_account']}' "
                    f"-s '{config['keychain_service']}' -w '<app-specific-password>'",
                    code="AUTH_KEYCHAIN",
                )
        except FileNotFoundError:
            raise AuthError("'security' command not found — not macOS?", code="AUTH_PLATFORM")

    return address, password


# ---------------------------------------------------------------------------
# Connection Management (Context Managers with Retry)
# ---------------------------------------------------------------------------

# Errors that should NOT be retried
NON_RETRYABLE = ("AUTHENTICATIONFAILED", "AUTH_KEYCHAIN", "AUTH_PLATFORM", "AUTH_FAILED")


def _is_retryable(exc: Exception) -> bool:
    """Check if an exception is transient and worth retrying."""
    msg = str(exc).upper()
    for pattern in NON_RETRYABLE:
        if pattern in msg:
            return False
    # Retryable: timeouts, connection errors, temporary IMAP failures
    if isinstance(exc, (socket.timeout, socket.gaierror, ConnectionError, OSError)):
        return True
    if isinstance(exc, imaplib.IMAP4.error):
        return True
    return False


@contextmanager
def imap_connection(
    config: dict,
    folder: str = "INBOX",
    readonly: bool = False,
) -> Generator[imaplib.IMAP4_SSL, None, None]:
    """
    Context manager for IMAP connections with retry and cleanup.

    Usage:
        with imap_connection(config, readonly=True) as conn:
            conn.uid('SEARCH', None, 'ALL')
    """
    address, password = get_credentials(config)
    provider = PROVIDERS.get(config["provider"], PROVIDERS["icloud"])
    timeout = config.get("connect_timeout", 30)
    max_retries = config.get("max_retries", 3)
    backoff = config.get("retry_backoff", [1, 2, 4])

    conn = None  # type: Optional[imaplib.IMAP4_SSL]
    last_exc = None  # type: Optional[Exception]

    for attempt in range(max_retries):
        try:
            ctx = ssl.create_default_context()
            conn = imaplib.IMAP4_SSL(
                provider["imap_host"],
                provider["imap_port"],
                ssl_context=ctx,
                timeout=timeout,
            )
            conn.login(address, password)
            conn.select(folder, readonly=readonly)
            logger.debug("IMAP connected (attempt %d)", attempt + 1)
            break
        except Exception as exc:
            last_exc = exc
            if conn:
                try:
                    conn.logout()
                except Exception:
                    pass
                conn = None

            if not _is_retryable(exc) or attempt == max_retries - 1:
                break

            delay = backoff[attempt] if attempt < len(backoff) else backoff[-1]
            logger.warning("IMAP connect failed (attempt %d): %s. Retrying in %ds...", attempt + 1, exc, delay)
            time.sleep(delay)

    if conn is None:
        exc = last_exc
        err = str(exc) if exc else "Unknown error"
        if "AUTHENTICATIONFAILED" in err.upper():
            raise AuthError(
                "Authentication failed. iCloud requires an app-specific password. "
                "Go to https://appleid.apple.com → Sign-In and Security → "
                "App-Specific Passwords → Generate one → then update keychain: "
                f"security add-generic-password -a '{config['keychain_account']}' "
                f"-s '{config['keychain_service']}' -w '<new-app-password>' -U",
            )
        raise IMAPError(f"IMAP connection failed after {max_retries} attempts: {err}")

    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass
        try:
            conn.logout()
        except Exception:
            pass
        logger.debug("IMAP connection closed")


@contextmanager
def smtp_connection(config: dict) -> Generator[smtplib.SMTP, None, None]:
    """Context manager for SMTP connections with retry and cleanup."""
    address, password = get_credentials(config)
    provider = PROVIDERS.get(config["provider"], PROVIDERS["icloud"])
    max_retries = config.get("max_retries", 3)
    backoff = config.get("retry_backoff", [1, 2, 4])

    server = None  # type: Optional[smtplib.SMTP]
    last_exc = None  # type: Optional[Exception]

    for attempt in range(max_retries):
        try:
            server = smtplib.SMTP(
                provider["smtp_host"],
                provider["smtp_port"],
                timeout=config.get("connect_timeout", 30),
            )
            server.ehlo()
            if provider.get("smtp_tls") == "starttls":
                server.starttls()
                server.ehlo()
            server.login(address, password)
            logger.debug("SMTP connected (attempt %d)", attempt + 1)
            break
        except Exception as exc:
            last_exc = exc
            if server:
                try:
                    server.quit()
                except Exception:
                    pass
                server = None

            if not _is_retryable(exc) or attempt == max_retries - 1:
                break

            delay = backoff[attempt] if attempt < len(backoff) else backoff[-1]
            logger.warning("SMTP connect failed (attempt %d): %s. Retrying in %ds...", attempt + 1, exc, delay)
            time.sleep(delay)

    if server is None:
        raise EmailError(f"SMTP connection failed after {max_retries} attempts: {last_exc}", "SMTP_ERROR")

    try:
        yield server
    finally:
        try:
            server.quit()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Email Parsing Utilities
# ---------------------------------------------------------------------------

def decode_mime_header(raw: Optional[str]) -> str:
    """Decode MIME-encoded header into readable string."""
    if not raw:
        return ""
    parts = decode_header(raw)
    decoded = []
    for data, charset in parts:
        if isinstance(data, bytes):
            decoded.append(data.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(data)
    return " ".join(decoded).strip()


def extract_body(msg: email_lib.message.Message, max_chars: int = 10000) -> Tuple[str, str]:
    """Extract (plain_text, html_text) from a message with safe decoding."""
    plain = ""
    html_body = ""

    def _decode_payload(part: email_lib.message.Message) -> str:
        payload = part.get_payload(decode=True)
        if not payload:
            return ""
        # Try declared charset first, then common fallbacks
        charset = part.get_content_charset()
        for enc in [charset, "utf-8", "latin-1", "ascii"]:
            if enc:
                try:
                    return payload.decode(enc)
                except (UnicodeDecodeError, LookupError):
                    continue
        return payload.decode("utf-8", errors="replace")

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            disp = str(part.get("Content-Disposition", ""))
            if "attachment" in disp:
                continue
            if ct == "text/plain" and not plain:
                plain = _decode_payload(part)
            elif ct == "text/html" and not html_body:
                html_body = _decode_payload(part)
    else:
        text = _decode_payload(msg)
        if msg.get_content_type() == "text/html":
            html_body = text
        else:
            plain = text

    return plain[:max_chars], html_body[:max_chars]


def html_to_text(html_str: str) -> str:
    """Convert HTML to readable plain text."""
    text = re.sub(r'<br\s*/?>', '\n', html_str, flags=re.I)
    text = re.sub(r'</?p[^>]*>', '\n', text, flags=re.I)
    text = re.sub(r'<li[^>]*>', '\n• ', text, flags=re.I)
    text = re.sub(r'<h[1-6][^>]*>', '\n## ', text, flags=re.I)
    text = re.sub(r'</h[1-6]>', '\n', text, flags=re.I)
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>', r'\2 (\1)', text, flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_lib.unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def get_attachments(msg: email_lib.message.Message) -> List[Dict]:
    """List attachments with metadata."""
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            disp = str(part.get("Content-Disposition", ""))
            if "attachment" in disp or ("inline" in disp and part.get_filename()):
                filename = decode_mime_header(part.get_filename())
                if filename:
                    payload = part.get_payload(decode=True) or b""
                    attachments.append({
                        "filename": filename,
                        "content_type": part.get_content_type(),
                        "size_bytes": len(payload),
                    })
    return attachments


def parse_date(date_str: Optional[str]) -> Optional[str]:
    """Parse email date to ISO format."""
    if not date_str:
        return None
    try:
        parsed = email_lib.utils.parsedate_to_datetime(date_str)
        return parsed.isoformat()
    except Exception:
        return date_str


def extract_email_address(from_header: str) -> str:
    """Extract just the email address from a From header."""
    match = re.search(r'<([^>]+)>', from_header)
    if match:
        return match.group(1).lower()
    return from_header.strip().lower()


# ---------------------------------------------------------------------------
# IMAP UID Helpers
# ---------------------------------------------------------------------------

def uid_search(conn: imaplib.IMAP4_SSL, criteria: str) -> List[bytes]:
    """Search using UID mode. Returns list of UID byte strings."""
    typ, data = conn.uid("SEARCH", None, criteria)
    if typ != "OK" or not data[0]:
        return []
    return data[0].split()


def uid_fetch(conn: imaplib.IMAP4_SSL, uid: bytes, parts: str) -> Optional[tuple]:
    """Fetch a message by UID. Returns the data tuple or None."""
    typ, data = conn.uid("FETCH", uid, parts)
    if typ != "OK" or not data or not data[0]:
        return None
    return data


# ---------------------------------------------------------------------------
# Triage / Priority Engine
# ---------------------------------------------------------------------------

def classify_priority(
    from_addr: str,
    subject: str,
    body_preview: str,
    config: dict,
) -> Dict[str, Any]:
    """Classify email priority for autonomous triage."""
    text = f"{subject} {body_preview}".lower()
    from_lower = from_addr.lower()
    signals = []

    priority = "normal"

    for kw in config.get("triage_keywords_urgent", []):
        if kw in text:
            priority = "urgent"
            signals.append(f"urgent keyword: '{kw}'")
            break

    if priority == "normal":
        for kw in config.get("triage_keywords_important", []):
            if kw in text:
                priority = "important"
                signals.append(f"important keyword: '{kw}'")
                break

    for kw in config.get("triage_keywords_low", []):
        if kw in from_lower or kw in text:
            priority = "low"
            signals.append(f"low-priority signal: '{kw}'")
            break

    # Category classification
    category = "unknown"
    if "noreply" in from_lower or "no-reply" in from_lower:
        category = "notification"
    elif "unsubscribe" in text:
        category = "newsletter"
    elif any(kw in text for kw in ["receipt", "order", "invoice", "confirmation", "shipping"]):
        category = "transactional"
    elif "@" in from_lower and not any(x in from_lower for x in ["noreply", "notify", "alert", "news"]):
        category = "personal"

    return {"priority": priority, "category": category, "signals": signals}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_count(args: argparse.Namespace, config: dict) -> None:
    """Inbox statistics."""
    with imap_connection(config, readonly=True) as conn:
        all_uids = uid_search(conn, "ALL")
        unread_uids = uid_search(conn, "(UNSEEN)")
        flagged_uids = uid_search(conn, "(FLAGGED)")

    output({
        "status": "ok",
        "inbox": {
            "total": len(all_uids),
            "unread": len(unread_uids),
            "flagged": len(flagged_uids),
        }
    })


def cmd_inbox(args: argparse.Namespace, config: dict) -> None:
    """List inbox messages with metadata."""
    with imap_connection(config, readonly=True) as conn:
        criteria = "(UNSEEN)" if args.unread else "ALL"
        uids = uid_search(conn, criteria)
        uids = uids[-(args.limit):]
        uids.reverse()

        messages = []
        for uid in uids:
            data = uid_fetch(conn, uid, "(UID FLAGS BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE MESSAGE-ID)])")
            if not data:
                continue

            raw_header = data[0][1]
            flags_raw = data[0][0].decode() if data[0][0] else ""
            msg = email_lib.message_from_bytes(raw_header)

            messages.append({
                "uid": uid.decode(),
                "from": decode_mime_header(msg.get("From", "")),
                "to": decode_mime_header(msg.get("To", "")),
                "subject": decode_mime_header(msg.get("Subject", "(no subject)")),
                "date": parse_date(msg.get("Date", "")),
                "message_id": msg.get("Message-ID", ""),
                "read": "\\Seen" in flags_raw,
                "flagged": "\\Flagged" in flags_raw,
            })

    output({"status": "ok", "messages": messages, "count": len(messages)})


def cmd_read(args: argparse.Namespace, config: dict) -> None:
    """Read full message content."""
    uid = str(args.uid).encode()
    with imap_connection(config) as conn:
        data = uid_fetch(conn, uid, "(RFC822)")
        if not data:
            raise NotFoundError(str(args.uid))

        raw = data[0][1]
        msg = email_lib.message_from_bytes(raw)

    max_chars = config.get("max_body_chars", 10000)
    plain, html_body = extract_body(msg, max_chars)
    body = plain if plain else html_to_text(html_body)
    body = body[:max_chars]

    output({
        "status": "ok",
        "message": {
            "uid": args.uid,
            "from": decode_mime_header(msg.get("From", "")),
            "to": decode_mime_header(msg.get("To", "")),
            "cc": decode_mime_header(msg.get("Cc", "")),
            "subject": decode_mime_header(msg.get("Subject", "")),
            "date": parse_date(msg.get("Date", "")),
            "message_id": msg.get("Message-ID", ""),
            "in_reply_to": msg.get("In-Reply-To", ""),
            "body": body,
            "body_format": "plain" if plain else "html_converted",
            "attachments": get_attachments(msg),
            "has_attachments": len(get_attachments(msg)) > 0,
        }
    })


def _build_message(
    config: dict,
    to: str,
    subject: str,
    body: str,
    html: bool = False,
    attachments: Optional[List[str]] = None,
    in_reply_to: Optional[str] = None,
) -> email_lib.mime.multipart.MIMEMultipart:
    """Build a MIME message. Shared by send/reply/forward."""
    address = config["default_from"]
    msg = email_lib.mime.multipart.MIMEMultipart()
    msg["From"] = address
    msg["To"] = to
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to

    if config.get("signature"):
        body += f"\n\n{config['signature']}"

    content_type = "html" if html else "plain"
    msg.attach(email_lib.mime.text.MIMEText(body, content_type))

    for filepath in (attachments or []):
        path = Path(filepath)
        if not path.exists():
            raise EmailError(f"Attachment not found: {filepath}", "FILE_NOT_FOUND")
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        with open(path, "rb") as f:
            attachment = email_lib.mime.application.MIMEApplication(f.read(), Name=path.name)
        attachment["Content-Disposition"] = f'attachment; filename="{path.name}"'
        msg.attach(attachment)

    return msg


def _send_message(config: dict, msg: email_lib.mime.multipart.MIMEMultipart, to: str) -> None:
    """Send a built MIME message via SMTP."""
    address = config["default_from"]
    recipients = [addr.strip() for addr in to.split(",")]
    with smtp_connection(config) as server:
        server.sendmail(address, recipients, msg.as_string())


def cmd_send(args: argparse.Namespace, config: dict) -> None:
    """Send an email (with guardrails pre-check and memory logging)."""
    # Integration: check guardrails before sending
    _guardrails_check_send(args.to, args.subject)

    msg = _build_message(
        config,
        to=args.to,
        subject=args.subject,
        body=args.body,
        html=getattr(args, "html", False),
        attachments=getattr(args, "attach", None),
    )
    _send_message(config, msg, args.to)

    # Integration: log to memory
    _memory_log_email("sent", args.to, args.subject)

    output_ok(f"Email sent to {args.to}", to=args.to, subject=args.subject, from_addr=config["default_from"])


def cmd_reply(args: argparse.Namespace, config: dict) -> None:
    """Reply to a message."""
    uid = str(args.uid).encode()
    with imap_connection(config, readonly=True) as conn:
        data = uid_fetch(conn, uid, "(RFC822)")
        if not data:
            raise NotFoundError(str(args.uid))
        original = email_lib.message_from_bytes(data[0][1])

    reply_to = decode_mime_header(original.get("Reply-To") or original.get("From"))
    to_addr = extract_email_address(reply_to)
    subject = decode_mime_header(original.get("Subject", ""))
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    message_id = original.get("Message-ID", "")

    msg = _build_message(config, to=to_addr, subject=subject, body=args.body, in_reply_to=message_id)
    _send_message(config, msg, to_addr)
    output_ok(f"Reply sent to {to_addr}", to=to_addr, subject=subject, from_addr=config["default_from"])


def cmd_forward(args: argparse.Namespace, config: dict) -> None:
    """Forward a message."""
    uid = str(args.uid).encode()
    with imap_connection(config, readonly=True) as conn:
        data = uid_fetch(conn, uid, "(RFC822)")
        if not data:
            raise NotFoundError(str(args.uid))
        original = email_lib.message_from_bytes(data[0][1])

    orig_from = decode_mime_header(original.get("From", ""))
    orig_date = original.get("Date", "")
    orig_subject = decode_mime_header(original.get("Subject", ""))
    plain, html_body = extract_body(original, config.get("max_body_chars", 10000))
    orig_body = plain if plain else html_to_text(html_body)

    subject = f"Fwd: {orig_subject}"
    body = getattr(args, "body", "") or ""
    body += f"\n\n---------- Forwarded message ----------\n"
    body += f"From: {orig_from}\nDate: {orig_date}\nSubject: {orig_subject}\n\n"
    body += orig_body[:config.get("max_body_chars", 10000)]

    msg = _build_message(config, to=args.to, subject=subject, body=body)
    _send_message(config, msg, args.to)
    output_ok(f"Forwarded to {args.to}", to=args.to, subject=subject, from_addr=config["default_from"])


def cmd_search(args: argparse.Namespace, config: dict) -> None:
    """Search emails."""
    query = args.query
    with imap_connection(config, readonly=True) as conn:
        # Try OR across subject, from, body
        criteria_list = [
            f'(OR (OR SUBJECT "{query}" FROM "{query}") BODY "{query}")',
            f'(OR SUBJECT "{query}" FROM "{query}")',
            f'SUBJECT "{query}"',
        ]

        uids = []  # type: List[bytes]
        for criteria in criteria_list:
            try:
                uids = uid_search(conn, criteria)
                if uids:
                    break
            except Exception:
                continue

        if not uids:
            output({"status": "ok", "messages": [], "count": 0, "query": query})
            return

        uids = uids[-(args.limit):]
        uids.reverse()

        messages = []
        for uid in uids:
            data = uid_fetch(conn, uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if not data:
                continue
            msg = email_lib.message_from_bytes(data[0][1])
            messages.append({
                "uid": uid.decode(),
                "from": decode_mime_header(msg.get("From", "")),
                "subject": decode_mime_header(msg.get("Subject", "")),
                "date": parse_date(msg.get("Date", "")),
            })

    output({"status": "ok", "messages": messages, "count": len(messages), "query": query})


def cmd_folders(args: argparse.Namespace, config: dict) -> None:
    """List mailbox folders."""
    # Use a raw connection since we don't need to select a folder
    address, password = get_credentials(config)
    provider = PROVIDERS.get(config["provider"], PROVIDERS["icloud"])
    ctx = ssl.create_default_context()
    conn = imaplib.IMAP4_SSL(
        provider["imap_host"], provider["imap_port"],
        ssl_context=ctx, timeout=config.get("connect_timeout", 30),
    )
    try:
        conn.login(address, password)
        _, folders = conn.list()
        result = []
        if folders:
            for f in folders:
                decoded = f.decode()
                match = re.search(r'"[/.]" (.+)$', decoded)
                name = match.group(1).strip('"') if match else decoded
                result.append(name)
    finally:
        try:
            conn.logout()
        except Exception:
            pass

    output({"status": "ok", "folders": result})


def cmd_mark(args: argparse.Namespace, config: dict) -> None:
    """Mark a message."""
    uid = str(args.uid).encode()
    with imap_connection(config) as conn:
        action = None
        if args.read:
            conn.uid("STORE", uid, "+FLAGS", "\\Seen")
            action = "marked_read"
        elif args.unread:
            conn.uid("STORE", uid, "-FLAGS", "\\Seen")
            action = "marked_unread"
        elif args.flag:
            conn.uid("STORE", uid, "+FLAGS", "\\Flagged")
            action = "flagged"
        elif args.unflag:
            conn.uid("STORE", uid, "-FLAGS", "\\Flagged")
            action = "unflagged"
        elif args.archive:
            for folder in ["Archive", "INBOX.Archive", "[Gmail]/All Mail"]:
                try:
                    conn.uid("COPY", uid, folder)
                    conn.uid("STORE", uid, "+FLAGS", "\\Deleted")
                    conn.expunge()
                    action = "archived"
                    break
                except Exception:
                    continue
            if not action:
                conn.uid("STORE", uid, "+FLAGS", "\\Seen")
                action = "marked_read_archive_failed"

    output_ok(f"Message {args.uid}: {action}", uid=args.uid, action=action)


def cmd_delete(args: argparse.Namespace, config: dict) -> None:
    """Delete a message."""
    uid = str(args.uid).encode()
    with imap_connection(config) as conn:
        for trash in ["Deleted Messages", "Trash", "[Gmail]/Trash", "INBOX.Trash"]:
            try:
                conn.uid("COPY", uid, trash)
                conn.uid("STORE", uid, "+FLAGS", "\\Deleted")
                conn.expunge()
                output_ok(f"Message {args.uid} moved to trash.", uid=args.uid)
                return
            except Exception:
                continue

        # Fallback: just mark deleted
        conn.uid("STORE", uid, "+FLAGS", "\\Deleted")
        conn.expunge()

    output_ok(f"Message {args.uid} deleted.", uid=args.uid)


def cmd_triage(args: argparse.Namespace, config: dict) -> None:
    """AI triage: classify and prioritize unread messages."""
    with imap_connection(config, readonly=True) as conn:
        uids = uid_search(conn, "(UNSEEN)")
        if not uids:
            output({
                "status": "ok",
                "triage": [],
                "summary": {"urgent": 0, "important": 0, "normal": 0, "low": 0},
                "total_unread": 0,
            })
            return

        uids = uids[-(args.limit):]
        triaged = []

        for uid in uids:
            data = uid_fetch(
                conn, uid,
                "(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)] BODY.PEEK[TEXT]<0.500>)"
            )
            if not data:
                continue

            raw_header = data[0][1]
            msg = email_lib.message_from_bytes(raw_header)
            from_addr = decode_mime_header(msg.get("From", ""))
            subject = decode_mime_header(msg.get("Subject", "(no subject)"))
            date = parse_date(msg.get("Date", ""))

            body_preview = ""
            if len(data) > 1 and data[1] and len(data[1]) > 1:
                try:
                    raw_body = data[1][1]
                    if isinstance(raw_body, bytes):
                        body_preview = raw_body.decode("utf-8", errors="replace")[:500]
                    else:
                        body_preview = str(raw_body)[:500]
                except Exception:
                    pass

            classification = classify_priority(from_addr, subject, body_preview, config)
            triaged.append({
                "uid": uid.decode(),
                "from": from_addr,
                "subject": subject,
                "date": date,
                **classification,
            })

    priority_order = {"urgent": 0, "important": 1, "normal": 2, "low": 3}
    triaged.sort(key=lambda x: priority_order.get(x["priority"], 2))

    summary = {"urgent": 0, "important": 0, "normal": 0, "low": 0}
    for t in triaged:
        summary[t["priority"]] = summary.get(t["priority"], 0) + 1

    # Integration: remember urgent/important emails in agent-memory
    for t in triaged:
        if t["priority"] in ("urgent", "important"):
            _memory_log_email(
                f"received ({t['priority']})",
                t["from"],
                t["subject"],
            )

    output({
        "status": "ok",
        "triage": triaged,
        "summary": summary,
        "total_unread": len(triaged),
    })


def cmd_thread(args: argparse.Namespace, config: dict) -> None:
    """Get full conversation thread for a message."""
    uid = str(args.uid).encode()
    with imap_connection(config, readonly=True) as conn:
        data = uid_fetch(conn, uid, "(RFC822)")
        if not data:
            raise NotFoundError(str(args.uid))

        target = email_lib.message_from_bytes(data[0][1])
        subject = decode_mime_header(target.get("Subject", ""))
        base_subject = re.sub(r'^(Re|Fwd|Fw):\s*', '', subject, flags=re.I).strip()

        # Also collect References/In-Reply-To for better threading
        references = target.get("References", "")
        in_reply_to = target.get("In-Reply-To", "")
        message_id = target.get("Message-ID", "")

        # Search by subject
        thread_uids = uid_search(conn, f'SUBJECT "{base_subject}"')

        # Also search by message-id references for accuracy
        for ref_id in [in_reply_to, message_id]:
            if ref_id:
                clean_id = ref_id.strip().strip("<>")
                try:
                    extra = uid_search(conn, f'HEADER Message-ID "{clean_id}"')
                    extra += uid_search(conn, f'HEADER In-Reply-To "{clean_id}"')
                    extra += uid_search(conn, f'HEADER References "{clean_id}"')
                    thread_uids = list(set(thread_uids + extra))
                except Exception:
                    pass

        thread_msgs = []
        for tid in thread_uids:
            td = uid_fetch(conn, tid, "(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE MESSAGE-ID)])")
            if not td:
                continue
            tmsg = email_lib.message_from_bytes(td[0][1])
            thread_msgs.append({
                "uid": tid.decode(),
                "from": decode_mime_header(tmsg.get("From", "")),
                "subject": decode_mime_header(tmsg.get("Subject", "")),
                "date": parse_date(tmsg.get("Date", "")),
                "message_id": tmsg.get("Message-ID", ""),
            })

    thread_msgs.sort(key=lambda x: x.get("date") or "")
    output({
        "status": "ok",
        "thread_subject": base_subject,
        "messages": thread_msgs,
        "count": len(thread_msgs),
    })


def cmd_batch_mark(args: argparse.Namespace, config: dict) -> None:
    """Mark multiple messages at once."""
    with imap_connection(config) as conn:
        uids = [u.strip() for u in args.uids.split(",")]
        results = []
        for uid_str in uids:
            uid = uid_str.encode()
            try:
                if args.read:
                    conn.uid("STORE", uid, "+FLAGS", "\\Seen")
                    results.append({"uid": uid_str, "action": "marked_read"})
                elif args.unread:
                    conn.uid("STORE", uid, "-FLAGS", "\\Seen")
                    results.append({"uid": uid_str, "action": "marked_unread"})
            except Exception as e:
                results.append({"uid": uid_str, "action": "error", "error": str(e)})

    output({"status": "ok", "results": results, "count": len(results)})


def cmd_digest(args: argparse.Namespace, config: dict) -> None:
    """Generate activity digest for the last N hours."""
    with imap_connection(config, readonly=True) as conn:
        since = datetime.now(timezone.utc) - timedelta(hours=args.hours)
        since_str = since.strftime("%d-%b-%Y")
        uids = uid_search(conn, f"(SINCE {since_str})")

        if not uids:
            output({
                "status": "ok",
                "period_hours": args.hours,
                "total": 0,
                "unread": 0,
                "top_senders": [],
                "recent_subjects": [],
            })
            return

        senders = {}  # type: Dict[str, int]
        subjects = []  # type: List[str]
        unread = 0

        for uid in uids[-50:]:
            data = uid_fetch(conn, uid, "(FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if not data:
                continue
            flags = data[0][0].decode() if data[0][0] else ""
            msg = email_lib.message_from_bytes(data[0][1])

            if "\\Seen" not in flags:
                unread += 1

            from_addr = decode_mime_header(msg.get("From", ""))
            sender_email = extract_email_address(from_addr)
            senders[sender_email] = senders.get(sender_email, 0) + 1
            subjects.append(decode_mime_header(msg.get("Subject", "")))

    top_senders = sorted(senders.items(), key=lambda x: -x[1])[:10]
    output({
        "status": "ok",
        "period_hours": args.hours,
        "total": len(uids),
        "unread": unread,
        "top_senders": [{"email": s[0], "count": s[1]} for s in top_senders],
        "recent_subjects": subjects[-10:],
    })


def cmd_config(args: argparse.Namespace, config: dict) -> None:
    """Show or set configuration."""
    if args.show:
        output({"status": "ok", "config": config})
    elif args.set:
        key, _, value = args.set.partition("=")
        if not key or not value:
            raise EmailError("Format: --set KEY=VALUE", "INVALID_ARG")

        if key in ("max_body_chars", "connect_timeout", "operation_timeout", "max_retries"):
            value = int(value)
        elif key in ("triage_keywords_urgent", "triage_keywords_important", "triage_keywords_low", "retry_backoff"):
            value = [v.strip() for v in value.split(",")]

        config[key] = value
        save_config(config)
        output_ok(f"Config updated: {key}={value}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Email Manager — Autonomous AI Email Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging to stderr")
    sub = parser.add_subparsers(dest="command")

    # count
    sub.add_parser("count", help="Inbox statistics")

    # inbox
    p = sub.add_parser("inbox", help="List inbox messages")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--unread", action="store_true")

    # read
    p = sub.add_parser("read", help="Read a message")
    p.add_argument("uid", type=int)

    # send
    p = sub.add_parser("send", help="Send email")
    p.add_argument("--to", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--html", action="store_true")
    p.add_argument("--attach", nargs="*")

    # reply
    p = sub.add_parser("reply", help="Reply to a message")
    p.add_argument("uid", type=int)
    p.add_argument("--body", required=True)

    # forward
    p = sub.add_parser("forward", help="Forward a message")
    p.add_argument("uid", type=int)
    p.add_argument("--to", required=True)
    p.add_argument("--body", default="")

    # search
    p = sub.add_parser("search", help="Search emails")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)

    # folders
    sub.add_parser("folders", help="List folders")

    # mark
    p = sub.add_parser("mark", help="Mark a message")
    p.add_argument("uid", type=int)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--read", action="store_true")
    g.add_argument("--unread", action="store_true")
    g.add_argument("--flag", action="store_true")
    g.add_argument("--unflag", action="store_true")
    g.add_argument("--archive", action="store_true")

    # delete
    p = sub.add_parser("delete", help="Delete a message")
    p.add_argument("uid", type=int)

    # triage
    p = sub.add_parser("triage", help="AI triage: prioritize unread")
    p.add_argument("--limit", type=int, default=50)

    # thread
    p = sub.add_parser("thread", help="Get conversation thread")
    p.add_argument("uid", type=int)

    # batch-mark
    p = sub.add_parser("batch-mark", help="Mark multiple messages")
    p.add_argument("--uids", required=True, help="Comma-separated UIDs")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--read", action="store_true")
    g.add_argument("--unread", action="store_true")

    # digest
    p = sub.add_parser("digest", help="Activity digest")
    p.add_argument("--hours", type=int, default=24)

    # config
    p = sub.add_parser("config", help="Show/set configuration")
    p.add_argument("--show", action="store_true")
    p.add_argument("--set", help="KEY=VALUE")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s: %(message)s", stream=sys.stderr)
    else:
        logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = get_config()

    commands = {
        "count": cmd_count,
        "inbox": cmd_inbox,
        "read": cmd_read,
        "send": cmd_send,
        "reply": cmd_reply,
        "forward": cmd_forward,
        "search": cmd_search,
        "folders": cmd_folders,
        "mark": cmd_mark,
        "delete": cmd_delete,
        "triage": cmd_triage,
        "thread": cmd_thread,
        "batch-mark": cmd_batch_mark,
        "digest": cmd_digest,
        "config": cmd_config,
    }

    try:
        commands[args.command](args, config)
    except EmailError as e:
        output_error(e.args[0], code=e.code)
    except imaplib.IMAP4.error as e:
        output_error(f"IMAP error: {e}", code="IMAP_ERROR")
    except smtplib.SMTPException as e:
        output_error(f"SMTP error: {e}", code="SMTP_ERROR")
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
