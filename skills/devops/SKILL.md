---
name: Master DevOps
description: Complete DevOps toolkit — CI/CD pipelines, infrastructure as code, containers, Kubernetes, GitOps, security, monitoring, progressive delivery, and pipeline monitoring across GitHub/GitLab.
---

# Master DevOps — Infrastructure, Delivery & Operations

## 1. CI/CD Pipelines

### Design Principles
- **Fail fast**: linting → unit tests → integration tests → e2e (cheapest first)
- **Cache dependencies** between runs — avoid redundant installs
- **Pin action/image versions with SHA**, not mutable tags
- **Secrets in environment variables**, masked in CI output — never in code or logs
- **Parallel jobs** for independent steps (test, lint, build simultaneously)
- **Build once, promote through stages** — same artifact to dev → staging → prod
- **Ignoring flaky tests erodes CI trust** — fix or delete them

### GitHub Actions
```bash
# List recent workflow runs
gh run list

# Latest run for current branch
gh run list --branch $(git branch --show-current) --limit 1

# Watch run in real-time
gh run watch

# View run details / logs / failed logs
gh run view <run-id>
gh run view <run-id> --log
gh run view <run-id> --log-failed

# Rerun only failed jobs
gh run rerun <run-id> --failed
```

### GitLab CI
```bash
# Pipeline status (current branch)
glab ci status

# Interactive pipeline view
glab ci view

# List recent pipelines
glab ci list

# Watch pipeline live
glab ci status --live

# Stream job logs
glab ci trace <job-id>
```

### Auto-Push + Pipeline Watch (Git Alias)
Add to `~/.gitconfig`:
```ini
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
Usage: `git pushflow` or `git pushflow origin main`

---

## 2. Deployment Strategies

| Strategy | How | When |
|---|---|---|
| **Blue-Green** | Run new version alongside old, switch traffic atomically | Need instant rollback |
| **Canary** | Route % of traffic to new version, observe, then promote | Catch issues before full rollout |
| **Rolling** | Update instances incrementally | Balance speed vs risk |
| **Feature Flags** | Deploy code dark, enable via flag (LaunchDarkly, Unleash, Flagsmith) | Decouple deploy from release |

- **Always have a rollback plan** before deploying — know exactly how to revert
- **Progressive delivery**: combine canary + feature flags + automated analysis (Flagger, Argo Rollouts)

---

## 3. Infrastructure as Code (IaC)

### Principles
- **Version control all infrastructure** — Terraform, Pulumi, OpenTofu, CloudFormation in git
- **Never apply without plan/diff review** — `terraform plan` before `apply`, always
- **State files contain secrets** — store remotely with encryption (S3+DynamoDB, GCS, Terraform Cloud), never in git
- **Modules for reuse** — don't copy-paste infrastructure definitions
- **Separate environments** with workspaces, directories, or accounts — dev changes must not affect prod

### Tools Landscape
| Tool | Language | State | Notes |
|---|---|---|---|
| **Terraform** | HCL | Remote backend | Industry standard, huge provider ecosystem |
| **OpenTofu** | HCL | Remote backend | Open-source Terraform fork (CNCF) |
| **Pulumi** | TS/Python/Go/C# | Pulumi Cloud or self-managed | Real programming languages, testing built-in |
| **CDK/CDKTF** | TS/Python/etc | CloudFormation/Terraform | AWS-native or Terraform bridge |

### Infrastructure Testing
- **Validate**: `terraform validate`, `pulumi preview`
- **Lint**: `tflint`, `checkov`, `tfsec` for security scanning
- **Integration tests**: Terratest (Go), Pulumi test framework
- **Policy as Code**: OPA/Rego, Sentinel, Kyverno

### Incremental Generation Pattern
When generating IaC, build **one component at a time** to prevent context overload:
1. Networking (VPC, subnets, security groups)
2. Compute (instances, ASGs, functions)
3. Database (RDS, managed DBs)
4. Monitoring (CloudWatch, Datadog, Prometheus)

---

## 4. Containers & Orchestration

### Container Best Practices
- **One process per container** — containers are not VMs
- **Health checks are mandatory** — orchestrators need them for routing and restarts
- **Don't run as root** — use non-root `USER` in Dockerfile
- **Immutable images**: config via environment variables, not baked in
- **Tag images with git SHA**, not just `latest` — know exactly what's deployed
- **Multi-stage builds** to minimize image size and attack surface

### Kubernetes
- Use **namespaces** for environment/team isolation
- **Resource requests & limits** on every pod — prevent noisy neighbors
- **Pod Disruption Budgets** for availability during upgrades
- **NetworkPolicies** for pod-to-pod traffic control (default deny)
- **Operators** for managing stateful/complex applications (database operators, cert-manager)

### GitOps (ArgoCD / Flux)
- **Git is the single source of truth** for desired cluster state
- **Declarative**: define desired state in manifests, controller reconciles
- **ArgoCD**: web UI, multi-cluster, app-of-apps pattern, ApplicationSets
- **Flux**: lightweight, native Kustomize/Helm support, image automation
- **Never `kubectl apply` manually in prod** — all changes through git

---

## 5. Security

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
- **Load balancer health checks** separate from app health
- **Firewall default deny** — explicitly allow what's needed

---

## 6. Monitoring, Observability & Reliability

### The Three Pillars
- **Metrics**: Prometheus, Datadog, CloudWatch — the four golden signals: latency, traffic, errors, saturation
- **Logs**: structured JSON logs, shipped to central platform (ELK, Loki, Datadog)
- **Traces**: OpenTelemetry, Jaeger, Zipkin — follow requests across services

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
- Self-service infrastructure provisioning (Backstage, Port, Humanitec)
- Golden paths: opinionated defaults that make the right thing easy
- Service catalogs with ownership, documentation, and dependencies
- Standardized templates for new services (cookiecutter, Yeoman, Backstage scaffolder)

### Developer Experience
- **Local dev parity**: Docker Compose, Tilt, Skaffold, DevContainers
- **Preview environments** per PR (Vercel, Argo CD pull request generator)
- **Self-service CI/CD**: teams own their pipelines, platform provides building blocks

---

## 8. Common Anti-Patterns

| Anti-Pattern | Why It's Bad | Do This Instead |
|---|---|---|
| SSH into prod to fix things | Undocumented changes, drift | All changes through automation |
| No staging environment | "Works on my machine" ≠ prod | Mirror prod in staging |
| Manual deployment steps | Will be done wrong eventually | Automate everything |
| Monitoring only happy paths | Miss errors and edge cases | Monitor error rates, latency p99 |
| `latest` tags everywhere | Can't reproduce or rollback | Git SHA or semver tags |
| Shared long-lived branches | Merge hell, stale code | Trunk-based dev or short-lived branches |
| Secrets in `.env` files in git | Credential leaks | Vault, sealed secrets, CI secrets |

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
| **L1** MVP | Health check, basic logging, error handling, manual deploy, unit tests |
| **L2** Stable | Structured logging, metrics, graceful shutdown, CI/CD, runbooks |
| **L3** Resilient | Distributed tracing, circuit breakers, auto-scaling, SLOs, on-call |
| **L4** Optimized | Canary deploys, predictive alerting, error budgets, chaos testing |

### Incident Response

**Escalation Matrix**
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
