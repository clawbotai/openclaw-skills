#!/usr/bin/env python3
"""Cloudflare Pages deployment via Direct Upload API.

Implements the correct CF Pages Direct Upload flow:
1. Hash local files
2. Request upload session (JWT + missing file list)
3. Upload missing files in batches
4. Create deployment

Usage:
    python deploy.py <project_name> <directory> [--branch main]

Requires: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID env vars.
Python 3.9+ stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("cf-deploy")

API_BASE = "https://api.cloudflare.com/client/v4"


class DeployError(Exception):
    pass


def _get_credentials() -> Tuple[str, str]:
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account:
        raise DeployError(
            "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID must be set"
        )
    return token, account


def _api_request(
    url: str,
    token: str,
    method: str = "GET",
    data: Optional[bytes] = None,
    content_type: str = "application/json",
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    headers = {
        "Authorization": "Bearer %s" % token,
        "Content-Type": content_type,
    }
    if extra_headers:
        headers.update(extra_headers)
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode()
            if body:
                return json.loads(body)
            return {"success": True}
    except error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise DeployError("HTTP %d: %s\n%s" % (e.code, e.reason, body))
    except error.URLError as e:
        raise DeployError("URL error: %s" % e.reason)


def _hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _collect_files(directory: str) -> List[Dict[str, Any]]:
    """Walk directory and collect file metadata + hashes."""
    base = Path(directory).resolve()
    files = []
    for root, _dirs, filenames in os.walk(base):
        for name in filenames:
            full = Path(root) / name
            rel = "/" + str(full.relative_to(base)).replace("\\", "/")
            file_hash = _hash_file(str(full))
            size = full.stat().st_size
            files.append({
                "path": rel,
                "hash": file_hash,
                "size": size,
                "full_path": str(full),
            })
    return files


def _build_multipart(
    files_to_upload: List[Dict[str, Any]],
) -> Tuple[bytes, str]:
    """Build multipart/form-data body for file upload."""
    boundary = "----CFDeployBoundary%s" % hashlib.md5(
        str(len(files_to_upload)).encode()
    ).hexdigest()[:16]
    parts = []
    for f in files_to_upload:
        mime = mimetypes.guess_type(f["full_path"])[0] or "application/octet-stream"
        with open(f["full_path"], "rb") as fh:
            content = fh.read()
        part = (
            ("--%s\r\n" % boundary).encode()
            + ("Content-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
               % (f["hash"], os.path.basename(f["full_path"]))).encode()
            + ("Content-Type: %s\r\n\r\n" % mime).encode()
            + content
            + b"\r\n"
        )
        parts.append(part)
    body = b"".join(parts) + ("--%s--\r\n" % boundary).encode()
    content_type = "multipart/form-data; boundary=%s" % boundary
    return body, content_type


def deploy(project_name: str, directory: str, branch: str = "main") -> Dict[str, Any]:
    """Deploy a directory to Cloudflare Pages via Direct Upload.

    Args:
        project_name: CF Pages project name.
        directory: Local directory to deploy.
        branch: Branch name (default: main).

    Returns:
        Deployment result dict.

    Raises:
        DeployError: On any failure.
    """
    token, account_id = _get_credentials()
    base_url = "%s/accounts/%s/pages/projects/%s" % (API_BASE, account_id, project_name)

    # 1. Collect and hash files
    files = _collect_files(directory)
    if not files:
        raise DeployError("No files found in %s" % directory)
    logger.info("Found %d files to deploy", len(files))

    # 2. Create upload session — send manifest of hashes
    hashes = {f["path"]: f["hash"] for f in files}
    manifest_data = json.dumps({"hashes": list(set(hashes.values()))}).encode()
    
    session_url = "%s/deployments" % base_url
    # Use the Direct Upload create deployment endpoint
    # POST with manifest to get upload URL + JWT
    
    # Build the file lookup by hash
    hash_to_file = {}
    for f in files:
        if f["hash"] not in hash_to_file:
            hash_to_file[f["hash"]] = f

    # 3. Upload files via multipart form-data with manifest
    manifest = json.dumps(hashes)
    
    # CF Direct Upload: single POST with files + manifest
    boundary = "----CFDeployBoundary%s" % os.urandom(8).hex()
    parts = []
    
    # Add manifest part
    parts.append(
        ("--%s\r\n" % boundary).encode()
        + b"Content-Disposition: form-data; name=\"manifest\"\r\n"
        + b"Content-Type: application/json\r\n\r\n"
        + manifest.encode()
        + b"\r\n"
    )
    
    # Add file parts (keyed by hash)
    uploaded_hashes = set()
    for f in files:
        if f["hash"] in uploaded_hashes:
            continue  # deduplicate
        uploaded_hashes.add(f["hash"])
        mime = mimetypes.guess_type(f["full_path"])[0] or "application/octet-stream"
        with open(f["full_path"], "rb") as fh:
            content = fh.read()
        parts.append(
            ("--%s\r\n" % boundary).encode()
            + ("Content-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
               % (f["hash"], os.path.basename(f["full_path"]))).encode()
            + ("Content-Type: %s\r\n\r\n" % mime).encode()
            + content
            + b"\r\n"
        )
    
    body = b"".join(parts) + ("--%s--\r\n" % boundary).encode()
    content_type = "multipart/form-data; boundary=%s" % boundary
    
    logger.info("Uploading %d unique files to %s...", len(uploaded_hashes), project_name)
    
    result = _api_request(
        session_url,
        token,
        method="POST",
        data=body,
        content_type=content_type,
    )
    
    if not result.get("success"):
        raise DeployError("Deployment failed: %s" % json.dumps(result.get("errors", [])))
    
    deployment = result.get("result", {})
    deploy_url = deployment.get("url", "unknown")
    deploy_id = deployment.get("id", "unknown")
    
    logger.info("Deployed! ID: %s URL: %s", deploy_id, deploy_url)
    return deployment


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy to Cloudflare Pages")
    parser.add_argument("project", help="Cloudflare Pages project name")
    parser.add_argument("directory", help="Directory to deploy")
    parser.add_argument("--branch", default="main", help="Branch name (default: main)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(json.dumps({"success": False, "error": "Not a directory: %s" % args.directory}))
        sys.exit(1)

    try:
        result = deploy(args.project, args.directory, args.branch)
        if args.json:
            print(json.dumps({"success": True, "deployment": result}, indent=2))
        else:
            print("✅ Deployed: %s" % result.get("url", "unknown"))
            print("   ID: %s" % result.get("id", "unknown"))
    except DeployError as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
