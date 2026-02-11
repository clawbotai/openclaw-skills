# HIPAA Software Validation Checklists

## Build-Time Checklist
1. **Scope & Data Mapping**
   - Document PHI data elements, sources, destinations, retention.
   - Classify services containing ePHI; isolate into compliant VPC/project.
2. **Architecture Review**
   - Confirm segregation of public vs. PHI workloads.
   - Encryption at rest/in transit documented (KMS/HSM, TLS versions).
   - Logging & monitoring coverage (auth, data access, admin actions).
3. **Policies & Agreements**
   - BAA executed for each vendor touching PHI.
   - Access control policy updated for new roles/services.
   - Incident response + breach notification plan references service.
4. **Secure SDLC Controls**
   - Static/dynamic analysis gates, dependency scanning, IaC scanning.
   - Threat model completed w/ mitigations.
   - Privacy review for minimum necessary PHI.

## Pre-Deployment Validation
1. **Access Tests**
   - RBAC enforced per role; no shared accounts.
   - MFA on all privileged paths.
   - Break-glass flow tested and logged.
2. **Audit & Monitoring**
   - Verify PHI access logs ship to SIEM with retention ≥6 years.
   - Alert rules for bulk export, failed logins, privilege escalations.
3. **Data Protection**
   - Backup/restore exercise performed.
   - Key rotation procedure documented; secrets stored in managed vault.
4. **Operational Readiness**
   - Runbook covering outages, DR, incident response.
   - Support team training + escalation tree.
   - Penetration test or targeted security assessment completed.

## Ongoing Compliance Tasks
- Quarterly access recertification for PHI systems.
- Annual risk analysis refresh.
- Monthly vulnerability patching cadence reports.
- Semiannual incident tabletop exercises (privacy + security scenarios).
- Breach notification drill (timelines, communications, legal review).
