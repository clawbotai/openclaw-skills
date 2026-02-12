#!/usr/bin/env python3
"""
Email Manager — Autonomous AI Email Client
============================================
Full IMAP/SMTP access optimized for AI agent consumption.

All commands output structured JSON for reliable parsing.
Credentials are pulled from macOS Keychain at runtime.

Supports: iCloud, Gmail, Outlook, any IMAP/SMTP provider.

Commands:
    count                           Inbox stats (total, unread, flagged)
    inbox [--limit N] [--unread]    List messages with metadata
    read <uid>                      Full message content + attachments
    send --to X --subject X --body X  Send email
    reply <uid> --body X            Reply to a message
    forward <uid> --to X [--body X] Forward a message
    search <query> [--limit N]      Search by subject/body/from
    folders                         List all mailbox folders
    mark <uid> --read|--unread|--flag|--unflag|--archive
    delete <uid>                    Move to trash
    triage [--limit N]              AI triage: prioritize unread messages
    thread <uid>                    Get full conversation thread
    batch-mark --uids 1,2,3 --read Mark multiple messages at once
    digest [--hours N]              Summary of recent activity
    config --show|--set KEY=VAL     Show/set provider config

Provider presets: icloud, gmail, outlook, custom
"""

from __future__ import annotations

import argparse
import email as email_lib
import email.mime.multipart
import email.mime.text
import email.mime.application
import email.utils
import hashlib
import html as html_lib
import imaplib
import json
import mimetypes
import os
import re
import smtplib
import ssl
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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

