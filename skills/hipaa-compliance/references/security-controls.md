# HIPAA Safeguards & Control Patterns

## Administrative Safeguards
- **Risk Analysis & Management**: Maintain asset inventory, data flows, threat modeling. Review at least annually or after major change.
- **Workforce Security**: Background checks, least privilege onboarding, timely offboarding, role-based training.
- **Information Access Management**: Role definitions, approval workflow, periodic recertification, emergency access procedures.
- **Security Awareness & Training**: Phishing simulations, secure coding training, insider threat education.
- **Contingency Plan**: Backup strategy (onsite/offsite), disaster recovery runbooks, emergency mode operations.
- **Business Associate Management**: Due diligence checklist, signed BAA, continuous monitoring, incident clauses.

## Physical Safeguards
- Facility access controls, visitor logs, badge policies.
- Device/media controls: encryption, secure disposal, chain-of-custody tracking.
- Workstation security: auto-lock, privacy screens, location policies.

## Technical Safeguards
- **Access Control**: MFA, contextual policies, session timeouts, just-in-time elevation.
- **Audit Controls**: Immutable logs (centralized SIEM), retention ≥6 years, monitoring for anomalous access.
- **Integrity Controls**: Checksums, digital signatures, configuration baselines, WORM backups.
- **Transmission Security**: TLS 1.2+, secure APIs, message-level encryption for queues, VPN/priv networks.
- **Encryption at Rest**: FIPS 140-2 validated modules where feasible, key rotation, envelope encryption.
- **Automatic Logoff**: Idle timeout, token expiry, re-auth for sensitive actions.

## Mapping to Software Delivery
| Area | Implementation Ideas |
| --- | --- |
| Identity | Central IdP + SCIM, per-environment RBAC, emergency break-glass accounts with logging. |
| Infrastructure | IaC with guardrails, hardened AMIs, CIS benchmarks, patch cadence. |
| Application | Data minimization, field-level encryption, consent tracking, immutable audit trails. |
| Data Lifecycle | Classification tags, retention scheduler, secure deletion workflows, encrypted backups + restore testing. |
| Monitoring | Correlate auth logs + API traces, PHI access dashboards, anomaly detection for bulk exports. |
| Incident Response | Runbook templates, RACI, tabletop exercises focusing on PHI exposures. |
