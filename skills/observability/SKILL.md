---
name: master-observability
version: 2.0.0
description: Complete observability engineering — OpenTelemetry-first instrumentation, structured logging, distributed tracing, metrics (RED/USE/Four Golden Signals), Prometheus/Grafana/Loki/Tempo stack, SLIs/SLOs/error budgets, alert design, dashboard patterns, and cost-aware operations.
---

# Master Observability

## Why This Exists

You cannot fix what you cannot see. Observability is the difference between "the site is slow" and "the payment service P99 latency spiked to 2s at 14:03 due to a connection pool exhaustion on the orders database." Without it, debugging is guesswork. With it, you have a structured path from symptom to root cause.

Observability is not monitoring. Monitoring tells you *when* something is broken. Observability lets you ask *why* — including questions you didn't anticipate when you built the system.

---

## The Observability Maturity Model

Most teams are stuck at Level 1, think they're at Level 3, and need to be at Level 2 before attempting anything higher.

| Level | Name | What It Looks Like | Risk |
|-------|------|--------------------|------|
| **0** | Printf Debugging | `console.log("here")`, SSH into prod to tail logs, no persistent storage | You're flying blind. Every incident is a manual archaeology expedition. |
| **1** | Structured Logs | JSON logs shipped to a central store (Loki, CloudWatch). Searchable. | You can answer questions *after* you know what to search for. No trends, no flow visibility. |
| **2** | Metrics + Alerts | RED/USE metrics in Prometheus, Grafana dashboards, PagerDuty alerts. | You know *when* things break. You still can't trace *why* across service boundaries. |
| **3** | Distributed Traces | OpenTelemetry traces across all services, correlated with logs via `trace_id`. | You can follow a request end-to-end. But you're reactive — you find problems after users report them. |
| **4** | Correlated Observability with SLOs | All three pillars linked. SLIs/SLOs with error budgets drive release decisions. Alerts fire on customer impact, not infrastructure noise. | You're proactive. You know you're burning error budget before customers complain. |

**Where to start:** Get to Level 2 first. Structured logs + basic metrics + alerts on the golden signals. This alone eliminates 80% of debugging pain.

---

## What to Instrument First

Decision framework for teams starting from scratch or adding observability to an existing system:

```
Step 1: Golden Signals (do this first — covers 80% of incidents)
  ├─ Latency (request duration histogram)
  ├─ Traffic (requests per second)
  ├─ Errors (5xx rate, application error rate)
  └─ Saturation (CPU, memory, connection pools, queue depth)

Step 2: Business Metrics (do this when golden signals are stable)
  ├─ Orders placed / revenue per minute
  ├─ User signups / active sessions
  ├─ Payment success rate
  └─ Whatever your business cares about — if it's on a KPI dashboard, instrument it

Step 3: Distributed Traces (do this when you have >2 services)
  ├─ Auto-instrument with OTel SDK
  ├─ Add custom spans for business-critical paths
  ├─ Tail-sample errors at 100%, everything else at 1-10%
  └─ Link traces to logs via trace_id

Step 4: SLOs and Error Budgets (do this when you're mature enough to act on them)
  ├─ Define SLIs from golden signals
  ├─ Set SLO targets based on actual baseline (not wishful thinking)
  ├─ Multi-window burn-rate alerts
  └─ Error budget gates release decisions
```

---

## Anti-Patterns

### The Log Tsunami

**Pattern:** Every function logs at DEBUG. Request bodies, response bodies, intermediate state — all of it, in production.

**Reality:** Log volume hits 50GB/day. Storage costs explode. Searching for the one error log takes minutes because it's buried in millions of debug lines. The signal-to-noise ratio approaches zero.

**Fix:** Production default = INFO. Log business events (order placed, payment failed, user authenticated), not data flow (entering function, exiting function). Make log level configurable at runtime so you can temporarily enable DEBUG for a specific service without redeploying.

### The Dashboard Museum

**Pattern:** Team creates a Grafana dashboard for every new feature. 47 dashboards exist. Nobody looks at any of them.

**Reality:** Dashboards without viewers are maintenance debt. They break silently when metric names change. During incidents, nobody knows which dashboard matters.

**Fix:** Maintain exactly these dashboards: War Room (overview), one per service, infrastructure, database, SLO. Delete everything else. If nobody opened a dashboard in 30 days, it shouldn't exist.

### The Alert Storm

**Pattern:** Every metric gets an alert. CPU > 70%? Alert. Memory > 60%? Alert. Pod restarted? Alert. Response time > 200ms? Alert.

