---
name: Master DevOps
description: Complete DevOps toolkit — CI/CD pipelines, infrastructure as code, containers, Kubernetes, GitOps, security, monitoring, progressive delivery, and pipeline monitoring across GitHub/GitLab.
---

# Master DevOps — Infrastructure, Delivery & Operations

DevOps is the discipline of making software delivery reliable and repeatable. Without it, every deployment is a gamble — dependent on whoever happens to be at the keyboard, whatever they remember about the process, and whatever state the server happens to be in.

This skill encodes the reasoning behind DevOps practices, not just the commands. Every section explains when to use a technique, when NOT to use it, and what goes wrong when you pick the wrong one. The goal: make the right delivery choice the obvious one, and make the wrong choice visibly wrong before it hits production.

---

## 1. CI/CD Pipelines

Continuous Integration catches breakage early. Continuous Delivery makes shipping a non-event. Together they turn "deploy day" from a ritual into a button press.

### Design Principles
- **Fail fast**: linting → unit tests → integration tests → e2e (cheapest first)
- **Cache dependencies** between runs — avoid redundant installs
- **Pin action/image versions with SHA**, not mutable tags
- **Secrets in environment variables**, masked in CI output — never in code or logs
- **Parallel jobs** for independent steps (test, lint, build simultaneously)
- **Build once, promote through stages** — same artifact to dev → staging → prod
- **Ignoring flaky tests erodes CI trust** — fix or delete them

**When to use CI/CD:** Always. Every project with more than one contributor or more than one deployment needs automated pipelines. Solo projects benefit too — CI catches the mistakes you make at 11pm.

**When NOT to automate deployment:** When you don't yet understand the deployment. If you've never deployed the service manually and successfully, don't automate what you don't understand. Do it manually once, document it, then automate.

### GitHub Actions
```bash
gh run list                                    # Recent workflow runs
gh run list --branch $(git branch --show-current) --limit 1  # Latest for current branch
gh run watch                                   # Watch run in real-time
gh run view <run-id> --log-failed              # Failed job logs
gh run rerun <run-id> --failed                 # Rerun only failed jobs
```

### GitLab CI
```bash
glab ci status              # Pipeline status (current branch)
glab ci view                # Interactive pipeline view
glab ci list                # Recent pipelines
glab ci status --live       # Watch pipeline live
glab ci trace <job-id>      # Stream job logs
```

### Auto-Push + Pipeline Watch (Git Alias)
```ini
# ~/.gitconfig
[alias]
    pushflow = "!f() { \
        git push \"${1:-origin}\" \"${2:-$(git branch --show-current)}\"; \
        url=$(git remote get-url \"${1:-origin}\"); \
        if echo \"$url\" | grep -q 'github.com'; then \
            sleep 3 && gh run watch; \
        elif echo \"$url\" | grep -q 'gitlab'; then \
            sleep 3 && glab ci status --live; \
        fi; \
    }; f"
```

---

## 2. Deployment Strategies

Choosing the wrong deployment strategy is how you turn a minor bug into a company-wide outage. The right choice depends on your risk tolerance, rollback requirements, and team size.

| Strategy | How | Best For | Rollback Speed |
|---|---|---|---|
| **Blue-Green** | Run new alongside old, switch traffic atomically | Zero-downtime requirements, instant rollback | Instant (switch back) |
| **Canary** | Route % of traffic to new, observe, promote | Catching issues before full blast radius | Fast (route back to old) |
| **Rolling** | Update instances incrementally | Large fleets, balanced speed/risk | Medium (finish rollout of old) |
| **Feature Flags** | Deploy dark, enable via flag | Decoupling deploy from release | Instant (toggle flag) |
| **Recreate** | Stop old, start new | Dev/staging, stateful apps that can't run two versions | Slow (redeploy old) |

**When NOT to use canary:** When you don't have automated analysis. A canary deployment without automated metric comparison is just a slower rollout — you're not actually catching anything, you're just hoping someone is watching the dashboard.

**When NOT to use blue-green:** When you can't afford double the infrastructure cost. Blue-green requires running two full environments simultaneously.

