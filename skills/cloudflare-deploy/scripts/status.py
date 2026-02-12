#!/usr/bin/env python3
"""Cloudflare Pages deployment status, logs, and rollback.

Usage:
    python status.py list <project_name>
    python status.py info <project_name> <deployment_id>
    python status.py logs <project_name> <deployment_id>
    python status.py rollback <project_name> <deployment_id>

Requires: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID env vars.
Python 3.9+ stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional
from urllib import error, request

API_BASE = "https://api.cloudflare.com/client/v4"


class StatusError(Exception):
    pass


def _api(endpoint: str, method: str = "GET") -> Dict[str, Any]:
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account:
        raise StatusError(
            "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID must be set"
        )
    url = "%s/accounts/%s%s" % (API_BASE, account, endpoint)
    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-Type": "application/json",
    }
    req = request.Request(url, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise StatusError("HTTP %d: %s\n%s" % (e.code, e.reason, body))
    except error.URLError as e:
        raise StatusError("URL error: %s" % e.reason)


def list_deployments(project: str) -> list:
    result = _api("/pages/projects/%s/deployments" % project)
    return result.get("result", [])


def get_deployment(project: str, deploy_id: str) -> Dict[str, Any]:
    result = _api("/pages/projects/%s/deployments/%s" % (project, deploy_id))
    return result.get("result", {})


def get_logs(project: str, deploy_id: str) -> list:
    result = _api("/pages/projects/%s/deployments/%s/history/logs" % (project, deploy_id))
    return result.get("result", [])


def rollback(project: str, deploy_id: str) -> Dict[str, Any]:
    result = _api(
        "/pages/projects/%s/deployments/%s/rollback" % (project, deploy_id),
        method="POST",
    )
    if not result.get("success"):
        raise StatusError("Rollback failed: %s" % json.dumps(result.get("errors", [])))
    return result.get("result", {})


def main() -> None:
    parser = argparse.ArgumentParser(description="CF Pages deployment status & rollback")
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="List deployments")
    p_list.add_argument("project", help="Project name")

    p_info = sub.add_parser("info", help="Deployment details")
    p_info.add_argument("project", help="Project name")
    p_info.add_argument("deployment_id", help="Deployment ID")

    p_logs = sub.add_parser("logs", help="Deployment logs")
    p_logs.add_argument("project", help="Project name")
    p_logs.add_argument("deployment_id", help="Deployment ID")

    p_rb = sub.add_parser("rollback", help="Rollback deployment")
    p_rb.add_argument("project", help="Project name")
    p_rb.add_argument("deployment_id", help="Deployment ID")

    args = parser.parse_args()

    try:
        if args.command == "list":
            deps = list_deployments(args.project)
            for d in deps:
                status = d.get("latest_stage", {}).get("status", "?")
                print("%-36s %-10s %s" % (d.get("id", "?"), status, d.get("url", "")))
            if not deps:
                print("No deployments found.")

        elif args.command == "info":
            dep = get_deployment(args.project, args.deployment_id)
            print(json.dumps(dep, indent=2))

        elif args.command == "logs":
            logs = get_logs(args.project, args.deployment_id)
            for entry in logs:
                print(entry if isinstance(entry, str) else json.dumps(entry))

        elif args.command == "rollback":
            result = rollback(args.project, args.deployment_id)
            print("Rolled back: %s" % result.get("id", "done"))

        else:
            parser.print_help()

    except StatusError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