**Reality:** On-call gets 40 alerts per day. They start ignoring all of them. When a real outage happens, the critical alert is buried in noise. Alert fatigue is the #1 cause of slow incident response.

**Fix:** Alert on symptoms, not causes. "Error rate > 5% for 5 minutes" is actionable. "CPU at 80%" is not (maybe that's normal). Every alert must have a runbook link. Review alerts monthly — if it never fires, delete it; if it always fires, raise the threshold or fix the underlying issue.

### The Metric Without Context

**Pattern:** Dashboard shows CPU at 80%. Team panics.

**Reality:** Is 80% bad? If the baseline is 75%, this is noise. If the baseline is 30%, this is a crisis. A metric without a baseline is a number without meaning.

**Fix:** Always display metrics with baselines. Use Grafana annotations to mark deployments and incidents. Show percentile trends (p50/p95/p99), not averages — averages hide outliers that kill user experience.

### The Trace Gap

**Pattern:** Tracing is set up for the API gateway and the main service. Traces stop at the database call or the message queue consumer.

**Reality:** The bottleneck is always in the part you didn't trace. The database query that takes 3 seconds, the Kafka consumer that's lagging — invisible because context propagation wasn't carried across the boundary.

**Fix:** Propagate trace context everywhere: HTTP headers, gRPC metadata, message queue payloads, background job arguments. Auto-instrument database clients and queue consumers with OTel. If a span has no children but represents a call to another system, you have a trace gap.

---

## 1 · Three Pillars + Correlation

| Pillar | Purpose | Question It Answers | Example |
|--------|---------|---------------------|---------|
| **Logs** | What happened | Why did this request fail? | `{"level":"error","msg":"payment declined","user_id":"u_82","trace_id":"abc"}` |
| **Metrics** | How much / how fast | Is latency increasing? | `http_request_duration_seconds{route="/api/orders"} 0.342` |
| **Traces** | Request flow | Where is the bottleneck? | `api-gateway → auth → order-service → db` |

**Correlation is the multiplier.** Each pillar alone gives partial visibility. Connected, they give root-cause analysis in minutes instead of hours:

- Embed `trace_id` in every log line → jump from log to full trace
- Add exemplars to metrics → jump from a latency spike to the specific trace that caused it
- Tag spans with the same correlation IDs as logs → unified search across pillars

Without correlation, you have three separate data stores. With it, you have observability.

---

## 2 · Structured Logging

Always emit logs as **structured JSON** — never free-text strings. Unstructured logs cannot be queried, aggregated, or alerted on. They're write-only data.

### 2.1 Required Fields

| Field | Purpose | Required |
|-------|---------|----------|
| `timestamp` | ISO-8601 with milliseconds | Always |
| `level` | Severity (DEBUG … FATAL) | Always |
| `service` | Originating service name | Always |
| `message` | Human-readable description | Always |
| `trace_id` | Distributed trace correlation | Always |
| `span_id` | Current span within trace | Always |
| `correlation_id` | Business-level correlation (order ID) | When applicable |
| `error` | Structured error object | On errors |
| `context` | Request-specific metadata | Recommended |

### 2.2 Context Enrichment (Middleware Pattern)

```typescript
app.use((req, res, next) => {
  const ctx = {
    trace_id: req.headers['x-trace-id'] || crypto.randomUUID(),
    request_id: crypto.randomUUID(),
    user_id: req.user?.id,
    method: req.method,
    path: req.path,
  };
  asyncLocalStorage.run(ctx, () => next());
});
```

### 2.3 Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| **FATAL** | App cannot continue, process exits | Database connection pool exhausted |
| **ERROR** | Operation failed, needs attention | Payment charge failed: CARD_DECLINED |
| **WARN** | Unexpected but recoverable | Retry 2/3 for upstream timeout |
| **INFO** | Normal business events | Order ORD-1234 placed successfully |
| **DEBUG** | Developer troubleshooting | Cache miss for key user:82:preferences |
| **TRACE** | Very fine-grained (rarely in prod) | Entering validateAddress with payload |

**Rules:** Production default = INFO+. Every ERROR should be actionable. Every FATAL must trigger an alert. If you're logging at DEBUG in production "just in case," you're in The Log Tsunami.

### 2.4 Logger Recommendations

| Library | Language | Strengths |
|---------|----------|-----------|
| **Pino** | Node.js | Fastest Node logger, low overhead |
| **structlog** | Python | Composable processors, context binding |
| **zerolog** | Go | Zero-allocation JSON logging |
| **zap** | Go | High performance, typed fields |
| **tracing** | Rust | Spans + events, async-aware |

---

## 3 · Distributed Tracing

### 3.1 Trace Anatomy

```
Trace (trace_id: abc123)
  └─ Span: frontend [100ms]
      └─ Span: api-gateway [80ms]
          ├─ Span: auth-service [10ms]
          └─ Span: user-service [60ms]
              └─ Span: database [40ms]
```

**Key concepts:** Trace = end-to-end request journey · Span = single operation · Context = propagated metadata · Tags/Attributes = key-value pairs for filtering · Events = timestamped milestones within a span.

### 3.2 OpenTelemetry Setup (Always Prefer OTel)

#### Node.js

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

const sdk = new NodeSDK({
  serviceName: 'order-service',
  traceExporter: new OTLPTraceExporter({
    url: 'http://otel-collector:4318/v1/traces',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});
sdk.start();
```

#### Python (Flask)

```python
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

resource = Resource(attributes={SERVICE_NAME: "my-service"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
```

#### Go

```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    "go.opentelemetry.io/otel/sdk/resource"
    semconv "go.opentelemetry.io/otel/semconv/v1.4.0"
)

func initTracer() (*sdktrace.TracerProvider, error) {
    exporter, err := otlptracehttp.New(context.Background())
    if err != nil { return nil, err }
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceNameKey.String("my-service"),
        )),
    )
    otel.SetTracerProvider(tp)
    return tp, nil
}
```

### 3.3 Span Creation Best Practice

```typescript
const tracer = trace.getTracer('order-service');

async function processOrder(order: Order) {
  return tracer.startActiveSpan('processOrder', async (span) => {
    try {
      span.setAttribute('order.id', order.id);
      span.setAttribute('order.total_cents', order.totalCents);
      await validateInventory(order);
      await chargePayment(order);
      span.setStatus({ code: SpanStatusCode.OK });
    } catch (err) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: err.message });
      span.recordException(err);
      throw err;
    } finally {
      span.end();
    }
  });
}
```

### 3.4 Context Propagation

- **Standard:** W3C Trace Context (`traceparent` / `tracestate` headers) — default in OTel
- Propagate across HTTP, gRPC, and message queues
- For async workers: serialise `traceparent` into the job payload
- For correlated logs:

```python
span = trace.get_current_span()
trace_id = format(span.get_span_context().trace_id, '032x')
logger.info("Processing request", extra={"trace_id": trace_id})
```

### 3.5 Sampling Strategies

| Strategy | Use When | Config Example |
|----------|----------|----------------|
| **Always On** | Low-traffic services, debugging | `sampler: always_on` |
| **Probabilistic** (N%) | General production | `param: 0.01` (1%) |
| **Rate-limited** (N/sec) | High-throughput services | `param: 100` |
| **Tail-based** | Need all error/slow traces | OTel Collector tail_sampling processor |
| **Adaptive** | Dynamic load | `ParentBased(TraceIdRatioBased(0.01))` |

**Rule:** Always sample 100% of error traces regardless of strategy.

---

## 4 · Metrics

### 4.1 RED Method (Request-Driven — for Services)

| Metric | Measures | PromQL |
|--------|----------|--------|
| **Rate** | Requests/sec | `sum(rate(http_requests_total[5m])) by (service)` |
| **Errors** | Error ratio | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` |
| **Duration** | Latency | `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))` |

