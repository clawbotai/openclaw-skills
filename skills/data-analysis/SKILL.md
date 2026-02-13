---
name: data-analysis
description: SQL queries, data exploration, visualization, dashboards, statistical analysis, and insight generation for any data warehouse and SQL dialect. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Data Analysis

Write SQL, explore data, build dashboards, and run statistical analysis across any SQL dialect. Translates business questions into queries, validates data quality, and generates actionable insights with proper statistical rigor.

## Activation Triggers

Activate when the user's request involves:
- Writing or debugging SQL queries
- Exploring a dataset or database schema
- Building dashboards or visualizations
- Statistical analysis or hypothesis testing
- Data quality validation or profiling
- Business metrics definition or tracking

## Commands

### `/data:write-query`
Generate SQL from natural language.

**Workflow:**
1. **Clarify intent** — what business question does this answer?
2. **Identify tables** — schema exploration if needed (`INFORMATION_SCHEMA`, `pg_catalog`, etc.)
3. **Write query** — correct dialect (PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, Redshift)
4. **Explain** — comment each CTE/subquery with business logic
5. **Optimize** — index hints, partition pruning, avoid SELECT *
6. **Validate** — check for NULL handling, edge cases, off-by-one in date ranges

**Dialect-specific patterns:**
- **PostgreSQL**: `DATE_TRUNC`, `FILTER (WHERE ...)`, window functions, CTEs
- **BigQuery**: `SAFE_DIVIDE`, `UNNEST`, `STRUCT`, partitioned tables
- **SQLite**: `strftime`, no window functions in older versions
- **MySQL**: `DATE_FORMAT`, `GROUP_CONCAT`, `IFNULL`

### `/data:explore-data`
Profile a dataset or table.

**Workflow:**
1. **Schema** — columns, types, constraints, indexes
2. **Volume** — row count, size, partitioning
3. **Distribution** — distinct values, NULL rates, min/max/mean per column
4. **Quality** — orphaned foreign keys, duplicate detection, anomalies
5. **Relationships** — join paths, implicit foreign keys (naming convention matching)
6. **Summary** — plain-English description of what this data represents

### `/data:build-dashboard`
Design a dashboard for a business question.

**Workflow:**
1. **Identify KPIs** — what metrics answer the question?
2. **Choose chart types** — bar (comparison), line (trend), scatter (correlation), table (detail)
3. **Write backing queries** — one per widget, optimized for refresh frequency
4. **Layout** — hierarchy: summary KPIs at top, trends in middle, detail at bottom
5. **Filters** — date range, segment, dimension selectors
6. **Output** — SQL + layout spec (or self-contained HTML dashboard)

### `/data:statistical-analysis`
Statistical analysis with proper methodology.

**Workflow:**
1. **Formalize hypothesis** — H₀ and H₁, significance level (default α=0.05)
2. **Check assumptions** — normality, independence, homoscedasticity
3. **Select test** — t-test, chi-square, Mann-Whitney, ANOVA, regression based on data type and assumptions
4. **Execute** — compute test statistic, p-value, confidence intervals, effect size
5. **Interpret** — practical significance vs statistical significance
6. **Report** — plain-English conclusion with caveats

## Auto-Firing Skills

### SQL Best Practices
**Fires when:** Writing any SQL query.
- Always use CTEs over nested subqueries for readability
- Explicit JOIN syntax (never implicit comma joins)
- Handle NULLs explicitly (`COALESCE`, `NULLIF`, `IS NOT NULL`)
- Date range: use `>=` start and `<` end (not `BETWEEN` for timestamps)
- Always `GROUP BY` the non-aggregated columns
- Add `ORDER BY` for deterministic results
- Limit result sets in exploration (`LIMIT 1000`)

### Data Visualization
**Fires when:** User asks for charts or visual representation.
Chart selection: categorical comparison (bar), time series (line), distribution (histogram), correlation (scatter), composition (stacked bar/pie for ≤5 categories), geographic (choropleth). Never use pie charts for >5 slices.

### Data Quality
**Fires when:** User mentions data issues, or anomalies detected during exploration.
Automated checks: NULL rates >10%, duplicate primary keys, referential integrity violations, statistical outliers (>3σ), sudden volume changes (>50% day-over-day), schema drift.

### Statistical Rigor
**Fires when:** User wants to draw conclusions from data.
Common pitfalls: multiple comparisons (Bonferroni correction), survivorship bias, Simpson's paradox, confounding variables, small sample sizes (<30), p-hacking. Always report confidence intervals alongside point estimates.

## Configuration

```yaml
default_dialect: "postgresql"    # SQL dialect
warehouse_connection: ""         # Connection string or reference
schema_cache_ttl: 3600          # Seconds to cache schema info
max_query_rows: 10000           # Safety limit for result sets
chart_library: "html"           # Output: html (self-contained), matplotlib, vega-lite
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| SQL Warehouse (PostgreSQL/BigQuery/etc.) | Execute queries | User runs query manually, pastes results |
| Visualization (Grafana/Metabase) | Dashboard hosting | Generate self-contained HTML dashboards |
| Notebook (Jupyter) | Interactive analysis | Python/SQL code blocks in conversation |
| dbt | Model documentation, lineage | User provides schema docs |
