#!/usr/bin/env python3
"""Cloudflare Pages project management.

Usage:
    python projects.py list
    python projects.py create <name> [--production-branch main]
    python projects.py delete <name>
    python projects.py info <name>
    python projects.py domains <name>
    python projects.py add-domain <name> <domain>

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


class ProjectError(Exception):
    pass


def _get_credentials():
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account:
        raise ProjectError(
            "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID must be set"
        )
    return token, account


def _api(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    token, account_id = _get_credentials()
    url = "%s/accounts/%s%s" % (API_BASE, account_id, endpoint)
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
        raise ProjectError("HTTP %d: %s\n%s" % (e.code, e.reason, err_body))
    except error.URLError as e:
        raise ProjectError("URL error: %s" % e.reason)


def list_projects() -> list:
    result = _api("/pages/projects")
    return result.get("result", [])


def create_project(name: str, production_branch: str = "main") -> Dict[str, Any]:
    data = {
        "name": name,
        "production_branch": production_branch,
    }
    result = _api("/pages/projects", method="POST", data=data)
    if not result.get("success"):
        raise ProjectError("Create failed: %s" % json.dumps(result.get("errors", [])))
    return result.get("result", {})


def get_project(name: str) -> Dict[str, Any]:
    result = _api("/pages/projects/%s" % name)
    return result.get("result", {})


def delete_project(name: str) -> bool:
    _api("/pages/projects/%s" % name, method="DELETE")
    return True


def list_domains(project_name: str) -> list:
    result = _api("/pages/projects/%s/domains" % project_name)
    return result.get("result", [])


def add_domain(project_name: str, domain: str) -> Dict[str, Any]:
    result = _api(
        "/pages/projects/%s/domains" % project_name,
        method="POST",
        data={"name": domain},
    )
    return result.get("result", {})


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Cloudflare Pages projects")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all projects")

    p_create = sub.add_parser("create", help="Create a project")
    p_create.add_argument("name", help="Project name")
    p_create.add_argument("--production-branch", default="main")

    p_info = sub.add_parser("info", help="Get project details")
    p_info.add_argument("name", help="Project name")

    p_del = sub.add_parser("delete", help="Delete a project")
    p_del.add_argument("name", help="Project name")

    p_domains = sub.add_parser("domains", help="List custom domains")
    p_domains.add_argument("name", help="Project name")

    p_add = sub.add_parser("add-domain", help="Add custom domain")
    p_add.add_argument("name", help="Project name")
    p_add.add_argument("domain", help="Domain to add")

    args = parser.parse_args()

    try:
        if args.command == "list":
            projects = list_projects()
            for p in projects:
                print("%-30s %s" % (p.get("name", "?"), p.get("subdomain", "")))
            if not projects:
                print("No projects found.")

        elif args.command == "create":
            proj = create_project(args.name, args.production_branch)
            print(json.dumps(proj, indent=2))

        elif args.command == "info":
            proj = get_project(args.name)
            print(json.dumps(proj, indent=2))

        elif args.command == "delete":
            delete_project(args.name)
            print("Deleted: %s" % args.name)

        elif args.command == "domains":
            domains = list_domains(args.name)
            for d in domains:
                print("%-40s %s" % (d.get("name", "?"), d.get("status", "")))
            if not domains:
                print("No custom domains.")

        elif args.command == "add-domain":
            result = add_domain(args.name, args.domain)
            print(json.dumps(result, indent=2))

        else:
            parser.print_help()

    except ProjectError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