### 4.2 USE Method (Resource-Driven — for Infrastructure)

| Metric | Measures | Example |
|--------|----------|---------|
| **Utilization** | % resource busy | CPU at 78% |
| **Saturation** | Work queued | 12 requests in thread pool queue |
| **Errors** | Resource errors | 3 disk I/O errors/min |

### 4.3 Four Golden Signals (Google SRE)

Latency · Traffic · Errors · Saturation — superset of RED that adds saturation for backend services.

### 4.4 SLIs, SLOs, SLAs & Error Budgets

| Concept | Definition | Example |
|---------|-----------|---------|
| **SLI** | Measured indicator | % requests < 300ms |
| **SLO** | Target for the SLI | 99.9% of requests < 300ms over 30 days |
| **SLA** | Contractual commitment | 99.5% availability or credits issued |
| **Error Budget** | 100% − SLO | 0.1% = ~43 min/month of allowed downtime |

**Multi-window, multi-burn-rate alerts** catch both sudden spikes and slow burns against SLOs. This is the gold standard for alerting — it replaces static thresholds with alerts that fire based on how fast you're consuming your error budget.

---

## 5 · Monitoring Stack

| Tool | Role | Notes |
|------|------|-------|
| **OpenTelemetry Collector** | Unified telemetry pipeline | Vendor-neutral; receives, processes, exports |
| **Prometheus** | Metrics store + alerting rules | Pull-based; use recording rules for perf |
| **Grafana** | Visualisation | Dashboards for metrics, logs, traces |
| **Loki** | Log aggregation | Label-indexed; pairs with Grafana |
| **Tempo** | Trace backend | S3-backed, integrates with Grafana |
| **Jaeger** | Trace visualisation (alternative) | Good standalone; Tempo preferred in Grafana stack |

