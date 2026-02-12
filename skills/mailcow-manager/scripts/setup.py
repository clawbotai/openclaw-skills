#!/usr/bin/env python3
"""Mailcow installation script generator.

Generates a cloud-init / SSH setup script for deploying Mailcow
on a fresh Ubuntu VPS (Hetzner or any provider).

Usage:
    python setup.py generate <hostname> [--timezone UTC]
    python setup.py install <hostname> <server_ip> [--ssh-key ~/.ssh/id_rsa]

The 'generate' command outputs a shell script.
The 'install' command SSHs into the server and runs the setup.

Requires: MAILCOW_HOSTNAME env var or --hostname flag.
Python 3.9+ stdlib only.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys


MAILCOW_SETUP_SCRIPT = """#!/bin/bash
set -euo pipefail

HOSTNAME="{hostname}"
TIMEZONE="{timezone}"

echo "=== TØRR STATICS Mail Server Setup ==="
echo "=== Hostname: $HOSTNAME ==="
echo "=== Timezone: $TIMEZONE ==="

# Update system
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose plugin
apt-get install -y -qq docker-compose-plugin

# Set timezone
timedatectl set-timezone "$TIMEZONE"

# Set hostname
hostnamectl set-hostname "$HOSTNAME"

# Clone Mailcow
cd /opt
git clone https://github.com/mailcow/mailcow-dockerized.git
cd mailcow-dockerized

# Generate config
cat > mailcow.conf << 'MCEOF'
MAILCOW_HOSTNAME={hostname}
MAILCOW_TZ={timezone}
DBNAME=mailcow
DBUSER=mailcow
DBROOT=auto
DBPASS=auto
HTTP_PORT=80
HTTP_BIND=0.0.0.0
HTTPS_PORT=443
HTTPS_BIND=0.0.0.0
SMTP_PORT=25
SMTPS_PORT=465
SUBMISSION_PORT=587
IMAP_PORT=143
IMAPS_PORT=993
POP_PORT=110
POPS_PORT=995
SIEVE_PORT=4190
API_KEY=auto
API_ALLOW_FROM=0.0.0.0/0
COMPOSE_PROJECT_NAME=mailcowdockerized
SKIP_LETS_ENCRYPT=n
ENABLE_SSL_SNI=n
SKIP_SOGO=n
SKIP_CLAMD=n
SKIP_SOLR=y
ADDITIONAL_SAN=
MCEOF

# Generate random passwords
sed -i "s/DBROOT=auto/DBROOT=$(openssl rand -hex 16)/" mailcow.conf
sed -i "s/DBPASS=auto/DBPASS=$(openssl rand -hex 16)/" mailcow.conf
API_KEY=$(openssl rand -hex 32)
sed -i "s/API_KEY=auto/API_KEY=$API_KEY/" mailcow.conf

# Start Mailcow
docker compose pull
docker compose up -d

echo ""
echo "========================================="
echo "  MAILCOW INSTALLATION COMPLETE"
echo "========================================="
echo ""
echo "  Admin Panel: https://$HOSTNAME"
echo "  Default Login: admin / moohoo"
echo "  API Key: $API_KEY"
echo ""
echo "  CHANGE THE DEFAULT PASSWORD IMMEDIATELY"
echo ""
echo "  Save this API key for MAILCOW_API_KEY env var"
echo "========================================="
"""


def generate_script(hostname: str, timezone: str = "UTC") -> str:
    return MAILCOW_SETUP_SCRIPT.format(hostname=hostname, timezone=timezone)


def install_remote(hostname: str, server_ip: str, ssh_key: str, timezone: str) -> None:
    """SSH into server and run the setup script."""
    script = generate_script(hostname, timezone)

    # Write temp script
    script_path = "/tmp/mailcow_setup.sh"
    with open(script_path, "w") as f:
        f.write(script)

    print("Uploading setup script to %s..." % server_ip)
    scp_cmd = ["scp", "-o", "StrictHostKeyChecking=no"]
    if ssh_key:
        scp_cmd.extend(["-i", ssh_key])
    scp_cmd.extend([script_path, "root@%s:/tmp/mailcow_setup.sh" % server_ip])

    result = subprocess.run(scp_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("SCP failed: %s" % result.stderr)
        sys.exit(1)

    print("Running setup (this takes 5-10 minutes)...")
    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no"]
    if ssh_key:
        ssh_cmd.extend(["-i", ssh_key])
    ssh_cmd.extend([
        "root@%s" % server_ip,
        "bash /tmp/mailcow_setup.sh"
    ])

    result = subprocess.run(ssh_cmd)
    sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mailcow Setup Generator")
    sub = parser.add_subparsers(dest="command")

    p_gen = sub.add_parser("generate", help="Generate setup script")
    p_gen.add_argument("hostname", help="Mail hostname (e.g. mail.torrstatics.com)")
    p_gen.add_argument("--timezone", default="UTC")

    p_install = sub.add_parser("install", help="Install via SSH")
    p_install.add_argument("hostname", help="Mail hostname")
    p_install.add_argument("server_ip", help="Server IP address")
    p_install.add_argument("--ssh-key", default=None)
    p_install.add_argument("--timezone", default="UTC")

    args = parser.parse_args()

    if args.command == "generate":
        print(generate_script(args.hostname, args.timezone))
    elif args.command == "install":
        install_remote(args.hostname, args.server_ip, args.ssh_key, args.timezone)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
