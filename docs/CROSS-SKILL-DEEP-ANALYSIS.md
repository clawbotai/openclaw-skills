# Cross-Skill Deep Analysis

## Skill Capability Matrix

### Layer 1 — Platform Services (always-on, used by other skills)

| Skill | Provides | Consumers | Has Scripts |
|-------|----------|-----------|-------------|
| **agent-memory** | Vector search, entity extraction, knowledge graph | ALL skills | ✓ memory.py |
| **agent-guardrails** | Risk classification, PII detection, rate limiting, audit | ALL external-facing skills | ✓ guardrails.py, snapshot.py |
| **agent-orchestration** | Fan-out/fan-in, pipeline, supervisor, expert panel, map-reduce | Complex multi-skill workflows | ✓ orchestrator.py |

### Layer 2 — Lifecycle & Discovery (meta-skills that manage other skills)

| Skill | Provides | Consumers |
|-------|----------|-----------|
| **skill-lifecycle** | Evo loop (Research→Build→Reflect), AIOps monitor, circuit breakers | skill-creator-extended, skill-scout |
| **skill-creator-extended** | 4-phase skill generation, composition patterns, validation | User-triggered |
| **skill-scout** | ClawHub/GitHub discovery, quality scoring, quarantine, acquisition | skill-creator-extended, skill-lifecycle |

### Layer 3 — Infrastructure (deployment, email, docs)

| Skill | Provides | Consumers |
|-------|----------|-----------|
| **cloudflare-deploy** | CF Pages deploy, project mgmt, rollback | web-builder |
| **mailcow-manager** | Mail server provisioning, domain/mailbox mgmt | email-manager |
| **email-manager** | IMAP/SMTP operations, search, triage | enterprise-search, customer-support, marketing |
| **docs-engine** | Diátaxis scaffolding, quality scoring, Gold Standard | ALL skills (documentation) |
| **web-builder** | SvelteKit, HTML bundling, deployment | task-planner (dashboard), data-analysis (dashboard) |

### Layer 4 — Engineering (build, secure, observe, operate)

| Skill | Provides | Consumers |
|-------|----------|-----------|
| **python-backend** | FastAPI/Django/Flask patterns, ORM, async, testing | MPMP, any backend project |
| **devops** | CI/CD, IaC, containers, K8s, GitOps | All deployed projects |
| **security** | AppSec, vuln mgmt, compliance, threat modeling | ALL skills (security review) |
| **observability** | Logging, tracing, metrics, SLOs, dashboards | ALL deployed services |

### Layer 5 — Domain Expertise (business function skills)

| Skill | Provides |
|-------|----------|
| **legal** | Contract review, NDA triage, compliance nav, risk assessment |
| **sales** | Pipeline mgmt, call prep, forecasting, battlecards |
| **customer-support** | Ticket triage, response drafting, escalation, KB authoring |
| **product-management** | PRDs, roadmaps, stakeholder comms, research synthesis |
| **marketing** | Content creation, campaigns, SEO, brand voice, competitive intel |
| **finance** | Journal entries, reconciliation, statements, variance, close mgmt |
| **data-analysis** | SQL, EDA, dashboards, statistics |
| **enterprise-search** | Unified cross-tool search |
| **bio-research** | Literature review, scRNA-seq, pipelines, drug discovery |
| **task-planner** | Task tracking, Kanban, workplace memory, daily planning |

---

## Integration Opportunities

### TIER 1 — Foundation Layer (prerequisite for everything else)

#### 1A. agent-memory → ALL skills (Shared Brain)
**Status:** lib/memory_client.py exists but unwired
**What it enables:** Every skill remembers past interactions. Legal recalls prior contract reviews for the same vendor. Sales remembers deal history. Finance knows last quarter's close patterns.

**Concrete wiring points:**

| Skill | Remember (write) | Recall (read) |
|-------|------------------|---------------|
| email-manager | Store important email summaries after triage | Recall context about sender/thread before drafting reply |
| customer-support | Store resolved ticket patterns | Recall similar past tickets during research |
| legal | Store contract review results, playbook deviations | Recall prior reviews for same vendor/template |
| sales | Store call debrief notes, deal stage changes | Recall account history before call prep |
| finance | Store variance explanations, close notes | Recall prior period patterns during analysis |
| data-analysis | Store validated query patterns, schema notes | Recall dataset profiles and past queries |
| product-management | Store spec decisions, research findings | Recall prior specs and roadmap context |
| marketing | Store campaign results, content performance | Recall brand voice examples, what worked |
| bio-research | Store paper summaries, analysis results | Recall prior literature reviews on same topic |
| task-planner | Store completed project retrospectives | Recall similar past projects for estimation |
| skill-lifecycle | Store error patterns, fix histories | Recall what fix worked for similar errors |
| security | Store audit findings, remediation results | Recall prior vulns in same codebase |

