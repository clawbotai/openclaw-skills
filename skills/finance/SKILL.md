---
name: finance
description: Corporate finance — journal entries, account reconciliation, financial statements, variance analysis, month-end close management, and audit support. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Finance

Accounting and corporate finance workflows — journal entries with proper debits/credits, account reconciliation, financial statement generation, variance analysis with root cause narratives, month-end close management, and audit support.

## Activation Triggers

Activate when the user's request involves:
- Journal entries, debits/credits, or account coding
- Bank or account reconciliation
- Financial statements (P&L, balance sheet, cash flow)
- Budget vs actual variance analysis
- Month-end or quarter-end close procedures
- Audit preparation or documentation
- Revenue recognition or expense classification

## Commands

### `/finance:journal-entry`
Create a journal entry with proper accounting treatment.

**Workflow:**
1. **Identify transaction** — what economic event occurred?
2. **Determine accounts** — which accounts are affected? (chart of accounts lookup)
3. **Apply standards** — ASC 606 (revenue), ASC 842 (leases), ASC 350 (intangibles), IFRS as applicable
4. **Format entry** — date, accounts, debits, credits, memo, supporting reference
5. **Validate** — debits = credits, correct account types (asset/liability/equity/revenue/expense), proper period
6. **Reversing entries** — flag if entry needs auto-reversal next period (accruals)

**Output format:**
```
Date: 2026-02-12
Ref: JE-2026-0212-001

  DR  Accounts Receivable (1200)     $10,000.00
    CR  Revenue - Product Sales (4100)           $10,000.00

Memo: Invoice #INV-1234 to Acme Corp for ISOBAR Ø1 units
Standard: ASC 606 — performance obligation satisfied at shipment
```

### `/finance:reconciliation`
Reconcile an account balance.

**Workflow:**
1. **Pull balances** — GL balance vs external source (bank statement, sub-ledger, vendor statement)
2. **Match transactions** — automated matching by amount, date, reference
3. **Identify discrepancies** — unmatched items, timing differences, errors
4. **Classify differences** — timing (clears next period), permanent (needs adjustment), error (needs correction)
5. **Generate adjustments** — journal entries for permanent differences
6. **Document** — reconciliation report with sign-off

### `/finance:financial-statements`
Generate financial statements from trial balance data.

**Statements:**
- **Income Statement** (P&L) — revenue, COGS, gross margin, operating expenses, EBITDA, net income
- **Balance Sheet** — assets (current/non-current), liabilities (current/long-term), equity
- **Cash Flow Statement** — operating (indirect method), investing, financing
- **Statement of Equity** — beginning balance, net income, distributions, ending balance

### `/finance:variance-analysis`
Budget vs actual analysis with root cause narratives.

**Workflow:**
1. **Calculate variances** — $ and % for each line item
2. **Flag material items** — threshold: >5% or >$10K (configurable)
3. **Categorize** — volume variance, price/rate variance, mix variance, timing
4. **Root cause** — investigate drivers for each material variance
5. **Narrative** — plain-English explanation suitable for management review
6. **Trend** — compare to prior periods for recurring patterns

### `/finance:close-checklist`
Month-end close management with task tracking.

**Standard checklist:**
1. Cut off AP/AR — ensure transactions in correct period
2. Bank reconciliations — all accounts
3. Intercompany eliminations — if multi-entity
4. Accruals — payroll, utilities, professional services
5. Depreciation and amortization entries
6. Revenue recognition review — ASC 606 compliance
7. Inventory valuation — lower of cost or NRV
8. Prepaids and deferrals — amortization entries
9. Trial balance review — scan for anomalies
10. Financial statement generation and review
11. Flux analysis — period-over-period changes
12. Management review package

## Auto-Firing Skills

### Accounting Standards
**Fires when:** User discusses revenue, leases, or complex transactions.
Apply correct standard: ASC 606 (5-step revenue model), ASC 842 (lease classification: operating vs finance, ROU asset calculation), ASC 350 (goodwill impairment), ASC 820 (fair value hierarchy). Flag when IFRS differs from US GAAP.

### Financial Analysis
**Fires when:** User asks about financial health or ratios.
Key ratios: current ratio, quick ratio, DSO, DPO, inventory turns, gross margin %, operating margin %, ROIC, debt-to-equity. Always provide context (industry benchmarks, trend direction).

### Audit Support
**Fires when:** User mentions audit, compliance, or documentation.
Maintain audit trail: every entry needs supporting documentation reference. Prepare PBC (Prepared by Client) lists. Organize workpapers by assertion: existence, completeness, valuation, rights/obligations, presentation.

### Close Management
**Fires when:** It's near month-end or user mentions close.
Track checklist completion. Estimate remaining effort. Flag items at risk of missing deadline. Suggest parallel vs sequential task ordering for efficiency.

## Configuration

```yaml
chart_of_accounts: {}         # Account number → name mapping
fiscal_year_end: "12-31"      # MM-DD
reporting_currency: "USD"
materiality_threshold_pct: 5  # Variance % to flag
materiality_threshold_abs: 10000  # Variance $ to flag
accounting_standard: "US GAAP"  # US GAAP or IFRS
close_deadline_business_days: 5  # Days after month-end
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| GL System (QuickBooks/NetSuite/Xero) | Trial balance, journal entries | User provides CSV/data |
| Bank (Plaid/direct feeds) | Bank statements for reconciliation | User uploads statements |
| Data Warehouse | Historical data for analysis | User provides extracts |
| Expense (Expensify/Brex) | Expense reports and coding | Manual expense entry |