### Deployment Strategy Decision Framework

```
Is downtime acceptable?
├── Yes → Recreate (simplest)
└── No
    ├── Need instant rollback?
    │   ├── Yes → Blue-Green
    │   └── No
    │       ├── Have automated metric analysis?
    │       │   ├── Yes → Canary
    │       │   └── No → Rolling
    │       └── Want to separate deploy from release?
    │           └── Feature Flags (combine with any above)
    └── Team size < 3?
        └── Keep it simple: Blue-Green or Rolling
```

**Always have a rollback plan before deploying.** Know exactly how to revert. If you can't explain the rollback in one sentence, you're not ready to deploy.

---

## 3. Infrastructure as Code (IaC)

Infrastructure that exists only in someone's head, or worse, only in a running server's current state, is infrastructure that will be lost. IaC makes infrastructure reproducible, reviewable, and recoverable.

### Principles
- **Version control all infrastructure** — Terraform, Pulumi, OpenTofu, CloudFormation in git
- **Never apply without plan/diff review** — `terraform plan` before `apply`, always
- **State files contain secrets** — store remotely with encryption (S3+DynamoDB, GCS, Terraform Cloud), never in git
- **Modules for reuse** — don't copy-paste infrastructure definitions
- **Separate environments** with workspaces, directories, or accounts — dev changes must not affect prod

**When to use IaC:** Any infrastructure you'd be sad to lose. If recreating it from the console would take more than 10 minutes, codify it.

**When NOT to use IaC:** Throwaway experiments. If you're testing whether a service works at all, clicking through the console is fine. Codify it once you decide to keep it.

### Tools Landscape

| Tool | Language | State | Best For |
|---|---|---|---|
| **Terraform** | HCL | Remote backend | Multi-cloud, huge ecosystem |
| **OpenTofu** | HCL | Remote backend | Terraform without licensing concerns |
| **Pulumi** | TS/Python/Go/C# | Pulumi Cloud or self-managed | Teams that hate HCL, need testing |
| **CDK/CDKTF** | TS/Python/etc | CloudFormation/Terraform | AWS-native shops |

### Infrastructure Testing
- **Validate**: `terraform validate`, `pulumi preview`
- **Lint**: `tflint`, `checkov`, `tfsec` for security scanning
- **Integration tests**: Terratest (Go), Pulumi test framework
- **Policy as Code**: OPA/Rego, Sentinel, Kyverno

### Incremental Generation Pattern
Build one component at a time to prevent context overload:
1. Networking (VPC, subnets, security groups)
2. Compute (instances, ASGs, functions)
3. Database (RDS, managed DBs)
4. Monitoring (CloudWatch, Datadog, Prometheus)

---

## 4. Containers & Orchestration

Containers make the "works on my machine" problem solvable. Orchestration makes running containers at scale survivable.

### Container Best Practices
- **One process per container** — containers are not VMs
- **Health checks are mandatory** — orchestrators need them for routing and restarts
- **Don't run as root** — use non-root `USER` in Dockerfile
- **Immutable images**: config via environment variables, not baked in
- **Tag images with git SHA**, not just `latest` — know exactly what's deployed
- **Multi-stage builds** to minimize image size and attack surface

**When to containerize:** Services going to production. Anything that needs reproducible environments. Anything with complex dependencies.

**When NOT to containerize:** Simple scripts, CLI tools used locally, projects where the overhead of Docker exceeds the benefit. A Python script that runs fine with `python script.py` doesn't need a container.

### Kubernetes

Use Kubernetes when you have multiple services that need orchestration, auto-scaling, and self-healing. Do NOT use Kubernetes for a single service on a single server — that's a mass driver to kill a mosquito.

- Use **namespaces** for environment/team isolation
- **Resource requests & limits** on every pod — prevent noisy neighbors
- **Pod Disruption Budgets** for availability during upgrades
- **NetworkPolicies** for pod-to-pod traffic control (default deny)
- **Operators** for managing stateful/complex applications (database operators, cert-manager)

