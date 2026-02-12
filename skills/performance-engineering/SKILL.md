# Master Performance & Cost Optimization Skill

> Unified skill for software performance engineering, load testing, profiling, caching, database optimization, FinOps, cloud cost optimization, and carbon-aware computing.

---

## 1. Performance Analysis & Profiling

### Application Profiling
- **Continuous profiling** with Pyroscope or Parca — always-on, low-overhead production profiling
- **On-demand profiling** — CPU (flame graphs), memory (allocation tracking), goroutine/thread analysis
- **eBPF-based observability** — kernel-level tracing without instrumentation (bcc, bpftrace, Cilium)
- **Language-specific profilers** — Go pprof, Java async-profiler/JFR, Python py-spy, Node clinic.js
- **Distributed tracing** — OpenTelemetry, Jaeger, Tempo for cross-service latency analysis

### Bottleneck Identification Workflow
1. Establish baseline metrics (p50/p95/p99 latency, throughput, error rate)
2. Identify hotspots via continuous profiling dashboards
3. Correlate with traces to find slow spans
4. Drill into flame graphs for code-level root cause
5. Validate fix with A/B comparison of profiles

---

## 2. Core Web Vitals & Frontend Performance

### Metrics
| Metric | Target | What It Measures |
|--------|--------|-----------------|
| **LCP** (Largest Contentful Paint) | ≤ 2.5s | Loading performance |
| **INP** (Interaction to Next Paint) | ≤ 200ms | Responsiveness |
| **CLS** (Cumulative Layout Shift) | ≤ 0.1 | Visual stability |

### Optimization Patterns
- **LCP**: Preload critical resources, optimize images (WebP/AVIF, responsive srcset), SSR/streaming HTML, font-display: swap
- **INP**: Break long tasks (yield to main thread), use `requestIdleCallback`, minimize JS bundle size, web workers for heavy computation
- **CLS**: Set explicit dimensions on images/embeds, avoid injecting content above fold, use CSS `contain`
- **Performance budgets**: Define max bundle size, max JS execution time, max request count — enforce in CI with Lighthouse CI or `bundlesize`

---

## 3. Load Testing & Capacity Planning

### Tools & When to Use
| Tool | Best For | Protocol Support |
|------|----------|-----------------|
| **k6** / Grafana Cloud k6 | Developer-centric, scriptable, CI integration | HTTP, gRPC, WebSocket, browser |
| **Artillery** | YAML-driven, quick scenarios, serverless-friendly | HTTP, Socket.io, WebSocket |
| **Locust** | Python-based, distributed, custom load shapes | HTTP (extensible) |
| **Gatling** | JVM teams, detailed reports | HTTP, WebSocket, JMS |

### Test Types
- **Smoke test** — minimal load, verify system works (1-5 VUs, 1 min)
- **Load test** — expected traffic, find baseline (target VUs, 10-30 min)
- **Stress test** — beyond capacity, find breaking point (ramp to failure)
- **Spike test** — sudden burst, test auto-scaling (instant jump to peak)
- **Soak test** — sustained load, find memory leaks/degradation (normal load, 2-8 hours)
- **Breakpoint test** — incremental ramp until failure to determine max capacity

### Load Test Workflow
```
1. Define SLOs (p99 < 500ms, error rate < 0.1%)
2. Script realistic user journeys (not just endpoint hits)
3. Use production-like data volumes
4. Run from multiple geographic regions if relevant
5. Monitor: app metrics, infra metrics, DB metrics, queue depths
6. Analyze: throughput curve, latency distribution, resource saturation
7. Report: max safe capacity, bottlenecks found, recommendations
```

---

## 4. Multi-Tier Caching

### Cache Layers (Edge → Origin)
```
Client (browser/app cache, service worker)
  → CDN (Cloudflare, CloudFront, Fastly) — static assets, edge compute
    → Reverse Proxy (Varnish, Nginx proxy_cache) — full page / API response cache
      → Application Cache (Redis, Memcached) — computed results, sessions, rate limits
        → Database Cache (query cache, materialized views, read replicas)
          → Origin Database
```

### Caching Strategies
| Strategy | Use Case |
|----------|----------|
| **Cache-aside** | General purpose, app controls cache population |
| **Read-through** | Cache acts as primary read interface |
| **Write-through** | Consistency-critical, cache updated on write |
| **Write-behind** | High write throughput, eventual consistency OK |
| **Refresh-ahead** | Predictable access patterns, pre-warm before expiry |

