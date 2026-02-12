---
name: data-analysis
description: SQL queries, data exploration, visualization, dashboards, statistical analysis, and insight generation for any data warehouse and SQL dialect. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Data Analysis

SQL queries, data exploration, visualization, dashboards, and insight generation. Works with any data warehouse, any SQL dialect, and any analytics stack.

## Activation Triggers

Activate when the user's request involves:
- SQL queries, data extraction, or database operations
- Data exploration, profiling, or EDA
- Charts, visualizations, or dashboards
- Statistical analysis, A/B tests, or hypothesis testing
- Data quality checks or validation
- Metrics definitions or KPI tracking

## Commands

### `/data:write-query`
Write optimized SQL for the user's warehouse dialect. Includes schema exploration, query optimization, and result interpretation.

**Dialect awareness:** Snowflake (QUALIFY, FLATTEN), BigQuery (UNNEST, STRUCT), Databricks (Delta Lake syntax), PostgreSQL.
**Patterns:** Running totals, YoY comparison, cohort analysis, sessionization, funnel analysis, retention curves.

### `/data:explore-data`
Exploratory data analysis: profile dataset, identify patterns, outliers, distributions, relationships.

### `/data:build-dashboard`
Create interactive dashboard with multiple visualizations from dataset or queries. Self-contained HTML.

### `/data:statistical-analysis`
Statistical analysis: hypothesis testing, regression, cohort analysis, A/B test interpretation.

**Tests:** t-test (mean comparison), chi-squared (categorical), ANOVA (multi-group), regression (relationship quantification).
**A/B testing:** Sample size calculation, test duration, multiple comparison correction, practical vs. statistical significance.

## Auto-Firing Skills

### SQL Expertise
**Fires when:** User needs SQL written, optimized, or debugged.
Optimization: appropriate joins, window functions, CTEs for readability, index-aware patterns.

### Visualization Design
**Fires when:** User asks for charts or visual representation.
Chart selection: bar (comparison), line (trend), scatter (correlation), histogram (distribution), heatmap (density). Principles: clear labels, appropriate scales, colorblind-safe palettes, no 3D, data-ink ratio optimization.

### Statistical Methods
**Fires when:** User asks about statistical tests or significance.
Common tests, confidence intervals, sample size planning, effect size interpretation.

### Data Quality
**Fires when:** User asks about data validation or cleaning.
Dimensions: completeness (null rates), accuracy (range checks), consistency (duplicates, formats), timeliness (freshness). Always validate before sharing analysis.

## Configuration

```yaml
warehouse_dialect: "postgresql"  # SQL dialect
schema_documentation: {}         # Data dictionary, table descriptions
naming_conventions: {}           # SQL and column naming conventions
reporting_standards: {}          # Standard metrics definitions
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Data Warehouse (Snowflake/BQ) | Execute SQL, explore schemas | Generate SQL for user to run |
| Analytics (Hex/Amplitude) | Existing analyses, dashboards | Build from scratch |
| Project Tracker (Jira) | Data request tracking | Manual tracking |
