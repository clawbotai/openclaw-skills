---
name: mailcow-manager
description: Provision Hetzner VPS, install Mailcow dockerized mail server, manage domains/mailboxes/aliases/DKIM, and configure Cloudflare DNS records for multi-domain email hosting.
---

## Overview

End-to-end mail server management: provision infrastructure, install Mailcow, configure DNS, and manage email accounts across multiple domains.

## Prerequisites

- Python 3.9+
- Environment variables (store in macOS Keychain):
  - `HETZNER_API_TOKEN` — from Hetzner Cloud console
  - `MAILCOW_HOST` — e.g. `mail.torrstatics.com`
  - `MAILCOW_API_KEY` — from Mailcow admin panel (generated during setup)
  - `CLOUDFLARE_API_TOKEN` — for DNS management
  - `CLOUDFLARE_ACCOUNT_ID` — for DNS management

## Workflow

### 1. Provision Server

```bash
# List available server types
python scripts/hetzner.py types

# Create VPS with mail firewall
python scripts/hetzner.py create mailcow-01 --type cx22 --image ubuntu-24.04 --location fsn1 --firewall

# Note the IP address from output
```

### 2. Configure DNS

```bash
# Set up all mail DNS records (MX, SPF, DMARC, autodiscover)
python scripts/dns_setup.py setup torrstatics.com <SERVER_IP>

# IMPORTANT: Set rDNS (PTR) in Hetzner panel: <IP> → mail.torrstatics.com
```

### 3. Install Mailcow

```bash
# Generate setup script (review it first)
python scripts/setup.py generate mail.torrstatics.com --timezone America/New_York

# Or install directly via SSH
python scripts/setup.py install mail.torrstatics.com <SERVER_IP> --ssh-key ~/.ssh/id_rsa
```

### 4. Manage Domains & Mailboxes

```bash
# Add a domain
python scripts/mailcow.py domain add torrstatics.com

# Create mailboxes
python scripts/mailcow.py mailbox add signal@torrstatics.com "SecurePass123!"
python scripts/mailcow.py mailbox add steven@torrstatics.com "SecurePass123!"

# Generate DKIM key
python scripts/mailcow.py dkim add torrstatics.com

# Get DKIM record and add to DNS
python scripts/mailcow.py dkim get torrstatics.com
python scripts/dns_setup.py add-dkim torrstatics.com "<dkim_value>"

# Add aliases
python scripts/mailcow.py alias add info@torrstatics.com signal@torrstatics.com

# Verify DNS
python scripts/dns_setup.py verify torrstatics.com
```

### 5. Add More Domains

Repeat steps 2 and 4 for each new domain. Mailcow handles multi-domain natively.

### 6. Monitor

```bash
python scripts/mailcow.py status
python scripts/mailcow.py queue list
python scripts/mailcow.py logs postfix --count 20
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/hetzner.py` | Hetzner Cloud VPS lifecycle (create/list/delete/firewall) |
| `scripts/mailcow.py` | Mailcow API (domains/mailboxes/aliases/DKIM/queue/logs) |
| `scripts/dns_setup.py` | Cloudflare DNS (MX/SPF/DKIM/DMARC/autodiscover) |
| `scripts/setup.py` | Mailcow installation script generator + SSH installer |

## Security Notes

- Change the default Mailcow admin password (`admin`/`moohoo`) immediately after install
- Store API keys in macOS Keychain, not in env files
- TLS is enforced on all mailbox connections by default
- The generated firewall only opens mail-related ports + SSH
