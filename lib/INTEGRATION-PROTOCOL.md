# Cross-Skill Integration Protocol

## Overview

This protocol defines how skills interact. The LLM agent reads each skill's SKILL.md and follows these integration rules. Skills never import each other directly.

## Before Any Skill Operation

```
1. RECALL — Check agent-memory for prior context
   python3 skills/agent-memory/scripts/memory.py recall "{skill} {operation} {entity}" --limit 5

2. APPLY — Use recalled context to inform the current operation
```

## After Significant Skill Output

```
3. REMEMBER — Store outcome in agent-memory
   python3 skills/agent-memory/scripts/memory.py remember "[{skill}] {summary}" --type episodic

4. LOG — If external action, log to audit trail
   python3 skills/agent-guardrails/scripts/guardrails.py log --action {type} --tier {T1-T4} --decision allow
```

## Before Any External Action

```
5. SCAN — Check for PII/secrets in outbound content
   python3 skills/agent-guardrails/scripts/guardrails.py scan --text "{content}"

6. CHECK — Classify risk tier
   python3 skills/agent-guardrails/scripts/guardrails.py check --action {type} --target {dest}

7. GATE — If requires_confirmation=true, ask user before proceeding
```

## Programmatic Access

For skills with Python scripts, import the shared library:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from lib.integration import recall_context, remember_outcome, safe_check, safe_scan, unified_search
```

## Skill-Specific Integration Points

### email-manager
- **Before send**: `guardrails.py scan` on body, `guardrails.py check --action send_email`
- **After send**: `memory.py remember "[email-manager] Sent to {to}: {subject}"`
- **After triage**: `memory.py remember "[email-manager] Urgent: {subject} from {sender}"`
- **Already wired** in `email_client.py` — no action needed

### customer-support
- **Before research**: `memory.py recall "[customer-support] {customer_name}"` for prior tickets
- **Before draft-response**: recall similar past responses for consistency
- **After escalate**: create task via `task-planner` scripts, remember escalation
- **Before sending response**: `guardrails.py scan` on response text

### legal
- **Before review-contract**: `memory.py recall "[legal] {vendor_name}"` for prior reviews
- **After review-contract**: `memory.py remember "[legal] Reviewed {vendor} contract: {risk_level}"`
- **Cross-reference**: recall sales and finance context for same vendor

### sales
- **Before call-prep**: `memory.py recall "[sales] {company_name}"` for deal history
- **After call-debrief**: `memory.py remember "[sales] Call with {company}: {outcome}"`
- **Before outreach**: `guardrails.py scan` on email body, check tier

### finance
- **Before variance-analysis**: recall prior period patterns
- **After close-checklist**: `memory.py remember "[finance] {period} close completed: {notes}"`
- **Cross-reference**: recall data-analysis queries for same accounts

### marketing
- **Before create-content**: `memory.py recall "[marketing] {topic} brand voice"`
- **After campaign results**: `memory.py remember "[marketing] Campaign {name}: {results}"`
- **Before publishing**: `guardrails.py scan` on content

### product-management
- **Before write-spec**: `memory.py recall "[product-management] {feature} {product}"`
- **After spec written**: `memory.py remember "[product-management] PRD: {feature} — {status}"`

### data-analysis
- **Before write-query**: `memory.py recall "[data-analysis] {table_name} schema"` for cached schema info
- **After explore-data**: `memory.py remember "[data-analysis] {table}: {row_count} rows, {summary}"` as semantic

### enterprise-search
- **Fan-out sources**: email-manager search, agent-memory recall, task-planner search
- **After search**: remember useful cross-references

### bio-research
- **Before literature-review**: `memory.py recall "[bio-research] {topic}"` for prior reviews
- **After analysis**: `memory.py remember "[bio-research] {analysis_type}: {key_finding}"`

### cloudflare-deploy
- **Before deploy**: `guardrails.py check --action deploy_site --target {project}`
- **After deploy**: `memory.py remember "[cloudflare-deploy] Deployed {project} commit {hash}"`

### security
- **After audit**: `memory.py remember "[security] Audit {target}: {finding_count} findings"`
- **Cross-reference**: recall prior audits for regression tracking

### devops
- **Before infra changes**: `guardrails.py check --action infra_change --target {resource}`
- **After deployment**: `memory.py remember "[devops] Deployed {service} to {env}"`

### task-planner
- **Receives from**: customer-support escalations, product-management roadmap items
- **After project completion**: `memory.py remember "[task-planner] Completed project: {name}"`