### Cache Invalidation Patterns
- **TTL-based** — simple, eventual consistency
- **Event-driven** — pub/sub on data changes (CDC with Debezium)
- **Tag-based** — invalidate groups of related entries
- **Versioned keys** — append version/hash to cache key, never invalidate

---

## 5. Database Performance

### Query Optimization
- **EXPLAIN ANALYZE** every slow query — understand execution plans
- **Index strategy**: covering indexes, partial indexes, composite indexes (column order matters)
- **N+1 detection**: Use query logging/APM to find repeated queries in loops; fix with eager loading, batch queries, or DataLoader pattern
- **Connection pooling**: PgBouncer (Postgres), ProxySQL (MySQL), application-level pools — size = (core_count * 2) + effective_spindle_count
- **Read replicas** for read-heavy workloads; route via proxy or app logic

### Database-Specific Optimizations
- **Partitioning** — range/hash/list for large tables (time-series, multi-tenant)
- **Materialized views** — pre-computed aggregations, refresh on schedule or trigger
- **Vacuum/analyze** (Postgres) — prevent bloat, keep statistics fresh
- **Slow query log** — enable and review regularly (long_query_time, pg_stat_statements)

### Async Processing
- Offload heavy work to queues (SQS, RabbitMQ, Redis Streams, Kafka)
- Use background workers for: email, PDF generation, image processing, webhooks, analytics
- Implement backpressure and circuit breakers
- Idempotency keys for safe retries

---

## 6. FinOps & Cloud Cost Optimization

### FinOps Framework (FOCUS Standard)
- **Inform** — Allocate costs accurately (tagging strategy, cost allocation, showback/chargeback)
- **Optimize** — Reduce waste (right-sizing, commitment discounts, spot/preemptible)
- **Operate** — Continuous governance (budgets, alerts, anomaly detection)

### Cost Visibility
- **Tagging strategy**: Enforce tags — `team`, `environment`, `service`, `cost-center`
- **Tools**: AWS Cost Explorer, GCP Billing, Azure Cost Management, **Kubecost** (Kubernetes), OpenCost
- **Unit economics**: Cost per request, cost per user, cost per transaction — track over time

### Right-Sizing
```
1. Collect 14+ days of CPU/memory utilization data
2. Identify over-provisioned resources (< 40% avg utilization)
3. Recommend instance family/size changes
4. Validate with load testing before applying
5. Automate with recommendations APIs (AWS Compute Optimizer, GCP Recommender)
```

### Commitment Discounts
| Type | Discount | Flexibility | Best For |
|------|----------|-------------|----------|
| **Reserved Instances** | 30-72% | Low (specific instance) | Stable baseline workloads |
| **Savings Plans** | 20-66% | Medium (compute family) | Variable but consistent spend |
| **Spot/Preemptible** | 60-90% | High (can be interrupted) | Stateless, fault-tolerant, batch |

### Spot Instance Patterns
- Use mixed instance pools (diversify across types/AZs)
- Implement graceful shutdown handlers (SIGTERM, 2-min warning)
- Combine with on-demand for baseline + spot for burst
- Use Karpenter or Cluster Autoscaler with spot node pools

---

## 7. Auto-Scaling Strategies

### Kubernetes Scaling
| Scaler | What It Scales | Based On |
|--------|---------------|----------|
| **HPA** (Horizontal Pod Autoscaler) | Pod replicas | CPU, memory, custom metrics |
| **VPA** (Vertical Pod Autoscaler) | Pod resource requests | Historical utilization |
| **KEDA** (Event-Driven Autoscaler) | Pod replicas | Queue depth, HTTP rate, cron, custom |
| **Karpenter/Cluster Autoscaler** | Nodes | Pending pod demand |

### Scaling Best Practices
- Set **resource requests** accurately (VPA recommendations → HPA scaling)
- Don't use VPA and HPA on the same metric simultaneously
- Use KEDA for event-driven workloads (scale to/from zero)
- Configure PodDisruptionBudgets to maintain availability during scaling
- Pre-warm for predictable spikes (scheduled scaling)

### Serverless Cost Optimization
- **Right-size memory** — profile to find optimal memory/cost ratio
- **Minimize cold starts** — provisioned concurrency for latency-sensitive, keep deployment packages small
- **Use ARM (Graviton)** — 20% cheaper, often faster
- **Avoid idle polling** — use event-driven triggers, not scheduled polling
- **Reserved concurrency** to prevent runaway costs

---

## 8. Storage & Data Transfer Optimization

