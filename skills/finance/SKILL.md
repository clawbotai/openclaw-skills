---
name: finance
description: Corporate finance — journal entries, account reconciliation, financial statements, variance analysis, month-end close management, and audit support. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Finance

Journal entry preparation, account reconciliation, financial statement generation, variance analysis, close process management, and audit support for corporate finance teams.

**⚠️ DISCLAIMER**: This skill assists with financial workflows but does not constitute professional accounting or financial advice. All outputs should be reviewed by qualified finance professionals.

## Activation Triggers

Activate when the user's request involves:
- Journal entries, debits/credits, or account coding
- Account reconciliation or balance comparison
- Financial statements (income statement, balance sheet, cash flow)
- Budget vs. actual variance analysis
- Month-end or year-end close processes
- Audit preparation or PBC lists

## Commands

### `/finance:journal-entry`
Prepare journal entries with proper debits/credits, account coding, supporting documentation references, and approval routing.

### `/finance:reconciliation`
Reconcile accounts: compare balances, identify discrepancies, prepare reconciliation documentation.

### `/finance:financial-statements`
Generate formatted financial statements (income statement, balance sheet, cash flow) from available data.

### `/finance:variance-analysis`
Analyze budget vs. actual variances with root cause identification and narrative explanations.

### `/finance:close-checklist`
Generate and track month-end/year-end close checklist: task assignments, deadlines, status tracking.

**Standard close sequence:** Subledger close → Intercompany eliminations → Accruals → Reserves → Consolidation → Reporting.

## Auto-Firing Skills

### Accounting Standards
**Fires when:** User asks about accounting treatment, GAAP, or IFRS.
Core standards: Revenue recognition (ASC 606), Lease accounting (ASC 842), Stock compensation (ASC 718), Debt/equity (ASC 470/480), Fair value (ASC 820). Principles: matching, conservatism, materiality, consistency.

### Financial Analysis
**Fires when:** User asks about financial ratios, metrics, or financial health.
Ratios: Liquidity (current, quick, cash), Profitability (gross/operating/net margin, ROE, ROA), Efficiency (DSO, DPO, inventory turns), Leverage (debt/equity, interest coverage). Trend analysis: period-over-period, rolling averages, seasonality.

### Audit Support
**Fires when:** User mentions audit, PBC list, or control testing.
PBC list management, documentation organization, control documentation, walkthrough prep. SOX compliance basics, control testing, remediation tracking.

### Close Management
**Fires when:** User discusses month-end close or period-end processes.
Close calendar, critical path, dependency management, pre-close activities, post-close review.

## Configuration

```yaml
chart_of_accounts: {}  # Account numbers, names, types
close_calendar: {}     # Standard close timeline
materiality_thresholds: {} # Variance analysis and JE approval thresholds
accounting_policies: {} # Specific policies and elections
reporting_format: {}   # Standard report formats
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Data Warehouse (Snowflake/BQ) | Financial data, GL, reporting | User provides data |
| Chat (Slack) | Close status, cross-functional comms | Manual updates |
| Email/Calendar (M365) | Audit correspondence, deadlines | User provides details |