**Recommended architecture:** Apps → OTel SDK → OTel Collector → Prometheus (metrics) + Loki (logs) + Tempo (traces) → Grafana.

### 5.1 Tempo Configuration

```yaml
server:
  http_listen_port: 3200
distributor:
  receivers:
    otlp:
      protocols:
        http:
        grpc:
storage:
  trace:
    backend: s3
    s3:
      bucket: tempo-traces
      endpoint: s3.amazonaws.com
```

### 5.2 Jaeger Quick Start (Docker Compose)

```yaml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "14268:14268"  # Collector HTTP
      - "4317:4317"    # OTel gRPC
      - "4318:4318"    # OTel HTTP
```

---

## 6 · Grafana Dashboards

### 6.1 Design Principles

```
┌──────────────────────────────────┐
│ Critical Metrics (Big Numbers)   │  ← Stat panels: error rate, uptime, active alerts
├──────────────────────────────────┤
│ Key Trends (Time Series)         │  ← Rate, latency percentiles, throughput
├──────────────────────────────────┤
│ Detailed Metrics (Tables/Heatmaps│  ← Top errors, slow queries, heatmaps
└──────────────────────────────────┘
```

### 6.2 Standard Dashboard Set

Keep exactly these. Delete the rest.

| Dashboard | Key Panels |
|-----------|------------|
| **War Room (Overview)** | Total RPS, global error rate %, p50/p95/p99 latency, active alerts by severity, deployment markers |
| **Service (per-service)** | RED metrics per endpoint, dependency health, resource utilisation, top errors table |
| **Infrastructure** | CPU/memory/disk/network per node, pod count by namespace, node status |
| **Database** | QPS, connection pool, query latency percentiles, replication lag, slow queries |
| **SLO** | Error budget remaining, burn rate, SLI trends over 30-day window |

### 6.3 Dashboard Variables

```json
{
  "templating": {
    "list": [
      {
        "name": "namespace",
        "type": "query",
        "query": "label_values(kube_pod_info, namespace)"
      },
      {
        "name": "service",
        "type": "query",
        "query": "label_values(kube_service_info{namespace=\"$namespace\"}, service)",
        "multi": true
      }
    ]
  }
}
```

### 6.4 Key Panel Examples

**Request Rate (time series):**
```json
{ "expr": "sum(rate(http_requests_total{namespace=\"$namespace\", service=~\"$service\"}[5m])) by (service)" }
```

**Error Rate % with alert:**
```json
{ "expr": "(sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))) * 100" }
```

**P95 Latency:**
```json
{ "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))" }
```

**Latency Heatmap:**
```json
{ "type": "heatmap", "expr": "sum(rate(http_request_duration_seconds_bucket[5m])) by (le)", "format": "heatmap" }
```

### 6.5 Dashboard as Code

**Provisioning (dashboards.yml):**
```yaml
apiVersion: 1
providers:
  - name: default
    type: file
    options:
      path: /etc/grafana/dashboards
```

**Terraform:**
```hcl
resource "grafana_dashboard" "api_monitoring" {
  config_json = file("${path.module}/dashboards/api-monitoring.json")
  folder      = grafana_folder.monitoring.id
}
```

---

## 7 · Alert Design

### 7.1 Severity Levels

| Severity | Response Time | Example |
|----------|---------------|---------|
| **P1** | Immediate (page) | Service fully down, data loss |
| **P2** | < 30 min | Error rate > 5%, p99 > 5s |
| **P3** | Business hours | Disk > 80%, cert expiring 7d |
| **P4** | Best effort | Non-critical deprecation |

### 7.2 Alert Fatigue Prevention

1. **Alert on symptoms, not causes** — "error rate > 5%" not "pod restarted"
2. **Multi-window, multi-burn-rate** — catch spikes and slow burns
3. **Every alert must have a runbook link** — unactionable alerts erode trust
4. **Review monthly** — delete/tune alerts that never fire or always fire
5. **Group related alerts** — use inhibition rules to suppress child alerts
6. **Appropriate thresholds** — if ignored daily, raise threshold or delete

### 7.3 Grafana Alert Example