### Storage Tiering
```
Hot  → SSD / gp3 / S3 Standard         (frequent access)
Warm → HDD / S3 IA / GCS Nearline      (monthly access)
Cold → S3 Glacier / Archive Storage     (yearly access)
```
- Implement **S3 Lifecycle Policies** to auto-tier objects by age
- Use **Intelligent-Tiering** when access patterns are unknown
- Compress before storing (zstd > gzip for most workloads)

### Data Transfer Cost Reduction
- Keep traffic **intra-AZ** when possible (free or cheap)
- Use **VPC endpoints / Private Link** to avoid NAT gateway charges
- **Compress API responses** (gzip/brotli)
- Use **CDN** to reduce origin egress
- Consider **multi-region replication** cost vs latency benefit
- **S3 Transfer Acceleration** / **CloudFront** for upload-heavy workloads

---

## 9. Carbon-Aware Computing

### Principles
- **Time-shift** batch workloads to low-carbon periods (use electricityMap API, WattTime)
- **Region-shift** to regions with greener grid mix
- **Right-size** — less waste = less carbon
- Use **ARM instances** — better perf/watt ratio
- Implement **Green Software Foundation** SCI (Software Carbon Intensity) metric
- Track carbon via cloud provider dashboards (AWS Customer Carbon Footprint, GCP Carbon Sense)

---

## 10. Performance Review Checklist

Use when auditing a system:

```markdown
### Frontend
- [ ] Core Web Vitals within targets (LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1)
- [ ] Performance budget defined and enforced in CI
- [ ] Images optimized (modern formats, lazy loading, srcset)
- [ ] JS bundle analyzed and code-split

### Backend
- [ ] p99 latency meets SLO
- [ ] No N+1 queries (verified via APM/query log)
- [ ] Connection pooling configured
- [ ] Async processing for heavy operations
- [ ] Caching strategy documented per service

### Infrastructure
- [ ] Auto-scaling configured and tested
- [ ] Resource requests/limits set accurately
- [ ] Load tested at 2x expected peak
- [ ] Capacity plan documented

### Cost
- [ ] All resources tagged
- [ ] Right-sizing review done (last 30 days)
- [ ] Commitment discounts evaluated
- [ ] Unused resources identified and removed
- [ ] Unit economics tracked
- [ ] Storage lifecycle policies in place

### Observability
- [ ] Continuous profiling enabled
- [ ] Distributed tracing instrumented
- [ ] Dashboards for latency, throughput, errors, saturation (USE/RED)
- [ ] Alerts on SLO burn rate
```

---

## 11. Templates & Quick Reference

### k6 Load Test Template
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // ramp up
    { duration: '5m', target: 50 },   // steady state
    { duration: '2m', target: 100 },  // stress
    { duration: '5m', target: 100 },  // steady stress
    { duration: '2m', target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(99)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('https://api.example.com/endpoint');
  check(res, {
    'status 200': (r) => r.status === 200,
    'latency < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

### Redis Caching Pattern (Python)
```python
import redis, json, hashlib

r = redis.Redis(connection_pool=pool)

def cached(ttl=300):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            key = f"{fn.__name__}:{hashlib.md5(json.dumps([args, kwargs], sort_keys=True, default=str).encode()).hexdigest()}"
            cached = r.get(key)
            if cached:
                return json.loads(cached)
            result = fn(*args, **kwargs)
            r.setex(key, ttl, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator
```

### Connection Pool Sizing Formula
```
pool_size = (core_count * 2) + effective_spindle_count
# For SSD: effective_spindle_count ≈ 1
# Example: 4-core server with SSD → pool_size = 9
# Start here, then tune based on monitoring
```

### Cost Tagging Policy Template
```yaml
required_tags:
  - key: team
    description: Owning team
    values: [platform, backend, data, ml]
  - key: environment
    description: Deployment environment  
    values: [production, staging, development]
  - key: service
    description: Service/application name
  - key: cost-center
    description: Business cost center
enforcement: deny-on-missing  # Block resource creation without tags
```

---

## Usage

When asked about performance or cost optimization:
1. **Diagnose** — Gather metrics, identify the constraint (CPU/memory/IO/network/cost)
2. **Prioritize** — Fix the biggest bottleneck first (Amdahl's law)
3. **Measure** — Baseline before, measure after (no unmeasured optimizations)
4. **Automate** — Codify the fix (IaC, CI checks, auto-scaling rules)
5. **Monitor** — Set alerts on regression, track unit economics over time
