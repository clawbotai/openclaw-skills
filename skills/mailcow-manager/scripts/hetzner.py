#!/usr/bin/env python3
"""Hetzner Cloud API client for provisioning and managing VPS instances.

Usage:
    python hetzner.py list
    python hetzner.py create <name> --type cx22 --image ubuntu-24.04 --location fsn1
    python hetzner.py info <server_id>
    python hetzner.py delete <server_id>
    python hetzner.py ssh-keys
    python hetzner.py types
    python hetzner.py images [--type system]

Requires: HETZNER_API_TOKEN env var.
Python 3.9+ stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional
from urllib import error, request

API_BASE = "https://api.hetzner.cloud/v1"


class HetznerError(Exception):
    pass


def _get_token() -> str:
    token = os.environ.get("HETZNER_API_TOKEN", "")
    if not token:
        raise HetznerError("HETZNER_API_TOKEN must be set")
    return token


def _api(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
) -> Any:
    token = _get_token()
    url = "%s/%s" % (API_BASE, endpoint.lstrip("/"))
    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {"success": True}
    except error.HTTPError as e:
        err_body = e.read().decode() if e.fp else ""
        raise HetznerError("HTTP %d: %s\n%s" % (e.code, e.reason, err_body))
    except error.URLError as e:
        raise HetznerError("Connection error: %s" % e.reason)


# ---------------------------------------------------------------------------
# Servers
# ---------------------------------------------------------------------------

def server_list() -> List[Dict[str, Any]]:
    result = _api("servers")
    return result.get("servers", [])


def server_create(
    name: str,
    server_type: str = "cx22",
    image: str = "ubuntu-24.04",
    location: str = "fsn1",
    ssh_keys: Optional[List[str]] = None,
    user_data: Optional[str] = None,
) -> Dict[str, Any]:
    data = {
        "name": name,
        "server_type": server_type,
        "image": image,
        "location": location,
        "start_after_create": True,
    }
    if ssh_keys:
        data["ssh_keys"] = ssh_keys
    if user_data:
        data["user_data"] = user_data
    return _api("servers", method="POST", data=data)


def server_info(server_id: str) -> Dict[str, Any]:
    result = _api("servers/%s" % server_id)
    return result.get("server", result)


def server_delete(server_id: str) -> Any:
    return _api("servers/%s" % server_id, method="DELETE")


def server_action(server_id: str, action: str) -> Any:
    return _api("servers/%s/actions/%s" % (server_id, action), method="POST")


# ---------------------------------------------------------------------------
# SSH Keys
# ---------------------------------------------------------------------------

def ssh_key_list() -> List[Dict[str, Any]]:
    result = _api("ssh_keys")
    return result.get("ssh_keys", [])


# ---------------------------------------------------------------------------
# Server Types & Images
# ---------------------------------------------------------------------------

def server_types() -> List[Dict[str, Any]]:
    result = _api("server_types")
    return result.get("server_types", [])


def images(image_type: str = "system") -> List[Dict[str, Any]]:
    result = _api("images?type=%s" % image_type)
    return result.get("images", [])


# ---------------------------------------------------------------------------
# Firewall
# ---------------------------------------------------------------------------

def create_mail_firewall(name: str = "mailcow-firewall") -> Dict[str, Any]:
    """Create a firewall with mail server rules."""
    rules = [
        {"direction": "in", "protocol": "tcp", "port": "22",
         "source_ips": ["0.0.0.0/0", "::/0"], "description": "SSH"},
        {"direction": "in", "protocol": "tcp", "port": "25",
         "source_ips": ["0.0.0.0/0", "::/0"], "description": "SMTP"},
        {"direction": "in", "protocol": "tcp", "port": "80",
         "source_ips": ["0.0.0.0/0", "::/0"], "description": "HTTP"},
        {"direction": "in", "protocol": "tcp", "port": "110",
         "source_ips": ["0.0.0.0/0", "::/0"], "description": "POP3"},
        {"direction": "in", "protocol": "tcp", "port": "143",
         "source_ips": ["0.0.0.0/0", "::/0"], "description": "IMAP"},
        {"direction": "in", "protocol": "tcp", "port": "443",
         "source_ips": ["0.0.0.0/0", "::/0"], "description": "HTTPS"},
        {"direction": "in", "protocol": "tcp", "port": "465",
         "source_ips": ["0.0.0.0/0", "::/0"], "description": "SMTPS"},
        {"direction": "in", "protocol": "tcp", "port": "587",
         "source_ips": ["0.0.0.0/0", "::/0"], "description": "Submission"},
        {"direction": "in", "protocol": "tcp", "port": "993",
         "source_ips": ["0.0.0.0/0", "::/0"], "description": "IMAPS"},
        {"direction": "in", "protocol": "tcp", "port": "995",
         "source_ips": ["0.0.0.0/0", "::/0"], "description": "POP3S"},
        {"direction": "in", "protocol": "tcp", "port": "4190",
         "source_ips": ["0.0.0.0/0", "::/0"], "description": "Sieve"},
    ]
    return _api("firewalls", method="POST", data={
        "name": name,
        "rules": rules,
    })


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def output(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(description="Hetzner Cloud Manager")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List servers")

    p_create = sub.add_parser("create", help="Create server")
    p_create.add_argument("name")
    p_create.add_argument("--type", default="cx22", dest="server_type")
    p_create.add_argument("--image", default="ubuntu-24.04")
    p_create.add_argument("--location", default="fsn1",
                          help="fsn1 (Falkenstein) | nbg1 (Nuremberg) | hel1 (Helsinki) | ash (Ashburn)")
    p_create.add_argument("--ssh-key", action="append", dest="ssh_keys", default=None)
    p_create.add_argument("--firewall", action="store_true", help="Create and attach mail firewall")

    p_info = sub.add_parser("info", help="Server details")
    p_info.add_argument("server_id")

    p_del = sub.add_parser("delete", help="Delete server")
    p_del.add_argument("server_id")

    sub.add_parser("ssh-keys", help="List SSH keys")
    sub.add_parser("types", help="List server types")

    p_img = sub.add_parser("images", help="List images")
    p_img.add_argument("--type", default="system", dest="image_type")

    p_fw = sub.add_parser("firewall", help="Create mail server firewall")
    p_fw.add_argument("--name", default="mailcow-firewall")

    args = parser.parse_args()

    try:
        if args.command == "list":
            servers = server_list()
            if not servers:
                print("No servers found.")
            for s in servers:
                ip = ""
                pub = s.get("public_net", {})
                if pub.get("ipv4"):
                    ip = pub["ipv4"].get("ip", "")
                print("%-6s %-20s %-15s %-10s %s" % (
                    s.get("id", "?"),
                    s.get("name", "?"),
                    ip,
                    s.get("status", "?"),
                    s.get("server_type", {}).get("name", "?"),
                ))

        elif args.command == "create":
            result = server_create(
                args.name,
                args.server_type,
                args.image,
                args.location,
                args.ssh_keys,
            )
            server = result.get("server", {})
            ip = server.get("public_net", {}).get("ipv4", {}).get("ip", "pending")
            root_pw = result.get("root_password", "")
            print("Server created:")
            print("  ID: %s" % server.get("id", "?"))
            print("  Name: %s" % server.get("name", "?"))
            print("  IP: %s" % ip)
            print("  Type: %s" % args.server_type)
            print("  Image: %s" % args.image)
            print("  Location: %s" % args.location)
            if root_pw:
                print("  Root password: %s" % root_pw)

            if args.firewall:
                fw = create_mail_firewall()
                fw_id = fw.get("firewall", {}).get("id")
                if fw_id:
                    _api("firewalls/%s/actions/apply_to_resources" % fw_id,
                         method="POST",
                         data={"apply_to": [{"type": "server", "server": {"id": server.get("id")}}]})
                    print("  Firewall: mailcow-firewall attached")

        elif args.command == "info":
            output(server_info(args.server_id))

        elif args.command == "delete":
            server_delete(args.server_id)
            print("Deleted server %s" % args.server_id)

        elif args.command == "ssh-keys":
            keys = ssh_key_list()
            for k in keys:
                print("%-6s %-20s %s..." % (
                    k.get("id", "?"),
                    k.get("name", "?"),
                    k.get("public_key", "")[:50],
                ))

        elif args.command == "types":
            types = server_types()
            for t in types:
                if t.get("deprecated"):
                    continue
                print("%-10s %d vCPU  %5dMB RAM  %4dGB disk  €%.2f/mo" % (
                    t.get("name", "?"),
                    t.get("cores", 0),
                    t.get("memory", 0) * 1024,
                    t.get("disk", 0),
                    t.get("prices", [{}])[0].get("price_monthly", {}).get("gross", 0),
                ))

        elif args.command == "images":
            imgs = images(args.image_type)
            for i in imgs:
                print("%-25s %s" % (i.get("name") or i.get("description", "?"), i.get("description", "")))

        elif args.command == "firewall":
            result = create_mail_firewall(args.name)
            output(result.get("firewall", result))

        else:
            parser.print_help()

    except HetznerError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