**Implementation:** Add `--remember` flag to each skill's key operations. After significant output, auto-store a compressed summary via `memory.py remember`.

#### 1B. agent-guardrails → ALL external-facing skills (Safety Gate)
**Status:** lib/guardrails_client.py exists but unwired
**What it enables:** PII detection before emails go out. Rate limiting on API calls. Audit trail for compliance.

**Concrete wiring points:**

| Skill | Gate Point | Risk Tier |
|-------|-----------|-----------|
| email-manager | Before `send` — scan body for PII/secrets | T3 |
| marketing | Before publishing content externally | T3 |
| sales | Before sending outreach emails | T3 |
| customer-support | Before sending customer responses | T3 |
| cloudflare-deploy | Before deploying to production | T3 |
| mailcow-manager | Before provisioning servers ($$) | T4 |
| web-builder | Before deploying to public URLs | T3 |
| devops | Before CI/CD changes, infrastructure modifications | T3-T4 |

**Implementation:** Before each external action, call `guardrails.py check --action <type> --target <dest>` and `guardrails.py scan --text <content>`. Abort if tier requires confirmation and user hasn't approved.

---

### TIER 2 — Data Pipelines (skills feeding each other)

#### 2A. enterprise-search → email-manager + task-planner + web search
**Pattern:** Fan-out search
**What it enables:** "Find everything about Project X" searches email, tasks, and web simultaneously.

```
enterprise-search decomposes query
  ├── email-manager search --query "Project X" → email results
  ├── task-planner search "Project X" → task/project results  
  ├── agent-memory recall "Project X" → memory results
  └── web_search "Project X" → web results
  
Merge → deduplicate → confidence score → unified results
```

**New integration:** task-planner as a searchable source (not in current architecture). task-planner has `scripts/task_manager.py` with search capability — enterprise-search should query it.

#### 2B. customer-support → enterprise-search → email-manager (Research Chain)
**Pattern:** Cascading enrichment
**What it enables:** `/support:research` automatically pulls customer email history, past tickets, and documentation.

```
support:research("Customer reports Feature X broken")
  → enterprise-search:search("Feature X issues customer bugs")
    → email-manager:search("Feature X" from:customer@...) 
    → task-planner:search("Feature X bug")
    → agent-memory:recall("Feature X known issues")
  → Synthesize with confidence scoring
  → support:draft-response (from enriched context)
```

#### 2C. data-analysis ↔ finance (Bidirectional Data Flow)
**Pattern:** Bidirectional
**What it enables:** Finance requests data extraction via data-analysis SQL skills. Data-analysis uses finance's chart of accounts for correct categorization.

```
finance:variance-analysis needs raw data
  → data-analysis:write-query (generates SQL for budget vs actual)
  → data-analysis:statistical-analysis (tests significance of variances)
  → finance interprets with accounting standards context

data-analysis:explore-data on financial tables
  → finance provides chart of accounts mapping
  → data-analysis uses correct metric definitions
```

#### 2D. data-analysis → marketing (Campaign Analytics)
**Pattern:** Sequential
**What it enables:** Marketing performance reports backed by real SQL queries instead of manual data.

```
marketing:performance-report
  → data-analysis:write-query (sessions, conversions, revenue by channel)
  → data-analysis:build-dashboard (self-contained HTML)
  → marketing interprets and adds strategic narrative
```

#### 2E. data-analysis → product-management (Metrics & OKRs)
**Pattern:** Sequential
**What it enables:** PM metrics tracking backed by actual data queries.

```
pm:synthesize-research (usage data component)
  → data-analysis:explore-data (feature adoption, funnel analysis)
  → data-analysis:statistical-analysis (A/B test results)
  → PM synthesizes into product insights
```

#### 2F. bio-research → data-analysis (Genomics Statistics)
**Pattern:** Sequential
**What it enables:** scRNA-seq DE analysis, clinical trial data analysis, compound screening statistics.

```
bio:analyze-scrna produces count matrices/DE results
  → data-analysis:statistical-analysis (Benjamini-Hochberg, enrichment)
  → data-analysis:build-dashboard (gene expression heatmap, volcano plot)
```

---

### TIER 3 — Business Workflow Compositions (multi-skill orchestrations)

#### 3A. Deal Review (legal + sales + finance)
**Pattern:** Expert Panel (agent-orchestration)
**Trigger:** "Review this deal/contract before signing"

```
agent-orchestration: Expert Panel pattern
  ├── Spawn: legal/review-contract → clause analysis, risk flags (G/Y/R)
  ├── Spawn: sales/call-prep → deal strategy, competitive position, account history
  ├── Spawn: finance/journal-entry → revenue recognition assessment (ASC 606)
  └── Orchestrator merges into unified Deal Review Brief
      → Conflicts highlighted (e.g., legal says high risk, sales says strategic)
      → Recommended action with weighted rationale
```

