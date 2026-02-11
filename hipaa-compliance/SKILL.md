---
name: hipaa-compliance
description: Build and validate HIPAA-compliant software and infrastructure. Use when designing healthcare workloads that handle PHI/ePHI, mapping safeguards, drafting policies/BAAs, running HIPAA risk analyses, or performing deployment readiness and ongoing compliance checks.
---

## Quick Start
1. **Scope & Intake**
   - Identify whether the requester is a Covered Entity or Business Associate and capture their PHI data flows (who supplies PHI, where it is processed/stored, integrations).
   - Read [references/hipaa-overview.md](references/hipaa-overview.md) to refresh rule requirements and terminology.
2. **Threat & Safeguard Planning**
   - For each component (identity, app, infra, data), map administrative/physical/technical safeguards using [references/security-controls.md](references/security-controls.md).
   - Capture control decisions in a risk register (threat, impact, mitigation, owner, review date).
3. **Architecture & Policy Alignment**
   - Ensure PHI workloads are isolated networks/projects with encryption, key management, logging, and backup plans.
   - Confirm BAAs exist for every vendor/service that stores or transports PHI. Highlight gaps.
4. **Validation Workflow**
   - Follow the build/pre-deployment/ongoing checklists in [references/validation-checklists.md](references/validation-checklists.md).
   - Require evidence links (ticket IDs, screenshots, config hashes) for each checklist item when delivering compliance packages.
5. **Documentation Pack**
   - Produce: updated data inventory, risk analysis summary, control matrix, incident response alignment, training plan, monitoring dashboard outline.
   - Note breach-notification SLAs and escalation contacts.

## Detailed Procedure

### 1. Intake & Data Inventory
- Capture PHI categories (demographics, lab results, payment) and whether data crosses borders.
- Note minimum necessary requirements: where can PHI be tokenized, redacted, or aggregated?
- Build/update architecture diagrams with trust boundaries.

### 2. Vendor & BAA Management
- List every SaaS/tool touching PHI; verify signed BAAs and security posture (SOC 2 Type II, HITRUST, etc.).
- If a BAA is missing, flag as a blocker and recommend alternates.

### 3. Safeguard Design
- Administrative: onboarding/offboarding, role-based training, contingency planning.
- Physical: hosting provider attestations, device controls if on-prem.
- Technical: IAM, encryption, logging, monitoring, session control.
- For each safeguard, record owner, implementation detail, monitoring method, and verification cadence.

### 4. Build & Test Controls
- Infrastructure-as-code with policy guardrails (terraform compliance checks, OPA policies).
- Application controls: field-level encryption, audit logging middleware, consent capture, secure API patterns.
- Security testing: SAST/DAST, dependency scans, manual review for PHI exposure paths, pen test scope including PHI APIs.

### 5. Pre-Deployment Readiness
- Walk through the Pre-Deployment section of `validation-checklists.md` item by item.
- Validate backup/restore, failover, and incident response tabletop referencing PHI-specific scenarios.
- Confirm monitoring dashboards include PHI access metrics and anomaly detection.

### 6. Ongoing Compliance Plan
- Define cadence for access recertification, risk analysis, training, vulnerability management, and disaster recovery tests.
- Outline breach-notification workflow: detection → assessment → legal/privacy review → notification clock.

### 7. Deliverables Template
Provide the user with a summary covering:
- **Risk analysis highlights** (top risks, mitigations, residual risk notes).
- **Control matrix** mapping HIPAA safeguard requirements to implemented controls.
- **Evidence index**: link to logs, diagrams, test results, policies.
- **Action register**: outstanding gaps with owners and deadlines.

## Tips
- When uncertain about whether data is PHI, err on the side of treating it as such unless explicitly de-identified under HIPAA Safe Harbor or Expert Determination.
- Emphasize “minimum necessary” in data pipelines—strip identifiers before analytics where feasible.
- Maintain alignment with other frameworks (SOC 2, HITRUST, NIST 800-53) by reusing control mappings.
- Document assumptions. HIPAA is risk-based; auditors look for the thought process even when perfect compliance is impossible.
