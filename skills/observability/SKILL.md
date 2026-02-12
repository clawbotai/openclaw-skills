---
name: master-observability
model: standard
description: >
  Complete observability engineering — OpenTelemetry-first instrumentation, structured logging,
  distributed tracing, metrics (RED/USE/Four Golden Signals), Prometheus/Grafana/Loki/Tempo stack,
  SLIs/SLOs/error budgets, alert design, dashboard patterns, and cost-aware operations.
  Use for any logging, monitoring, tracing, alerting, or dashboard work.
version: 2.0.0
---

# Master Observability

Everything needed to build, operate, and evolve observable systems — from a single service to planet-scale microservices.

---

## 1 · Three Pillars + Correlation

| Pillar | Purpose | Question It Answers | Example |
|--------|---------|---------------------|---------|
| **Logs** | What happened | Why did this request fail? | `{"level":"error","msg":"payment declined","user_id":"u_82","trace_id":"abc"}` |
| **Metrics** | How much / how fast | Is latency increasing? | `http_request_duration_seconds{route="/api/orders"} 0.342` |
| **Traces** | Request flow | Where is the bottleneck? | `api-gateway → auth → order-service → db` |

**Correlation is key:** Embed `trace_id` in every log line so you can jump from a log entry to the full distributed trace and from a trace span to matching log lines. Metrics link via exemplars.

---

## 2 · Structured Logging

Always emit logs as **structured JSON** — never free-text strings.

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

**Rules:** Production default = INFO+. Every ERROR should be actionable. Every FATAL must trigger an alert.

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

**Multi-window, multi-burn-rate alerts** catch both sudden spikes and slow burns against SLOs.

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

## 10 · Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Logging PII/secrets | Privacy/compliance violation | Mask or exclude; use token references |
| Excessive logging | Cost explosion, signal drowns in noise | Log business events, not data flow |
| Unstructured logs | Cannot query or alert on fields | Structured JSON with consistent schema |
| String interpolation in logs | Breaks structured fields, injection risk | Pass fields as metadata |
| Missing correlation IDs | Cannot trace across services | Generate and propagate trace_id everywhere |
| Alert storms | On-call fatigue, real issues buried | Grouping, inhibition, deduplication |
| High-cardinality labels | Prometheus OOM, dashboard timeouts | Never use user/request ID as label |
| Alerts without runbooks | Unactionable, trust erosion | Mandatory runbook link on every alert |
| Logs-only observability | Blind to trends and flow | Add metrics and traces |
| No sampling strategy | Trace storage costs explode | Probabilistic + tail-based sampling |

---

## 11 · NEVER Do

1. **NEVER log passwords, tokens, API keys, or secrets** — even at DEBUG
2. **NEVER use console.log / print in production** — use a structured logger
3. **NEVER use user IDs, emails, or request IDs as metric labels** — cardinality explosion
4. **NEVER create alerts without a runbook link**
5. **NEVER rely on logs alone** — you need all three pillars
6. **NEVER log request/response bodies by default** — opt-in only with PII redaction
7. **NEVER ignore log volume** — set budgets and alert on quota breach
8. **NEVER skip context propagation in async flows** — broken traces are worse than none
