#!/usr/bin/env python3
"""Mailcow API client for managing domains, mailboxes, aliases, and DKIM.

Usage:
    python mailcow.py status
    python mailcow.py domain list
    python mailcow.py domain add <domain> [--max-mailboxes 10] [--quota 10240]
    python mailcow.py domain delete <domain>
    python mailcow.py mailbox list [--domain <domain>]
    python mailcow.py mailbox add <email> <password> [--name "Full Name"] [--quota 1024]
    python mailcow.py mailbox delete <email>
    python mailcow.py mailbox update <email> [--quota 2048] [--active 1]
    python mailcow.py alias list [--domain <domain>]
    python mailcow.py alias add <address> <goto>
    python mailcow.py alias delete <id>
    python mailcow.py dkim list
    python mailcow.py dkim add <domain> [--length 2048]
    python mailcow.py dkim get <domain>
    python mailcow.py queue list
    python mailcow.py queue flush
    python mailcow.py logs <type> [--count 50]

Requires env vars:
    MAILCOW_HOST     — e.g. mail.torrstatics.com
    MAILCOW_API_KEY  — from Mailcow admin panel

Python 3.9+ stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
from typing import Any, Dict, List, Optional
from urllib import error, request


class MailcowError(Exception):
    pass


def _get_config():
    host = os.environ.get("MAILCOW_HOST", "").rstrip("/")
    key = os.environ.get("MAILCOW_API_KEY", "")
    if not host or not key:
        raise MailcowError("MAILCOW_HOST and MAILCOW_API_KEY must be set")
    if not host.startswith("http"):
        host = "https://" + host
    return host, key


def _api(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
) -> Any:
    host, key = _get_config()
    url = "%s/api/v1/%s" % (host, endpoint.lstrip("/"))
    headers = {
        "X-API-Key": key,
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = request.Request(url, data=body, headers=headers, method=method)

    # Create SSL context (allow self-signed for initial setup)
    ctx = ssl.create_default_context()

    try:
        with request.urlopen(req, timeout=30, context=ctx) as resp:
            raw = resp.read().decode()
            if raw:
                return json.loads(raw)
            return {"success": True}
    except error.HTTPError as e:
        err_body = e.read().decode() if e.fp else ""
        raise MailcowError("HTTP %d: %s\n%s" % (e.code, e.reason, err_body))
    except error.URLError as e:
        raise MailcowError("Connection error: %s" % e.reason)


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def cmd_status() -> Dict[str, Any]:
    result = _api("get/status/containers")
    return result


# ---------------------------------------------------------------------------
# Domains
# ---------------------------------------------------------------------------

def domain_list() -> List[Dict[str, Any]]:
    return _api("get/domain/all")


def domain_add(
    domain: str,
    max_mailboxes: int = 10,
    max_aliases: int = 50,
    quota: int = 10240,  # MB
    active: int = 1,
) -> Any:
    return _api("add/domain", method="POST", data={
        "domain": domain,
        "description": domain,
        "aliases": str(max_aliases),
        "mailboxes": str(max_mailboxes),
        "defquota": "1024",
        "maxquota": str(quota),
        "quota": str(quota),
        "active": str(active),
        "rl_value": "",
        "rl_frame": "",
        "backupmx": "0",
        "relay_all_recipients": "0",
        "restart_sogo": "1",
    })


def domain_delete(domain: str) -> Any:
    return _api("delete/domain", method="POST", data=[domain])


# ---------------------------------------------------------------------------
# Mailboxes
# ---------------------------------------------------------------------------

def mailbox_list(domain: Optional[str] = None) -> List[Dict[str, Any]]:
    result = _api("get/mailbox/all")
    if domain and isinstance(result, list):
        result = [m for m in result if m.get("domain") == domain]
    return result


def mailbox_add(
    email: str,
    password: str,
    name: str = "",
    quota: int = 1024,  # MB
    active: int = 1,
) -> Any:
    local, domain = email.split("@", 1)
    return _api("add/mailbox", method="POST", data={
        "local_part": local,
        "domain": domain,
        "name": name or local,
        "password": password,
        "password2": password,
        "quota": str(quota),
        "active": str(active),
        "force_pw_update": "0",
        "tls_enforce_in": "1",
        "tls_enforce_out": "1",
    })


def mailbox_update(
    email: str,
    quota: Optional[int] = None,
    active: Optional[int] = None,
    name: Optional[str] = None,
) -> Any:
    data = {"items": [email], "attr": {}}
    if quota is not None:
        data["attr"]["quota"] = str(quota)
    if active is not None:
        data["attr"]["active"] = str(active)
    if name is not None:
        data["attr"]["name"] = name
    return _api("edit/mailbox", method="POST", data=data)


def mailbox_delete(email: str) -> Any:
    return _api("delete/mailbox", method="POST", data=[email])


# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------

def alias_list(domain: Optional[str] = None) -> List[Dict[str, Any]]:
    result = _api("get/alias/all")
    if domain and isinstance(result, list):
        result = [a for a in result if a.get("domain") == domain]
    return result


def alias_add(address: str, goto: str, active: int = 1) -> Any:
    return _api("add/alias", method="POST", data={
        "address": address,
        "goto": goto,
        "active": str(active),
    })


def alias_delete(alias_id: str) -> Any:
    return _api("delete/alias", method="POST", data=[alias_id])


# ---------------------------------------------------------------------------
# DKIM
# ---------------------------------------------------------------------------

def dkim_list() -> Any:
    return _api("get/dkim/all")


def dkim_add(domain: str, length: int = 2048) -> Any:
    return _api("add/dkim", method="POST", data={
        "domains": domain,
        "dkim_selector": "dkim",
        "key_size": str(length),
    })


def dkim_get(domain: str) -> Any:
    return _api("get/dkim/%s" % domain)


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------

def queue_list() -> Any:
    return _api("get/mailq/all")


def queue_flush() -> Any:
    return _api("delete/mailq", method="POST", data={"action": "super_delete", "items": ["all"]})


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------

def get_logs(log_type: str, count: int = 50) -> Any:
    return _api("get/logs/%s/%d" % (log_type, count))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def output(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(description="Mailcow Manager")
    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="Container status")

    # domain
    p_domain = sub.add_parser("domain", help="Domain management")
    dsub = p_domain.add_subparsers(dest="action")
    dsub.add_parser("list", help="List domains")
    da = dsub.add_parser("add", help="Add domain")
    da.add_argument("domain")
    da.add_argument("--max-mailboxes", type=int, default=10)
    da.add_argument("--max-aliases", type=int, default=50)
    da.add_argument("--quota", type=int, default=10240)
    dd = dsub.add_parser("delete", help="Delete domain")
    dd.add_argument("domain")

    # mailbox
    p_mb = sub.add_parser("mailbox", help="Mailbox management")
    msub = p_mb.add_subparsers(dest="action")
    ml = msub.add_parser("list", help="List mailboxes")
    ml.add_argument("--domain", default=None)
    ma = msub.add_parser("add", help="Add mailbox")
    ma.add_argument("email")
    ma.add_argument("password")
    ma.add_argument("--name", default="")
    ma.add_argument("--quota", type=int, default=1024)
    md = msub.add_parser("delete", help="Delete mailbox")
    md.add_argument("email")
    mu = msub.add_parser("update", help="Update mailbox")
    mu.add_argument("email")
    mu.add_argument("--quota", type=int, default=None)
    mu.add_argument("--active", type=int, default=None)
    mu.add_argument("--name", default=None)

    # alias
    p_al = sub.add_parser("alias", help="Alias management")
    asub = p_al.add_subparsers(dest="action")
    al = asub.add_parser("list", help="List aliases")
    al.add_argument("--domain", default=None)
    aa = asub.add_parser("add", help="Add alias")
    aa.add_argument("address")
    aa.add_argument("goto")
    ad = asub.add_parser("delete", help="Delete alias")
    ad.add_argument("id")

    # dkim
    p_dk = sub.add_parser("dkim", help="DKIM management")
    dksub = p_dk.add_subparsers(dest="action")
    dksub.add_parser("list", help="List DKIM keys")
    dka = dksub.add_parser("add", help="Generate DKIM key")
    dka.add_argument("domain")
    dka.add_argument("--length", type=int, default=2048)
    dkg = dksub.add_parser("get", help="Get DKIM record")
    dkg.add_argument("domain")

    # queue
    p_q = sub.add_parser("queue", help="Mail queue")
    qsub = p_q.add_subparsers(dest="action")
    qsub.add_parser("list", help="List queue")
    qsub.add_parser("flush", help="Flush queue")

    # logs
    p_log = sub.add_parser("logs", help="View logs")
    p_log.add_argument("type", choices=["dovecot", "postfix", "sogo", "rspamd", "watchdog", "acme"])
    p_log.add_argument("--count", type=int, default=50)

    args = parser.parse_args()

    try:
        if args.command == "status":
            output(cmd_status())

        elif args.command == "domain":
            if args.action == "list":
                domains = domain_list()
                if isinstance(domains, list):
                    for d in domains:
                        print("%-30s mboxes: %s/%s  active: %s" % (
                            d.get("domain_name", "?"),
                            d.get("mboxes_in_domain", 0),
                            d.get("max_num_mboxes_for_domain", "?"),
                            d.get("active", "?"),
                        ))
                else:
                    output(domains)
            elif args.action == "add":
                output(domain_add(args.domain, args.max_mailboxes, args.max_aliases, args.quota))
            elif args.action == "delete":
                output(domain_delete(args.domain))
            else:
                p_domain.print_help()

        elif args.command == "mailbox":
            if args.action == "list":
                mboxes = mailbox_list(args.domain)
                if isinstance(mboxes, list):
                    for m in mboxes:
                        print("%-35s %-20s quota: %sMB  active: %s" % (
                            m.get("username", "?"),
                            m.get("name", ""),
                            m.get("quota", 0) // 1048576,
                            m.get("active", "?"),
                        ))
                else:
                    output(mboxes)
            elif args.action == "add":
                output(mailbox_add(args.email, args.password, args.name, args.quota))
            elif args.action == "delete":
                output(mailbox_delete(args.email))
            elif args.action == "update":
                output(mailbox_update(args.email, args.quota, args.active, args.name))
            else:
                p_mb.print_help()

        elif args.command == "alias":
            if args.action == "list":
                aliases = alias_list(args.domain)
                if isinstance(aliases, list):
                    for a in aliases:
                        print("%-35s → %-35s  id: %s" % (
                            a.get("address", "?"),
                            a.get("goto", "?"),
                            a.get("id", "?"),
                        ))
                else:
                    output(aliases)
            elif args.action == "add":
                output(alias_add(args.address, args.goto))
            elif args.action == "delete":
                output(alias_delete(args.id))
            else:
                p_al.print_help()

        elif args.command == "dkim":
            if args.action == "list":
                output(dkim_list())
            elif args.action == "add":
                output(dkim_add(args.domain, args.length))
            elif args.action == "get":
                result = dkim_get(args.domain)
                if isinstance(result, dict) and result.get("dkim_txt"):
                    print("DKIM TXT record for %s:" % args.domain)
                    print("  Name: dkim._domainkey.%s" % args.domain)
                    print("  Value: %s" % result["dkim_txt"])
                else:
                    output(result)
            else:
                p_dk.print_help()

        elif args.command == "queue":
            if args.action == "list":
                output(queue_list())
            elif args.action == "flush":
                output(queue_flush())
            else:
                p_q.print_help()

        elif args.command == "logs":
            logs = get_logs(args.type, args.count)
            if isinstance(logs, list):
                for entry in logs:
                    if isinstance(entry, dict):
                        print("%s %s" % (entry.get("time", ""), entry.get("message", json.dumps(entry))))
                    else:
                        print(entry)
            else:
                output(logs)

        else:
            parser.print_help()

    except MailcowError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
