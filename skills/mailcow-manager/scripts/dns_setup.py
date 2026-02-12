#!/usr/bin/env python3
"""Cloudflare DNS record manager for mail server setup.

Configures all required DNS records for a Mailcow mail server:
  - MX record
  - A record for mail hostname
  - SPF (TXT)
  - DKIM (TXT)
  - DMARC (TXT)
  - Autodiscover/Autoconfig (CNAME)
  - rDNS note (must be set in Hetzner panel)

Usage:
    python dns_setup.py setup <domain> <mail_ip> [--mail-host mail.domain.com]
    python dns_setup.py verify <domain>
    python dns_setup.py add-dkim <domain> <dkim_value>
    python dns_setup.py list <domain>

Requires: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID env vars.
Python 3.9+ stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional
from urllib import error, request

API_BASE = "https://api.cloudflare.com/client/v4"


class DNSError(Exception):
    pass


def _get_credentials():
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not token:
        raise DNSError("CLOUDFLARE_API_TOKEN must be set")
    return token


def _api(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
) -> Any:
    token = _get_credentials()
    url = "%s/%s" % (API_BASE, endpoint.lstrip("/"))
    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except error.HTTPError as e:
        err_body = e.read().decode() if e.fp else ""
        raise DNSError("HTTP %d: %s\n%s" % (e.code, e.reason, err_body))
    except error.URLError as e:
        raise DNSError("Connection error: %s" % e.reason)


def get_zone_id(domain: str) -> str:
    """Find the Cloudflare zone ID for a domain."""
    result = _api("zones?name=%s" % domain)
    zones = result.get("result", [])
    if not zones:
        raise DNSError("Zone not found for %s. Is it added to Cloudflare?" % domain)
    return zones[0]["id"]


def list_records(zone_id: str) -> List[Dict[str, Any]]:
    result = _api("zones/%s/dns_records?per_page=100" % zone_id)
    return result.get("result", [])


def add_record(
    zone_id: str,
    record_type: str,
    name: str,
    content: str,
    ttl: int = 3600,
    priority: Optional[int] = None,
    proxied: bool = False,
) -> Dict[str, Any]:
    data = {
        "type": record_type,
        "name": name,
        "content": content,
        "ttl": ttl,
        "proxied": proxied,
    }
    if priority is not None:
        data["priority"] = priority
    result = _api("zones/%s/dns_records" % zone_id, method="POST", data=data)
    if not result.get("success"):
        raise DNSError("Failed to add %s record: %s" % (record_type, json.dumps(result.get("errors", []))))
    return result.get("result", {})


def setup_mail_dns(domain: str, mail_ip: str, mail_host: Optional[str] = None) -> List[str]:
    """Set up all DNS records needed for Mailcow."""
    if not mail_host:
        mail_host = "mail.%s" % domain

    zone_id = get_zone_id(domain)
    existing = list_records(zone_id)
    existing_set = set()
    for r in existing:
        existing_set.add((r["type"], r["name"], r.get("content", "")))

    created = []

    records = [
        # A record for mail hostname
        ("A", mail_host, mail_ip, None, False),
        # MX record
        ("MX", domain, mail_host, 10, False),
        # SPF
        ("TXT", domain, "v=spf1 a mx ip4:%s -all" % mail_ip, None, False),
        # DMARC
        ("TXT", "_dmarc.%s" % domain, "v=DMARC1; p=quarantine; rua=mailto:postmaster@%s; fo=1" % domain, None, False),
        # Autodiscover for Outlook
        ("CNAME", "autodiscover.%s" % domain, mail_host, None, False),
        # Autoconfig for Thunderbird
        ("CNAME", "autoconfig.%s" % domain, mail_host, None, False),
    ]

    for rtype, name, content, priority, proxied in records:
        # Skip if already exists with same type and name
        name_full = name if "." in name else "%s.%s" % (name, domain)
        found = False
        for r in existing:
            if r["type"] == rtype and r["name"] == name_full:
                found = True
                break
        if found:
            created.append("SKIP  %-6s %-40s (already exists)" % (rtype, name))
            continue

        try:
            add_record(zone_id, rtype, name, content, priority=priority, proxied=proxied)
            created.append("ADD   %-6s %-40s → %s" % (rtype, name, content[:60]))
        except DNSError as e:
            created.append("FAIL  %-6s %-40s: %s" % (rtype, name, str(e)[:80]))

    return created


def add_dkim_record(domain: str, dkim_value: str) -> str:
    """Add DKIM TXT record."""
    zone_id = get_zone_id(domain)
    name = "dkim._domainkey.%s" % domain
    try:
        add_record(zone_id, "TXT", name, dkim_value)
        return "ADD   TXT    %s" % name
    except DNSError as e:
        return "FAIL  TXT    %s: %s" % (name, str(e))


def verify_mail_dns(domain: str) -> List[str]:
    """Verify all required mail DNS records exist."""
    import socket

    checks = []
    mail_host = "mail.%s" % domain

    # Check A record
    try:
        ip = socket.gethostbyname(mail_host)
        checks.append("PASS  A      %-40s → %s" % (mail_host, ip))
    except socket.gaierror:
        checks.append("FAIL  A      %-40s (not found)" % mail_host)

    # Check MX
    try:
        # Use dig-style via DNS over TXT lookup in CF API
        zone_id = get_zone_id(domain)
        records = list_records(zone_id)
        mx_found = any(r["type"] == "MX" for r in records)
        spf_found = any(r["type"] == "TXT" and "v=spf1" in r.get("content", "") for r in records)
        dmarc_found = any(r["type"] == "TXT" and r["name"].startswith("_dmarc") for r in records)
        dkim_found = any(r["type"] == "TXT" and "_domainkey" in r["name"] for r in records)

        checks.append("%s  MX     %s" % ("PASS" if mx_found else "FAIL", domain))
        checks.append("%s  SPF    %s" % ("PASS" if spf_found else "FAIL", domain))
        checks.append("%s  DMARC  _dmarc.%s" % ("PASS" if dmarc_found else "FAIL", domain))
        checks.append("%s  DKIM   dkim._domainkey.%s" % ("PASS" if dkim_found else "MISS", domain))
    except DNSError as e:
        checks.append("FAIL  Zone lookup: %s" % str(e))

    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Mail DNS Setup (Cloudflare)")
    sub = parser.add_subparsers(dest="command")

    p_setup = sub.add_parser("setup", help="Configure all mail DNS records")
    p_setup.add_argument("domain")
    p_setup.add_argument("mail_ip")
    p_setup.add_argument("--mail-host", default=None)

    p_verify = sub.add_parser("verify", help="Verify mail DNS records")
    p_verify.add_argument("domain")

    p_dkim = sub.add_parser("add-dkim", help="Add DKIM TXT record")
    p_dkim.add_argument("domain")
    p_dkim.add_argument("dkim_value")

    p_list = sub.add_parser("list", help="List all DNS records")
    p_list.add_argument("domain")

    args = parser.parse_args()

    try:
        if args.command == "setup":
            results = setup_mail_dns(args.domain, args.mail_ip, args.mail_host)
            for r in results:
                print(r)
            print("\n⚠  IMPORTANT: Set rDNS (PTR) for %s → mail.%s in Hetzner Cloud panel" % (
                args.mail_ip, args.domain))
            print("⚠  DKIM record will be added after Mailcow generates the key")

        elif args.command == "verify":
            results = verify_mail_dns(args.domain)
            for r in results:
                print(r)

        elif args.command == "add-dkim":
            print(add_dkim_record(args.domain, args.dkim_value))

        elif args.command == "list":
            zone_id = get_zone_id(args.domain)
            records = list_records(zone_id)
            for r in records:
                print("%-6s %-40s → %s" % (
                    r.get("type", "?"),
                    r.get("name", "?"),
                    r.get("content", "?")[:70],
                ))

        else:
            parser.print_help()

    except DNSError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
