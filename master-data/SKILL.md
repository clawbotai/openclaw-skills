# Master Data Skill

Comprehensive data engineering skill covering database design, PostgreSQL operations, schema management, and modern data patterns.

---

## 1. Schema Design

### Normalization
- **1NF–3NF / BCNF**: Eliminate redundancy for OLTP workloads
- **When to denormalize**: Read-heavy analytics, materialized views, pre-joined tables

### Star Schema & Dimensional Modeling
- Fact tables (measures) + dimension tables (context)
- Slowly Changing Dimensions (SCD Type 1/2/3)
- Use for data warehouses and OLAP queries

### Naming Conventions
- `snake_case` for tables/columns
- Singular table names (`user` not `users`) — pick one, be consistent
- Prefix: `fk_`, `idx_`, `uq_` for constraints/indexes
- Always include `id`, `created_at`, `updated_at`

### Data Validation
- Use `CHECK` constraints, `NOT NULL`, enums, domains
- Validate at DB level (last line of defense) AND application level
- Use `pg_jsonschema` or application-layer validation for JSON columns

---

## 2. PostgreSQL Operations

### Connection Management
- **Connection pooling** is mandatory for production: use **PgBouncer** (transaction mode) or **pgpool-II**
- Pool sizing: `connections = (cores * 2) + effective_spindle_count`
- Set `statement_timeout`, `idle_in_transaction_session_timeout`

### Configuration Tuning
```
shared_buffers = 25% of RAM
effective_cache_size = 75% of RAM
work_mem = RAM / max_connections (start 4-16MB)
maintenance_work_mem = 512MB-1GB
random_page_cost = 1.1 (SSD) | 4.0 (HDD)
wal_buffers = 64MB
max_wal_size = 2GB
```

### Query Optimization
- **Always use `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)`** to diagnose
- Watch for: sequential scans on large tables, nested loops on big sets, high buffer hits vs reads
- Use CTEs cautiously (materialized by default pre-PG12, optimization fence)
- Prefer `EXISTS` over `IN` for subqueries
- Use `LIMIT` with `ORDER BY` indexed columns for pagination (keyset pagination > OFFSET)

### Indexing Strategies
| Type | Use Case |
|------|----------|
| **B-tree** | Default. Equality, range, sorting, `LIKE 'prefix%'` |
| **GIN** | Full-text search, JSONB, arrays, trigrams |
| **GiST** | Geometry/spatial, range types, full-text |
| **BRIN** | Very large tables with natural ordering (timestamps, IDs) |
| **Hash** | Equality-only (rare, B-tree usually better) |

- **Partial indexes**: `CREATE INDEX ... WHERE condition` — index only relevant rows
- **Covering indexes**: `INCLUDE (col)` to enable index-only scans
- **Expression indexes**: `CREATE INDEX ... ON (lower(email))`
- Monitor with `pg_stat_user_indexes` — drop unused indexes

### Partitioning
- **Range**: Time-series data (`created_at` ranges)
- **List**: Category-based (region, tenant)
- **Hash**: Even distribution when no natural partition key
- Use declarative partitioning (PG 10+), partition pruning automatic
- Detach/attach partitions for zero-downtime maintenance

---

## 3. Migrations

### Zero-Downtime Migration Patterns
1. **Add column** → nullable first, backfill, then add constraint
2. **Rename column** → add new, dual-write, migrate reads, drop old
3. **Add index** → `CREATE INDEX CONCURRENTLY` (no table lock)
4. **Drop column** → stop writing, deploy, then drop
5. **Change type** → add new column, backfill, swap

### Tools
- **Flyway** / **Liquibase**: Java ecosystem
- **golang-migrate**: Go ecosystem
- **Alembic**: Python/SQLAlchemy
- **Prisma Migrate** / **Drizzle Kit**: TypeScript
- **sqitch**: Database-native, dependency-based

### Schema Versioning
- Every change is a numbered migration file (up + down)
- Store migration state in `schema_migrations` table
- Never edit applied migrations — always add new ones
- Review migrations in CI before deploy

---

## 4. Backup & Recovery

### WAL Archiving & PITR
- Enable `archive_mode = on`, configure `archive_command`
- Use **pgBackRest** or **Barman** for production backups
- Test restores regularly (untested backups = no backups)

### Backup Strategy
- **Full**: Weekly (pg_basebackup)
- **Incremental**: Daily (WAL archiving)
- **Logical**: pg_dump for schema-level / cross-version migration
- Retention: 30 days minimum, compliance-dependent