**Implementation:** Use `sessions_spawn` for each expert. Each gets: contract text + deal context. Orchestrator synthesizes.

#### 3B. Product Launch (PM → marketing → sales → support)
**Pattern:** Pipeline (agent-orchestration)
**Trigger:** "Plan the launch for [feature]"

```
Step 1: pm/write-spec → PRD with features, audience, success metrics
Step 2: marketing/plan-campaign (receives PRD) → campaign plan, content calendar, messaging
Step 3: sales/battlecard (receives PRD + campaign) → competitive positioning, outreach templates
Step 4: support/write-kb (receives PRD) → KB articles, FAQ, known limitations
Step 5: task-planner creates launch project with all deliverables tracked
```

#### 3C. Incident Response (security → devops → observability → legal → support)
**Pattern:** Supervisor (agent-orchestration)
**Trigger:** Security incident detected

```
Supervisor orchestrates:
  1. security: threat assessment, containment recommendation
  2. devops: execute containment (firewall rules, service isolation)
  3. observability: trace analysis, blast radius assessment
  4. legal: compliance obligations (notification deadlines, regulatory)
  5. support: customer communication drafting
  6. task-planner: incident tasks with deadlines
  7. agent-memory: store incident for future reference
```

#### 3D. Customer Onboarding (support + PM + marketing + task-planner)
**Pattern:** Pipeline
**Trigger:** "Set up onboarding for new customer [name]"

```
Step 1: support/research → customer profile, use case, tier
Step 2: pm/write-spec → success criteria for this customer's use case
Step 3: marketing/create-content → welcome email sequence, personalized guides
Step 4: task-planner → onboarding project with milestones and check-in dates
Step 5: agent-memory → store customer profile for future interactions
```

#### 3E. Quarterly Business Review (finance + sales + PM + data-analysis)
**Pattern:** Fan-out / Fan-in
**Trigger:** "Prepare QBR for Q1"

```
Parallel:
  ├── finance/financial-statements → P&L, balance sheet, key ratios
  ├── finance/variance-analysis → budget vs actual with narratives
  ├── sales/pipeline-review + sales/forecast → pipeline health, Q2 forecast
  ├── pm/roadmap-update → shipped features, upcoming roadmap
  ├── data-analysis/build-dashboard → KPI dashboard (HTML)
  └── marketing/performance-report → campaign results, brand metrics

Merge → Executive QBR deck with sections from each skill
```

#### 3F. Research Project (bio-research + data-analysis + docs-engine + task-planner)
**Pattern:** Pipeline with iteration
**Trigger:** "Start a research project on [topic]"

```
Step 1: bio-research/literature-review → systematic review, gap analysis
Step 2: bio-research/run-pipeline → data generation (sequencing, etc.)
Step 3: data-analysis/statistical-analysis → hypothesis testing
Step 4: bio-research/analyze-scrna → biological interpretation
Step 5: docs-engine → paper/report generation (Diátaxis structure)
Step 6: task-planner → project milestones, experiment checklist
Loop: Steps 2-4 may repeat based on findings
```

---

### TIER 4 — Meta-Skill Integration (skills that improve skills)

#### 4A. Skill Factory Pipeline (scout → lifecycle → creator)
**Pattern:** Pipeline
**What it enables:** Fully autonomous skill acquisition and evolution.

```
User needs capability X
  → skill-scout/discover: search ClawHub + GitHub
  → skill-scout/evaluate: quality scoring (7 dimensions)
  
  IF score > threshold:
    → skill-scout/acquire (quarantine → security scan → install)
    → skill-lifecycle/monitor: begin monitoring
    
  IF no good external skill found:
    → skill-creator-extended/architect_skill.py: generate from scratch
    → skill-lifecycle: Research→Build→Reflect loop
    → skill-lifecycle/monitor: begin monitoring
    
  ON ERROR (runtime):
    → skill-lifecycle/monitor: classify error, check circuit breaker
    → skill-lifecycle/evo-loop: auto-repair
    → agent-memory: store fix for future reference
```

#### 4B. docs-engine → ALL skills (Documentation Quality)
**Pattern:** Periodic audit
**What it enables:** Every skill's SKILL.md gets quality-scored and improved.

```
docs-engine/score-quality on each skill's SKILL.md
  → Flag: missing sections, stale references, unclear workflows
  → Generate: missing documentation scaffolding
  → Track: documentation debt in task-planner
```

#### 4C. security → ALL skills (Security Audit Pipeline)
**Pattern:** Periodic sweep
**What it enables:** Automated security review of all skill scripts.