### GitOps (ArgoCD / Flux)

Git is the single source of truth for desired cluster state. The controller reconciles reality to match git. **Never `kubectl apply` manually in prod** — all changes through git.

- **ArgoCD**: web UI, multi-cluster, app-of-apps pattern, ApplicationSets
- **Flux**: lightweight, native Kustomize/Helm support, image automation

**When to use GitOps:** Teams with multiple services in Kubernetes. When you need audit trails for every change. When you want to stop SSHing into clusters.

**When NOT to use GitOps:** Single-service deployments. Teams that don't use Kubernetes. Adding GitOps to a simple `docker-compose up` setup is overengineering.

---

## 5. Security

Security is not a phase — it's a property of every phase. Build security into the pipeline, don't bolt it on at the end.

### Container & Supply Chain Security
- **Scan images** for vulnerabilities (Trivy, Grype, Snyk)
- **Sign images** with Sigstore/Cosign — verify provenance
- **SLSA framework** for supply chain integrity (provenance attestations)
- **SBOM generation** (Syft, `docker sbom`) for dependency transparency
- **Distroless/minimal base images** — fewer packages = smaller attack surface
- **Read-only root filesystem** in production containers

### Secrets Management
- **Never store secrets in git** — use Vault, Sealed Secrets, External Secrets Operator, or CI secret storage
- **Rotate secrets regularly** — automation makes rotation painless
- **Different secrets per environment** — dev leak shouldn't compromise prod
- **Audit secret access** — know who accessed what and when
- **Secrets in memory, not disk** when possible — temp files persist longer than expected

### Network Security
- Internal services don't need public IPs — use private subnets
- **TLS everywhere**, including internal traffic — zero trust
- **DNS for service discovery** — hardcoded IPs break when things move
- **Firewall default deny** — explicitly allow what's needed

---

## 6. Monitoring, Observability & Reliability

A service without monitoring is a service you hope is working. Hope is not a strategy.

### The Three Pillars

| Pillar | Tools | What It Tells You |
|---|---|---|
| **Metrics** | Prometheus, Datadog, CloudWatch | How the system is performing (latency, traffic, errors, saturation) |
| **Logs** | ELK, Loki, Datadog | What happened and why |
| **Traces** | OpenTelemetry, Jaeger, Zipkin | How a request flowed across services |

**When to add each:**
- **Metrics:** Day one. Non-negotiable. At minimum: request rate, error rate, latency p50/p95/p99.
- **Logs:** Day one. Structured JSON. Ship to a central platform.
- **Traces:** When you have more than two services talking to each other. Before that, logs are sufficient.

### Alerting
- **Alert on symptoms, not causes** — "users seeing errors" not "CPU high"
- **Every alert must be actionable** — if you can't act on it, it's noise
- **Dashboard per service** with key metrics — one glance shows health

### Reliability Engineering
- **Define SLOs** before building alerting — what does "healthy" mean?
- **Error budgets**: 99.9% = ~8h downtime/year is acceptable
- **Chaos engineering** in staging — break things intentionally (Litmus, Chaos Monkey)
- **Runbooks for common incidents** — 3am is not the time to figure out recovery
- **Blameless post-mortems** — focus on systems, not people

---

## 7. Platform Engineering

### Internal Developer Platform (IDP)

**When to invest in platform engineering:** When you have 5+ teams deploying independently. When the same infrastructure questions get asked every week. When onboarding a new service takes more than a day.

**When NOT to:** Teams under 20 engineers. The platform itself becomes a product that needs maintaining — don't create overhead you can't sustain.

- Self-service infrastructure provisioning (Backstage, Port, Humanitec)
- Golden paths: opinionated defaults that make the right thing easy
- Service catalogs with ownership, documentation, and dependencies
- Standardized templates for new services

### Developer Experience
- **Local dev parity**: Docker Compose, Tilt, Skaffold, DevContainers
- **Preview environments** per PR (Vercel, Argo CD pull request generator)
- **Self-service CI/CD**: teams own their pipelines, platform provides building blocks

---

