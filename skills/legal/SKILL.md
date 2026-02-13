---
name: legal
description: AI-powered legal workflow assistant — contract review, NDA triage, compliance navigation, risk assessment, meeting briefings, and templated responses. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Legal

An AI-powered productivity skill for in-house legal teams. Automates contract review against organizational playbooks, NDA triage with structured checklists, compliance workflow navigation, legal risk assessment using severity-by-likelihood matrices, meeting briefing generation, and templated response drafting.

**⚠️ DISCLAIMER**: This skill assists with legal workflows but does not provide legal advice. All analysis must be reviewed by qualified legal professionals. Include this disclaimer in all outputs.

## Activation Triggers

Activate when the user's request involves:
- Contract review, redlining, or clause analysis
- NDA review or triage
- Compliance questions (GDPR, CCPA, HIPAA, SOX)
- Legal risk assessment or exposure analysis
- Meeting prep for legal matters
- Drafting legal responses (DSARs, hold notices, etc.)
- Vendor agreement review

## Commands

### `/legal:review-contract`
Clause-by-clause contract review against negotiation playbook.

**Workflow:**
1. Receive contract document (pasted text, file, or connector)
2. Identify contract type and applicable playbook positions
3. Extract and analyze each major clause category:
   - **Limitation of Liability** — Standard: mutual cap at 12 months fees. Acceptable: 6-24 months. Escalation: uncapped or consequential damages.
   - **Indemnification** — Standard: mutual for IP infringement and data breach. Acceptable: limited to third-party claims. Escalation: unilateral or uncapped.
   - **IP Ownership** — Standard: each party retains pre-existing IP, customer owns customer data. Escalation: broad IP assignment.
   - **Data Protection** — Standard: require DPA. Requirements: sub-processor notification, deletion on termination, breach notification within 72 hours.
4. Classify each clause: 🟢 GREEN (acceptable), 🟡 YELLOW (negotiate if practical), 🔴 RED (must negotiate/escalate)
5. Identify missing standard clauses (default to RED)
6. Generate redline suggestions and negotiation strategy

**Output:** Executive Summary → Clause-by-Clause Analysis (G/Y/R) → Missing Clauses → Recommended Redlines → Negotiation Strategy → Risk Assessment

### `/legal:triage-nda`
Categorize incoming NDAs using structured checklist.

**Checklist items** (each receives: Standard / Needs Attention / Missing):
- Definition of Confidential Information
- Obligations of Receiving Party
- Term and Duration
- Permitted Disclosures
- Return/Destruction
- Remedies
- Residuals Clause
- Non-Solicitation
- Governing Law
- Assignment

**Routing:**
- **STANDARD APPROVAL**: All Standard, mutual, term ≤ 3 years
- **COUNSEL REVIEW**: 1-3 Needs Attention, or unilateral, or non-standard term, or non-solicitation present
- **FULL REVIEW**: Any Missing, 4+ Needs Attention, broad residuals, unusual governing law, assignment restrictions

### `/legal:vendor-check`
Check vendor agreement status, review third-party risk posture, surface contract details.

### `/legal:brief`
Generate contextual briefings. Types:
- **Daily Brief**: Scan 24-hour activity, active matters, deadlines
- **Topic Research**: Deep dive with implications
- **Incident Response**: Context, exposure, required actions

Structure: Key Facts → Relevant History → Action Items → Open Questions → Recommended Approach

### `/legal:respond`
Create templated responses for:
- Data Subject Access Requests (DSARs)
- Discovery/Litigation Holds
- Standard Inquiries (contract status, compliance cert, insurance verification)
- Regulatory Responses (breach notifications, audit responses)

All templates include professional disclaimers and customization placeholders.

## Auto-Firing Skills

### Contract Review
**Fires when:** User provides or references a contract, agreement, or asks about terms/clauses.
Apply the clause analysis framework above. Three-tier classification. Missing clauses default RED.

### NDA Triage
**Fires when:** User provides an NDA or confidentiality agreement.
Apply checklist workflow. Consistent format every time for cross-deal comparison.

### Compliance
**Fires when:** User asks about regulatory compliance, data protection, GDPR, CCPA, privacy.
Navigate compliance workflows: DPIAs, ROPAs, DPA requirements, breach notification timelines by jurisdiction, data subject rights, cross-border transfer mechanisms (SCCs, adequacy decisions, BCRs), cookie consent, privacy by design.

### Legal Risk Assessment
**Fires when:** User asks about risk classification or legal exposure.
Framework:
- **Severity**: Critical / High / Medium / Low
- **Likelihood**: Almost Certain (>90%) / Likely (60-90%) / Possible (30-60%) / Unlikely (10-30%) / Rare (<10%)
- Risk Score = Severity × Likelihood
- Priority matrix: Critical+Likely = Immediate GC escalation. High+Likely = Senior counsel 24h. Medium = Standard review. Low = Monitor.

### Canned Responses
**Fires when:** User asks for template responses or form letters.
Categories: DSARs, Discovery/Litigation Holds, Standard Inquiries, Regulatory Responses.

### Meeting Briefing
**Fires when:** User asks for meeting prep or background on a legal matter.
Synthesize from connected sources. Always include: Key Facts, Relevant History, Action Items, Open Questions, Recommended Approach.

## Configuration

```yaml
playbook: {}           # Standard positions, acceptable ranges, escalation triggers by clause type
escalation_contacts: [] # Named individuals for escalation routing
regulatory_jurisdictions: [] # Jurisdictions affecting compliance frameworks
template_library_path: "" # Path to custom response templates
risk_tolerance: "medium"  # Affects YELLOW/RED threshold
matter_management_ids: {} # Integration mapping for matter/case IDs
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Chat (Slack) | Legal channel context, prior decisions | Work from user-provided context |
| Cloud Storage (Box/SharePoint) | Contract repos, templates, playbooks | User pastes documents directly |
| Project Tracker (Jira) | Legal request tracking | Manual status tracking |
| Email/Calendar (M365) | Meeting invites, correspondence | User provides meeting details |

## Degraded Mode

Without connectors, the skill still functions by:
- Accepting pasted contract text for review
- Using built-in clause analysis framework
- Generating templates from internal knowledge
- Asking user for context that would normally come from connectors

## Cross-Skill Integration

### Memory Protocol
- **Before `/legal:review-contract`**: `memory.py recall "[legal] {vendor_name}"` — prior reviews, known issues, playbook deviations
- **Before `/legal:triage-nda`**: recall prior NDAs with same counterparty for consistency
- **After review**: `memory.py remember "[legal] Reviewed {vendor} {doc_type}: risk={G/Y/R}, key_issues={list}" --importance 0.8`
- **After compliance check**: store regulatory findings as semantic memory

### Safety Gate
- **Before sharing legal analysis externally**: `guardrails.py scan` for confidential terms/clauses

### Connected Skills
- **sales** → deal review composition: legal risk assessment + sales strategy + finance rev rec
- **finance** → contract financial terms feed into revenue recognition analysis
- **enterprise-search** → pull prior correspondence with vendor from email