### Replication
- **Streaming replication**: Real-time binary, read replicas
- **Logical replication**: Selective tables, cross-version, pub/sub model
- Use for read scaling, geographic distribution, zero-downtime upgrades

---

## 5. AI-Assisted Schema Design

### Workflow
1. Describe domain in natural language
2. Generate initial ERD and DDL
3. Review normalization, indexes, constraints
4. Generate migration files
5. Generate seed data for testing

### Prompt Patterns
```
Design a PostgreSQL schema for [domain]. Requirements:
- [list entities and relationships]
- [performance requirements]
- [expected scale]
Include: tables, indexes, constraints, and sample queries.
```

### Schema Review Checklist
- [ ] Primary keys on all tables
- [ ] Foreign keys with appropriate ON DELETE
- [ ] Indexes on foreign keys and frequent WHERE/JOIN columns
- [ ] `created_at` / `updated_at` timestamps
- [ ] Appropriate data types (don't use VARCHAR for everything)
- [ ] CHECK constraints for business rules
- [ ] COMMENT ON for documentation

---

## 6. Advanced Patterns

### CQRS & Event Sourcing
- Separate read/write models for complex domains
- Event store: append-only table with `event_type`, `payload` (JSONB), `created_at`
- Rebuild state by replaying events; use snapshots for performance
- Consider **EventStoreDB** for dedicated event stores

### Change Data Capture (CDC)
- **Debezium**: Captures row-level changes from WAL → Kafka
- Use for: real-time sync, event-driven architectures, audit logs
- Alternative: PostgreSQL logical decoding + `wal2json`

### Multi-Tenancy
- **Schema-per-tenant**: Strong isolation, migration complexity
- **Row-level (RLS)**: Shared tables + `tenant_id`, use `SET app.current_tenant`
- **Database-per-tenant**: Maximum isolation, operational overhead

### Database-per-Service (Microservices)
- Each service owns its data; no shared databases
- Communicate via APIs or events, not JOINs
- Use saga pattern for distributed transactions

### JSONB Patterns
- Use for flexible/semi-structured data within PostgreSQL
- Index with GIN: `CREATE INDEX ON t USING GIN (data jsonb_path_ops)`
- Use `jsonb_to_record` for querying as relational data
- Don't store everything as JSON — use proper columns for queried fields

### Time-Series
- Use partitioning by time range
- Consider **TimescaleDB** extension for automatic partitioning + compression
- Retention policies: auto-drop old partitions

### Full-Text Search
- `tsvector` + `tsquery` with GIN index
- Use `ts_rank` for relevance scoring
- Consider **pg_trgm** for fuzzy/similarity search
- For heavy search workloads, consider Elasticsearch/Meilisearch

---

## 7. ORMs & Query Builders

### Decision Guide
| Approach | When to Use |
|----------|-------------|
| **Raw SQL** | Complex queries, performance-critical, full control |
| **Query Builder** (Knex, Kysely, Drizzle) | Type-safe, composable, close to SQL |
| **ORM** (Prisma, TypeORM, SQLAlchemy, Django ORM) | Rapid development, simple CRUD, migrations |

### Best Practices
- Always log slow queries (`log_min_duration_statement = 1000`)
- Use parameterized queries (never string interpolation)
- Beware N+1 queries — use eager loading / DataLoader
- Use transactions for multi-statement operations

---

## 8. Monitoring & Observability

### Key Metrics
- `pg_stat_activity`: Active connections, waiting queries
- `pg_stat_user_tables`: Sequential vs index scans, dead tuples
- `pg_stat_statements`: Top queries by time/calls (enable extension)
- Autovacuum health: `last_autovacuum`, dead tuple ratio

### Tools
- **pg_stat_statements** (built-in extension)
- **pgHero** / **PgAnalyze**: Dashboard + recommendations
- **Prometheus + postgres_exporter**: Metrics pipeline

---

## Quick Reference Commands

```sql
-- Table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(oid)) FROM pg_class WHERE relkind='r' ORDER BY pg_total_relation_size(oid) DESC LIMIT 20;

-- Unused indexes
SELECT indexrelname, idx_scan FROM pg_stat_user_indexes WHERE idx_scan = 0 AND indexrelname NOT LIKE '%pkey%';

-- Active queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC;

-- Kill long query
SELECT pg_cancel_backend(pid);  -- graceful
SELECT pg_terminate_backend(pid);  -- force

-- Table bloat estimate
SELECT schemaname, tablename, n_dead_tup, n_live_tup, round(n_dead_tup::numeric/greatest(n_live_tup,1)*100, 2) AS dead_pct FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 20;

-- Force analyze
ANALYZE VERBOSE table_name;
```