## 8. Anti-Patterns

### The YAML Engineer

**Pattern:** Copy-pasting CI/CD configs from Stack Overflow or other projects without understanding what each step does. Adding steps "just in case." 200-line pipeline configs where nobody knows which steps are critical.

**Reality:** When the pipeline breaks, nobody can debug it because nobody understands it. Steps get added but never removed. The pipeline takes 45 minutes because half the steps are redundant.

**Fix:** Every pipeline step must have an owner who can explain why it exists. Review pipelines quarterly — delete steps nobody can justify. Start minimal and add steps only when a real problem demands them.

### The Snowflake Server

**Pattern:** SSHing into production to apply hotfixes, install packages, or tweak configs. "Just this once" becomes the norm.

**Reality:** The server's actual state diverges from what's in version control. Nobody knows what's running. When the server dies, you can't recreate it because the knowledge died with it.

**Fix:** All changes through code. If you SSH into prod to fix something, your first action after the incident is codifying that fix in IaC/config management and redeploying cleanly.

### The Monitoring Desert

**Pattern:** Service is deployed, runs for months, nobody looks at metrics because there are no metrics. "It's fine — nobody's complained."

**Reality:** Users are complaining, just not to you. Or the service is silently degraded. Or it's consuming 10x the resources it should. You won't know until the bill arrives or the outage happens.

**Fix:** No service goes to production without: (1) health check endpoint, (2) request rate + error rate + latency metrics, (3) at least one alert on error rate. This is L1 maturity — the absolute minimum.

### The Canary That Never Sings

**Pattern:** Running canary deployments but never automating the analysis. Someone is "supposed to watch the dashboard" during rollout.

**Reality:** The person watching gets distracted, or the metrics are ambiguous, or it's 3am and nobody's watching at all. The canary catches nothing because nobody's listening.

**Fix:** Automated canary analysis (Flagger, Argo Rollouts with analysis templates, Kayenta). Define success criteria upfront: error rate < 1%, p99 latency < 500ms. The system promotes or rolls back without human intervention.

---

## 9. Production Readiness

A meta-checklist that orchestrates all DevOps concerns into a single go/no-go assessment. Use before first deploy, major releases, quarterly reviews, or after incidents.

### When to Run

| Trigger | Context |
|---------|---------|
| Before first deploy | New service going to production |
| Before major release | Significant feature or architecture change |
| Quarterly review | Scheduled audit of existing services |
| After incident | Post-incident hardening |
| Dependency upgrade | Major framework or runtime change |
| Team handoff | Transferring service ownership |

### Production Readiness Checklist

**Health & Lifecycle**
- [ ] Health check endpoint (`/healthz`) returns dependency status
- [ ] Readiness probe distinguishes "starting" from "ready"
- [ ] Liveness probe detects deadlocks and unrecoverable states
- [ ] Graceful shutdown drains in-flight requests
- [ ] Startup probe allows slow initialization

**Resilience**
- [ ] Circuit breakers on all external service calls
- [ ] Retry with exponential backoff + jitter on transient failures
- [ ] Rate limiting per endpoint and per client
- [ ] Timeouts on every outbound call (HTTP, DB, queue)
- [ ] Bulkhead isolation for critical vs non-critical paths

**Configuration & Secrets**
- [ ] All config externalized (env vars, config service, feature flags)
- [ ] No secrets in code, images, or env var defaults
- [ ] Secrets from vault (AWS SM, HashiCorp Vault)
- [ ] Config changes don't require redeployment

**Data Safety**
- [ ] Backup strategy defined and tested (RPO/RTO documented)
- [ ] Restore verified in non-production
- [ ] DB migrations backward-compatible and reversible
- [ ] Data retention policies enforced

**Operational Readiness**
- [ ] Runbooks for top 5 failure scenarios
- [ ] SLOs defined (availability, latency, error rate) with error budgets
- [ ] On-call rotation staffed, escalation path documented
- [ ] Dashboards show golden signals (latency, traffic, errors, saturation)
- [ ] Alerting rules with appropriate thresholds and severity

### Maturity Levels