```json
{
  "alert": {
    "name": "High Error Rate",
    "for": "5m",
    "conditions": [{
      "evaluator": {"type": "gt", "params": [5]},
      "query": {"params": ["A", "5m", "now"]},
      "reducer": {"type": "avg"}
    }],
    "notifications": [{"uid": "slack-channel"}]
  }
}
```

---

## 8 · Advanced Topics

### 8.1 eBPF-Based Observability

Kernel-level instrumentation without code changes. Tools: **Pixie**, **Cilium Hubble**, **bpftrace**. Ideal for network-level tracing and when you can't modify application code.

### 8.2 Continuous Profiling

Always-on, low-overhead CPU/memory profiling in production. Tools: **Pyroscope**, **Grafana Phlare**, **Parca**. Links profiles to traces for precise root-cause analysis.

### 8.3 Cost-Aware Observability

Observability has a cost curve that goes exponential if you're not deliberate:

- **Log volume budgets** — alert when a service exceeds daily quota
- **Metric cardinality limits** — never use user ID or request ID as label (Prometheus OOM)
- **Trace sampling** — sample 1-10% in production; tail-sample errors at 100%
- **Retention tiers** — hot (7d full resolution) → warm (30d downsampled) → cold (archival)
- **Drop unused metrics** — OTel Collector filter processor

### 8.4 Runbook Automation

Every alert should link to a runbook. Mature teams automate runbooks via **Rundeck**, **PagerDuty Process Automation**, or custom operators that auto-remediate known issues.

---

## 9 · Observability Checklist

Every service must have:

- [ ] Structured JSON logging with consistent schema
- [ ] trace_id / span_id propagated on all requests (including async)
- [ ] RED metrics exposed for every external endpoint
- [ ] Health check endpoints (`/healthz` and `/readyz`)
- [ ] Distributed tracing with OpenTelemetry
- [ ] Dashboards for RED metrics and resource utilisation
- [ ] Alerts with runbook links for error rate, latency, and saturation
- [ ] Log level configurable at runtime without redeployment
- [ ] PII scrubbing verified and tested
- [ ] Retention policies defined for logs, metrics, and traces
- [ ] SLIs/SLOs defined with error budget tracking

---

## NEVER Do

1. **NEVER log passwords, tokens, API keys, or secrets** — even at DEBUG
2. **NEVER use console.log / print in production** — use a structured logger
3. **NEVER use user IDs, emails, or request IDs as metric labels** — cardinality explosion
4. **NEVER create alerts without a runbook link**
5. **NEVER rely on logs alone** — you need all three pillars
6. **NEVER log request/response bodies by default** — opt-in only with PII redaction
7. **NEVER ignore log volume** — set budgets and alert on quota breach
8. **NEVER skip context propagation in async flows** — broken traces are worse than none

---

## Cross-Skill Integration

### Memory Protocol
- **After SLO breach**: `memory.py remember "[observability] SLO breach: {service} {sli} below target" --importance 0.9`
- **After dashboard created**: `memory.py remember "[observability] Dashboard: {name} for {service}"`

### Connected Skills
- **devops** → deployment events correlate with metric changes
- **security** → security events surface in observability pipeline
- **python-backend** → instrumentation patterns injected during development
- **data-analysis** → metric analysis and statistical anomaly detection

---

## Quick Reference Card

```
MATURITY        L0 printf → L1 structured logs → L2 metrics+alerts → L3 traces → L4 SLOs
INSTRUMENT      Golden signals first → business metrics → traces → SLOs
THREE PILLARS   Logs (what happened) + Metrics (how much) + Traces (where)
CORRELATION     trace_id in every log, exemplars in metrics, context in spans

RED             Rate · Errors · Duration (for services)
USE             Utilization · Saturation · Errors (for infrastructure)
GOLDEN SIGNALS  Latency · Traffic · Errors · Saturation

LOGGING         Structured JSON | INFO+ in prod | DEBUG configurable at runtime | Never log secrets
TRACING         OTel SDK → Collector → Tempo | W3C traceparent | 100% sample errors
METRICS         Prometheus scrape | No high-cardinality labels | Histograms for latency
ALERTS          Symptoms not causes | Runbook link required | Review monthly | Burn-rate for SLOs

STACK           OTel Collector → Prometheus + Loki + Tempo → Grafana
DASHBOARDS      War Room · Per-Service · Infra · DB · SLO — delete the rest
COST            Log budgets · Cardinality limits · Tail sampling · Retention tiers

ANTI-PATTERNS   Log Tsunami · Dashboard Museum · Alert Storm · Metric Without Context · Trace Gap
```