# Default config — can be overridden via config.json
DEFAULT_CONFIG = {
    "provider": "icloud",
    "keychain_service": "icloud-email",
    "keychain_account": "clawbotai@icloud.com",
    "default_from": "clawbotai@icloud.com",
    "signature": "",
    "max_body_chars": 10000,
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

def output(data: Any, pretty: bool = True) -> None:
    """Print structured JSON output for the agent."""
    print(json.dumps(data, indent=2 if pretty else None, default=str, ensure_ascii=False))


def output_error(message: str, code: str = "ERROR") -> None:
    """Print structured error."""
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
                output_error(
                    "Could not retrieve password from macOS Keychain. "
                    f"Run: security add-generic-password -a '{config['keychain_account']}' "
                    f"-s '{config['keychain_service']}' -w '<app-specific-password>'",
                    code="AUTH_KEYCHAIN",
                )
        except FileNotFoundError:
            output_error("'security' command not found — not macOS?", code="AUTH_PLATFORM")

    return address, password


# ---------------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------------

def connect_imap(config: dict) -> imaplib.IMAP4_SSL:
    """Connect and authenticate to IMAP."""
    address, password = get_credentials(config)
    provider = PROVIDERS.get(config["provider"], PROVIDERS["icloud"])
    ctx = ssl.create_default_context()
    try:
        conn = imaplib.IMAP4_SSL(
            provider["imap_host"], provider["imap_port"], ssl_context=ctx
        )
        conn.login(address, password)
        return conn
    except imaplib.IMAP4.error as e:
        err = str(e)
        if "AUTHENTICATIONFAILED" in err:
            output_error(
                "Authentication failed. iCloud requires an app-specific password. "
                "Go to https://appleid.apple.com → Sign-In and Security → "
                "App-Specific Passwords → Generate one → then update keychain: "
                f"security add-generic-password -a '{config['keychain_account']}' "
                f"-s '{config['keychain_service']}' -w '<new-app-password>' -U",
                code="AUTH_FAILED",
            )
        output_error(f"IMAP connection failed: {err}", code="IMAP_ERROR")


def connect_smtp(config: dict) -> smtplib.SMTP:
    """Connect and authenticate to SMTP."""
    address, password = get_credentials(config)
    provider = PROVIDERS.get(config["provider"], PROVIDERS["icloud"])
    try:
        server = smtplib.SMTP(provider["smtp_host"], provider["smtp_port"])
        server.ehlo()
        if provider.get("smtp_tls") == "starttls":
            server.starttls()
            server.ehlo()
        server.login(address, password)
        return server
    except Exception as e:
        output_error(f"SMTP connection failed: {e}", code="SMTP_ERROR")


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


def extract_body(msg: email_lib.message.Message) -> Tuple[str, str]:
    """Extract (plain_text, html_text) from a message."""
    plain = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            disp = str(part.get("Content-Disposition", ""))
            if "attachment" in disp:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if ct == "text/plain" and not plain:
                plain = text
            elif ct == "text/html" and not html_body:
                html_body = text
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if msg.get_content_type() == "text/html":
                html_body = text
            else:
                plain = text

    return plain, html_body


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


def parse_date(date_str: str) -> Optional[str]:
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
    # Might just be a bare address
    return from_header.strip().lower()


# ---------------------------------------------------------------------------
# Triage / Priority Engine
# ---------------------------------------------------------------------------

def classify_priority(
    from_addr: str,
    subject: str,
    body_preview: str,
    config: dict,
) -> Dict[str, Any]:
    """
    Classify email priority for autonomous triage.

    Returns:
        {
            "priority": "urgent" | "important" | "normal" | "low",
            "category": "personal" | "transactional" | "newsletter" | "notification" | "unknown",
            "signals": ["list of why"]
        }
    """
    text = f"{subject} {body_preview}".lower()
    from_lower = from_addr.lower()
    signals = []

    # Priority classification
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

    return {
        "priority": priority,
        "category": category,
        "signals": signals,
    }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_count(args, config):
    """Inbox statistics."""
    conn = connect_imap(config)
    conn.select("INBOX", readonly=True)

    _, all_data = conn.search(None, "ALL")
    total = len(all_data[0].split()) if all_data[0] else 0

    _, unseen_data = conn.search(None, "(UNSEEN)")
    unread = len(unseen_data[0].split()) if unseen_data[0] else 0

    _, flagged_data = conn.search(None, "(FLAGGED)")
    flagged = len(flagged_data[0].split()) if flagged_data[0] else 0

    conn.logout()
    output({
        "status": "ok",
        "inbox": {
            "total": total,
            "unread": unread,
            "flagged": flagged,
        }
    })


def cmd_inbox(args, config):
    """List inbox messages with metadata."""
    conn = connect_imap(config)
    conn.select("INBOX", readonly=True)

    criteria = "(UNSEEN)" if args.unread else "ALL"
    _, data = conn.search(None, criteria)

    if not data[0]:
        conn.logout()
        output({"status": "ok", "messages": [], "count": 0})
        return

    uids = data[0].split()
    uids = uids[-(args.limit):]
    uids.reverse()

    messages = []
    for uid in uids:
        _, msg_data = conn.fetch(uid, "(UID FLAGS BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE MESSAGE-ID)])")
        if not msg_data or not msg_data[0]:
            continue

        raw_header = msg_data[0][1]
        flags_raw = msg_data[0][0].decode() if msg_data[0][0] else ""
        msg = email_lib.message_from_bytes(raw_header)

        is_read = "\\Seen" in flags_raw
        is_flagged = "\\Flagged" in flags_raw
        from_addr = decode_mime_header(msg.get("From", ""))
        to_addr = decode_mime_header(msg.get("To", ""))
        subject = decode_mime_header(msg.get("Subject", "(no subject)"))
        date = parse_date(msg.get("Date", ""))
        message_id = msg.get("Message-ID", "")

        messages.append({
            "uid": uid.decode(),
            "from": from_addr,
            "to": to_addr,
            "subject": subject,
            "date": date,
            "message_id": message_id,
            "read": is_read,
            "flagged": is_flagged,
        })

    conn.logout()
    output({
        "status": "ok",
        "messages": messages,
        "count": len(messages),
    })


def cmd_read(args, config):
    """Read full message content."""
    conn = connect_imap(config)
    conn.select("INBOX")

    uid = str(args.uid).encode()
    _, msg_data = conn.fetch(uid, "(RFC822)")
    if not msg_data or not msg_data[0]:
        conn.logout()
        output_error(f"Message {args.uid} not found.", code="NOT_FOUND")

    raw = msg_data[0][1]
    msg = email_lib.message_from_bytes(raw)
    conn.logout()

    from_addr = decode_mime_header(msg.get("From", ""))
    to_addr = decode_mime_header(msg.get("To", ""))
    cc = decode_mime_header(msg.get("Cc", ""))
    subject = decode_mime_header(msg.get("Subject", ""))
    date = parse_date(msg.get("Date", ""))
    message_id = msg.get("Message-ID", "")
    in_reply_to = msg.get("In-Reply-To", "")

    plain, html_body = extract_body(msg)
    body = plain if plain else html_to_text(html_body)
    body = body[:config.get("max_body_chars", 10000)]

    attachments = get_attachments(msg)

    output({
        "status": "ok",
        "message": {
            "uid": args.uid,
            "from": from_addr,
            "to": to_addr,
            "cc": cc,
            "subject": subject,
            "date": date,
            "message_id": message_id,
            "in_reply_to": in_reply_to,
            "body": body,
            "body_format": "plain" if plain else "html_converted",
            "attachments": attachments,
            "has_attachments": len(attachments) > 0,
        }
    })


def cmd_send(args, config):
    """Send an email."""
    address = config["default_from"]

    msg = email_lib.mime.multipart.MIMEMultipart()
    msg["From"] = address
    msg["To"] = args.to
    msg["Subject"] = args.subject
    if hasattr(args, "reply_to_id") and args.reply_to_id:
        msg["In-Reply-To"] = args.reply_to_id
        msg["References"] = args.reply_to_id

    body = args.body
    if config.get("signature"):
        body += f"\n\n{config['signature']}"

    content_type = "html" if getattr(args, "html", False) else "plain"
    msg.attach(email_lib.mime.text.MIMEText(body, content_type))

    # Attachments
    if getattr(args, "attach", None):
        for filepath in args.attach:
            path = Path(filepath)
            if not path.exists():
                output_error(f"Attachment not found: {filepath}", code="FILE_NOT_FOUND")
            ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            with open(path, "rb") as f:
                attachment = email_lib.mime.application.MIMEApplication(f.read(), Name=path.name)
            attachment["Content-Disposition"] = f'attachment; filename="{path.name}"'
            msg.attach(attachment)

    server = connect_smtp(config)
    recipients = [addr.strip() for addr in args.to.split(",")]
    server.sendmail(address, recipients, msg.as_string())
    server.quit()

    output_ok(
        f"Email sent to {args.to}",
        to=args.to,
        subject=args.subject,
        from_addr=address,
    )


def cmd_reply(args, config):
    """Reply to a message."""
    conn = connect_imap(config)
    conn.select("INBOX", readonly=True)

    uid = str(args.uid).encode()
    _, msg_data = conn.fetch(uid, "(RFC822)")
    if not msg_data or not msg_data[0]:
        conn.logout()
        output_error(f"Message {args.uid} not found.", code="NOT_FOUND")

    raw = msg_data[0][1]
    original = email_lib.message_from_bytes(raw)
    conn.logout()

    reply_to = decode_mime_header(original.get("Reply-To") or original.get("From"))
    subject = decode_mime_header(original.get("Subject", ""))
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    message_id = original.get("Message-ID", "")

    # Build a fake args object for cmd_send
    class SendArgs:
        to = extract_email_address(reply_to) if "<" not in reply_to else reply_to
        html = False
        attach = None
        reply_to_id = message_id
    send_args = SendArgs()
    send_args.subject = subject
    send_args.body = args.body

    cmd_send(send_args, config)


def cmd_forward(args, config):
    """Forward a message."""
    conn = connect_imap(config)
    conn.select("INBOX", readonly=True)

    uid = str(args.uid).encode()
    _, msg_data = conn.fetch(uid, "(RFC822)")
    if not msg_data or not msg_data[0]:
        conn.logout()
        output_error(f"Message {args.uid} not found.", code="NOT_FOUND")

    raw = msg_data[0][1]
    original = email_lib.message_from_bytes(raw)
    conn.logout()

    orig_from = decode_mime_header(original.get("From", ""))
    orig_date = original.get("Date", "")
    orig_subject = decode_mime_header(original.get("Subject", ""))
    plain, html_body = extract_body(original)
    orig_body = plain if plain else html_to_text(html_body)

    subject = f"Fwd: {orig_subject}"
    body = getattr(args, "body", "") or ""
    body += f"\n\n---------- Forwarded message ----------\n"
    body += f"From: {orig_from}\nDate: {orig_date}\nSubject: {orig_subject}\n\n"
    body += orig_body[:config.get("max_body_chars", 10000)]

    class SendArgs:
        to = args.to
        html = False
        attach = None
        reply_to_id = None
    send_args = SendArgs()
    send_args.subject = subject
    send_args.body = body

    cmd_send(send_args, config)


def cmd_search(args, config):
    """Search emails."""
    conn = connect_imap(config)
    conn.select("INBOX", readonly=True)

    query = args.query
    # Try OR across subject, from, body
    criteria_list = [
        f'(OR (OR SUBJECT "{query}" FROM "{query}") BODY "{query}")',
        f'(OR SUBJECT "{query}" FROM "{query}")',
        f'SUBJECT "{query}"',
    ]

    uids = []
    for criteria in criteria_list:
        try:
            _, data = conn.search(None, criteria)
            if data[0]:
                uids = data[0].split()
                break
        except Exception:
            continue

    if not uids:
        conn.logout()
        output({"status": "ok", "messages": [], "count": 0, "query": query})
        return

    uids = uids[-(args.limit):]
    uids.reverse()

    messages = []
    for uid in uids:
        _, msg_data = conn.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        if not msg_data or not msg_data[0]:
            continue
        raw = msg_data[0][1]
        msg = email_lib.message_from_bytes(raw)
        messages.append({
            "uid": uid.decode(),
            "from": decode_mime_header(msg.get("From", "")),
            "subject": decode_mime_header(msg.get("Subject", "")),
            "date": parse_date(msg.get("Date", "")),
        })

    conn.logout()
    output({"status": "ok", "messages": messages, "count": len(messages), "query": query})


def cmd_folders(args, config):
    """List mailbox folders."""
    conn = connect_imap(config)
    _, folders = conn.list()
    result = []
    if folders:
        for f in folders:
            decoded = f.decode()
            match = re.search(r'"[/.]" (.+)$', decoded)
            name = match.group(1).strip('"') if match else decoded
            result.append(name)
    conn.logout()
    output({"status": "ok", "folders": result})


def cmd_mark(args, config):
    """Mark a message."""
    conn = connect_imap(config)
    conn.select("INBOX")
    uid = str(args.uid).encode()

    action = None
    if args.read:
        conn.store(uid, "+FLAGS", "\\Seen")
        action = "marked_read"
    elif args.unread:
        conn.store(uid, "-FLAGS", "\\Seen")
        action = "marked_unread"
    elif args.flag:
        conn.store(uid, "+FLAGS", "\\Flagged")
        action = "flagged"
    elif args.unflag:
        conn.store(uid, "-FLAGS", "\\Flagged")
        action = "unflagged"
    elif args.archive:
        # Move to Archive folder (iCloud uses "Archive")
        for folder in ["Archive", "INBOX.Archive", "[Gmail]/All Mail"]:
            try:
                conn.copy(uid, folder)
                conn.store(uid, "+FLAGS", "\\Deleted")
                conn.expunge()
                action = "archived"
                break
            except Exception:
                continue
        if not action:
            conn.store(uid, "+FLAGS", "\\Seen")
            action = "marked_read_archive_failed"

    conn.logout()
    output_ok(f"Message {args.uid}: {action}", uid=args.uid, action=action)


def cmd_delete(args, config):
    """Delete a message."""
    conn = connect_imap(config)
    conn.select("INBOX")
    uid = str(args.uid).encode()

    # Try moving to Trash first
    for trash in ["Deleted Messages", "Trash", "[Gmail]/Trash", "INBOX.Trash"]:
        try:
            conn.copy(uid, trash)
            conn.store(uid, "+FLAGS", "\\Deleted")
            conn.expunge()
            conn.logout()
            output_ok(f"Message {args.uid} moved to trash.", uid=args.uid)
            return
        except Exception:
            continue

    # Fallback: just mark deleted
    conn.store(uid, "+FLAGS", "\\Deleted")
    conn.expunge()
    conn.logout()
    output_ok(f"Message {args.uid} deleted.", uid=args.uid)


def cmd_triage(args, config):
    """
    AI triage: classify and prioritize unread messages.

    Returns messages sorted by priority with classification metadata.
    This is the primary command for autonomous inbox management.
    """
    conn = connect_imap(config)
    conn.select("INBOX", readonly=True)

    _, data = conn.search(None, "(UNSEEN)")
    if not data[0]:
        conn.logout()
        output({
            "status": "ok",
            "triage": [],
            "summary": {"urgent": 0, "important": 0, "normal": 0, "low": 0},
            "total_unread": 0,
        })
        return

    uids = data[0].split()
    uids = uids[-(args.limit):]

    triaged = []
    for uid in uids:
        _, msg_data = conn.fetch(
            uid,
            "(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)] BODY.PEEK[TEXT]<0.500>)"
        )
        if not msg_data or not msg_data[0]:
            continue

        # Parse header
        raw_header = msg_data[0][1]
        msg = email_lib.message_from_bytes(raw_header)
        from_addr = decode_mime_header(msg.get("From", ""))
        subject = decode_mime_header(msg.get("Subject", "(no subject)"))
        date = parse_date(msg.get("Date", ""))

        # Get body preview for classification
        body_preview = ""
        if len(msg_data) > 1 and msg_data[1] and len(msg_data[1]) > 1:
            try:
                body_preview = msg_data[1][1].decode("utf-8", errors="replace")[:500]
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

    conn.logout()

    # Sort by priority
    priority_order = {"urgent": 0, "important": 1, "normal": 2, "low": 3}
    triaged.sort(key=lambda x: priority_order.get(x["priority"], 2))

    summary = {"urgent": 0, "important": 0, "normal": 0, "low": 0}
    for t in triaged:
        summary[t["priority"]] = summary.get(t["priority"], 0) + 1

    output({
        "status": "ok",
        "triage": triaged,
        "summary": summary,
        "total_unread": len(triaged),
    })


def cmd_thread(args, config):
    """Get full conversation thread for a message."""
    conn = connect_imap(config)
    conn.select("INBOX", readonly=True)

    # First get the target message to find its subject and message-id
    uid = str(args.uid).encode()
    _, msg_data = conn.fetch(uid, "(RFC822)")
    if not msg_data or not msg_data[0]:
        conn.logout()
        output_error(f"Message {args.uid} not found.", code="NOT_FOUND")

    raw = msg_data[0][1]
    target = email_lib.message_from_bytes(raw)
    subject = decode_mime_header(target.get("Subject", ""))
    # Strip Re:/Fwd: prefixes to get base subject
    base_subject = re.sub(r'^(Re|Fwd|Fw):\s*', '', subject, flags=re.I).strip()

    # Search for all messages with this subject
    _, data = conn.search(None, f'SUBJECT "{base_subject}"')
    thread_msgs = []
    if data[0]:
        for tid in data[0].split():
            _, td = conn.fetch(tid, "(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE MESSAGE-ID)])")
            if not td or not td[0]:
                continue
            tmsg = email_lib.message_from_bytes(td[0][1])
            thread_msgs.append({
                "uid": tid.decode(),
                "from": decode_mime_header(tmsg.get("From", "")),
                "subject": decode_mime_header(tmsg.get("Subject", "")),
                "date": parse_date(tmsg.get("Date", "")),
                "message_id": tmsg.get("Message-ID", ""),
            })

    # Sort by date
    thread_msgs.sort(key=lambda x: x.get("date") or "")

    conn.logout()
    output({
        "status": "ok",
        "thread_subject": base_subject,
        "messages": thread_msgs,
        "count": len(thread_msgs),
    })


def cmd_batch_mark(args, config):
    """Mark multiple messages at once."""
    conn = connect_imap(config)
    conn.select("INBOX")

    uids = [u.strip() for u in args.uids.split(",")]
    results = []
    for uid in uids:
        try:
            if args.read:
                conn.store(uid.encode(), "+FLAGS", "\\Seen")
                results.append({"uid": uid, "action": "marked_read"})
            elif args.unread:
                conn.store(uid.encode(), "-FLAGS", "\\Seen")
                results.append({"uid": uid, "action": "marked_unread"})
        except Exception as e:
            results.append({"uid": uid, "action": "error", "error": str(e)})

    conn.logout()
    output({"status": "ok", "results": results, "count": len(results)})


def cmd_digest(args, config):
    """Generate activity digest for the last N hours."""
    conn = connect_imap(config)
    conn.select("INBOX", readonly=True)

    since = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    since_str = since.strftime("%d-%b-%Y")
    _, data = conn.search(None, f'(SINCE {since_str})')

    if not data[0]:
        conn.logout()
        output({
            "status": "ok",
            "period_hours": args.hours,
            "total": 0,
            "unread": 0,
            "senders": [],
            "subjects": [],
        })
        return

    uids = data[0].split()
    senders = {}
    subjects = []
    unread = 0

    for uid in uids[-50:]:  # Cap at 50 for performance
        _, msg_data = conn.fetch(
            uid,
            "(FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
        )
        if not msg_data or not msg_data[0]:
            continue
        flags = msg_data[0][0].decode() if msg_data[0][0] else ""
        raw = msg_data[0][1]
        msg = email_lib.message_from_bytes(raw)

        if "\\Seen" not in flags:
            unread += 1

        from_addr = decode_mime_header(msg.get("From", ""))
        sender_email = extract_email_address(from_addr)
        senders[sender_email] = senders.get(sender_email, 0) + 1

        subjects.append(decode_mime_header(msg.get("Subject", "")))

    conn.logout()

    # Sort senders by count
    top_senders = sorted(senders.items(), key=lambda x: -x[1])[:10]

    output({
        "status": "ok",
        "period_hours": args.hours,
        "total": len(uids),
        "unread": unread,
        "top_senders": [{"email": s[0], "count": s[1]} for s in top_senders],
        "recent_subjects": subjects[-10:],
    })


def cmd_config(args, config):
    """Show or set configuration."""
    if args.show:
        # Mask sensitive fields
        display = config.copy()
        output({"status": "ok", "config": display})
    elif args.set:
        key, _, value = args.set.partition("=")
        if not key or not value:
            output_error("Format: --set KEY=VALUE", code="INVALID_ARG")

        # Type coercion for known fields
        if key in ("max_body_chars",):
            value = int(value)
        elif key in ("triage_keywords_urgent", "triage_keywords_important", "triage_keywords_low"):
            value = [v.strip() for v in value.split(",")]

        config[key] = value
        save_config(config)
        output_ok(f"Config updated: {key}={value}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """CLI entry point: parse arguments and dispatch to the appropriate email command."""
    parser = argparse.ArgumentParser(
        description="Email Manager — Autonomous AI Email Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
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
    commands[args.command](args, config)


if __name__ == "__main__":
    main()