| Level | Name | Key Requirements |
|-------|------|-----------------|
| **L1** | MVP | Health check, basic logging, error handling, manual deploy, unit tests |
| **L2** | Stable | Structured logging, metrics, graceful shutdown, CI/CD, runbooks |
| **L3** | Resilient | Distributed tracing, circuit breakers, auto-scaling, SLOs, on-call |
| **L4** | Optimized | Canary deploys, predictive alerting, error budgets, chaos testing |

### Using Maturity Levels Progressively

Do not try to reach L4 on day one. That path leads to over-engineering and paralysis.

**L1 is the launch bar.** Every service must meet L1 before going to production. This takes hours, not days. If you can't meet L1, you're not ready to ship.

**L2 is the "we're serious" bar.** Reach L2 within the first month of production. This is where you stop firefighting and start operating.

**L3 is for services that matter.** Revenue-critical, user-facing, high-traffic. Not every internal tool needs distributed tracing and auto-scaling.

**L4 is aspirational.** Few services need it. Pursue L4 when your error budget is consistently tight or when the cost of an outage justifies the investment.

**Assessment approach:** Score each checklist item as Met / Partial / Missing. A service's maturity level is the highest level where ALL items are Met. Partial doesn't count — L2 with a missing item is L1.

### Incident Response

| Severity | Response | Escalation | Notify |
|----------|----------|------------|--------|
| SEV-1 (outage) | 15 min | 30 min | Exec + customers |
| SEV-2 (degraded) | 30 min | 1 hour | Eng lead |
| SEV-3 (minor) | 4 hours | Next biz day | Standup |
| SEV-4 (cosmetic) | Next sprint | N/A | Backlog |

### NEVER Do
1. Skip health checks — every service needs them
2. Store secrets in code or images
3. Deploy without a rollback plan (< 5 min rollback or don't ship)
4. Ignore error budget violations — freeze features, fix reliability
5. Go to production without runbooks

---

## Cross-Skill Integration

### Safety Gate
- **Before infra changes**: `guardrails.py check --action infra_change --target {resource}` (T3-T4)
- **Before production deployments**: `guardrails.py check --action deploy_production` (T4)

### Memory Protocol
- **After deployment**: `memory.py remember "[devops] Deployed {service} to {env}: {version}"`
- **After incident**: `memory.py remember "[devops] Incident {id}: {summary}, resolution={action}" --importance 0.9`

### Connected Skills
- **security** → pre-deploy security gates, container scanning results
- **observability** → post-deploy monitoring, SLO validation
- **cloudflare-deploy** → CF Pages deployment execution
- **web-builder** → build artifacts for deployment
- **python-backend** → Dockerfile generation, CI/CD pipeline setup

---

## Quick Reference Card

```
# CI/CD
gh run watch                    # Watch GitHub Actions
gh run view <id> --log-failed   # Debug failures
gh run rerun <id> --failed      # Retry failed jobs
git pushflow                    # Push + watch pipeline

# IaC
terraform plan                  # Always before apply
terraform validate              # Syntax check
tflint / checkov / tfsec        # Lint + security scan

# Containers
docker build --tag app:$(git rev-parse --short HEAD) .
# Always: non-root USER, health check, multi-stage build

# K8s
kubectl get pods -n <ns>        # Pod status
kubectl logs -f <pod>           # Stream logs
kubectl rollout undo deployment/<name>  # Rollback
```

| Decision | Answer |
|---|---|
| Need instant rollback? | Blue-Green |
| Want to test on real traffic? | Canary (with automated analysis) |
| Simple, low-risk? | Rolling |
| Decouple deploy from release? | Feature Flags |
| First deploy ever? | Meet L1 checklist first |
| Service critical? | Target L3 maturity |

| NEVER | ALWAYS |
|---|---|
| SSH hotfixes to prod | Changes through code |
| `latest` image tags | Git SHA tags |
| Secrets in git | Vault / CI secrets |
| Deploy without rollback plan | Know how to revert in < 5 min |
| Alert on causes | Alert on symptoms |