```
For each skill with scripts/:
  security/code-review → OWASP checks, secrets detection, input validation
  security/threat-model → STRIDE analysis of skill's attack surface
  agent-guardrails/scan → PII detection in reference files
  → Results stored in agent-memory
  → Remediation tasks created in task-planner
```

---

### TIER 5 — Infrastructure Compositions

#### 5A. web-builder + cloudflare-deploy + devops (Full Deployment Pipeline)
**Pattern:** Pipeline
**What it enables:** Build → Test → Deploy → Monitor in one workflow.

```
web-builder/scaffold → create SvelteKit app
  → devops/ci-cd → GitHub Actions pipeline
  → security/code-review → pre-deploy security check
  → cloudflare-deploy/deploy → push to CF Pages
  → observability/instrument → add monitoring
  → agent-memory → store deployment record
```

#### 5B. mailcow-manager + email-manager + cloudflare-deploy (Email Infrastructure)
**Pattern:** Sequential setup
**What it enables:** Full self-hosted email from provisioning to daily use.

```
mailcow-manager/provision → Hetzner VPS + Mailcow install
  → mailcow-manager/dns → Cloudflare DNS records (MX, SPF, DKIM, DMARC)
  → mailcow-manager/mailbox → create mailboxes
  → email-manager → daily operations (send, receive, triage)
  → agent-guardrails → PII scanning on all outbound email
```

#### 5C. python-backend + security + observability + devops (Backend Stack)
**Pattern:** Layered composition
**What it enables:** Any new backend service gets security, monitoring, and CI/CD from day one.

```
python-backend: FastAPI scaffold
  → security: auth patterns, input validation, secrets management
  → observability: structured logging, tracing, health endpoints
  → devops: Dockerfile, CI/CD pipeline, deployment config
  → docs-engine: API documentation scaffold
```

---

## Opportunity Summary

| # | Integration | Skills | Pattern | Effort | Impact | Priority |
|---|-------------|--------|---------|--------|--------|----------|
| 1A | Shared Brain | memory → all | Hub | High | Critical | **P0** |
| 1B | Safety Gate | guardrails → all external | Hub | Medium | Critical | **P0** |
| 2A | Unified Search | search → email + tasks + memory | Fan-out | Medium | High | **P1** |
| 2B | Support Research | support → search → email | Cascade | Medium | High | **P1** |
| 2C | Finance Data | data ↔ finance | Bidirectional | Low | High | **P1** |
| 3A | Deal Review | legal + sales + finance | Expert Panel | Medium | High | **P2** |
| 3B | Product Launch | PM → mktg → sales → support | Pipeline | Medium | High | **P2** |
| 3E | QBR Preparation | finance + sales + PM + data | Fan-out | Medium | High | **P2** |
| 4A | Skill Factory | scout → lifecycle → creator | Pipeline | High | High | **P2** |
| 2D | Campaign Analytics | data → marketing | Sequential | Low | Medium | **P2** |
| 2E | PM Metrics | data → PM | Sequential | Low | Medium | **P3** |
| 3C | Incident Response | security → devops → obs → legal | Supervisor | High | High | **P3** |
| 3D | Customer Onboarding | support + PM + mktg + tasks | Pipeline | Medium | Medium | **P3** |
| 4B | Doc Quality | docs-engine → all skills | Periodic | Low | Medium | **P3** |
| 4C | Security Audit | security → all scripts | Periodic | Medium | Medium | **P3** |
| 5A | Deploy Pipeline | web + CF + devops | Pipeline | Medium | Medium | **P3** |
| 5B | Email Infra | mailcow + email + CF | Sequential | High | Medium | **P3** |
| 5C | Backend Stack | python + security + obs + devops | Layered | Medium | Medium | **P4** |
| 2F | Genomics Stats | bio → data | Sequential | Low | Low | **P4** |
| 3F | Research Project | bio + data + docs + tasks | Pipeline | Medium | Low | **P4** |

---

## Recommended Implementation Order

### Phase 1: Wire the Foundation (P0)
1. Wire `agent-memory` into email-manager, customer-support, and task-planner
2. Wire `agent-guardrails` into email-manager (scan before send)
3. Add `--remember` capability to legal, sales, finance after significant outputs

### Phase 2: Enable Search & Data Flow (P1)
4. Wire enterprise-search to query email-manager and task-planner
5. Wire customer-support research to use enterprise-search
6. Wire data-analysis as data provider for finance variance analysis

### Phase 3: Business Compositions (P2)
7. Build Deal Review orchestration (legal + sales + finance expert panel)
8. Build Product Launch pipeline (PM → marketing → sales → support)
9. Build Skill Factory pipeline (scout → lifecycle → creator)
10. Wire data-analysis into marketing performance reports

### Phase 4: Advanced Integrations (P3-P4)
11. Incident Response orchestration
12. QBR preparation workflow
13. docs-engine periodic skill audit
14. security periodic code review sweep
