# Master Growth & SaaS Metrics Skill

Comprehensive growth strategy, SaaS metrics, and startup scaling skill. Covers the full lifecycle from pre-product/market fit through scale-up.

---

## 1. North Star Metric (NSM) Framework

Help teams identify and track their single most important metric that captures the core value delivered to customers.

**Process:**
1. Define value hypothesis → what action signals a customer received value?
2. Map to measurable event (e.g., "weekly active projects" not "logins")
3. Decompose NSM into input metrics (breadth, depth, frequency, efficiency)
4. Build dashboards tracking NSM + inputs weekly

**Examples by business type:**
| Type | NSM Example |
|------|-------------|
| Marketplace | Weekly transactions completed |
| SaaS (collab) | Weekly active teams with 3+ members |
| Media | Total time spent reading/watching |
| E-commerce | Weekly purchases per active customer |
| Fintech | Assets under management |

---

## 2. AARRR Pirate Metrics

Full-funnel framework for tracking growth across five stages:

### Acquisition
- Channel attribution (first-touch, last-touch, multi-touch/linear, U-shaped, W-shaped)
- CAC by channel (paid, organic, referral, content, partnerships)
- Blended vs. paid CAC
- Channel saturation curves

### Activation
- Define "aha moment" — the action that correlates with long-term retention
- Time-to-value (TTV) optimization
- Onboarding funnel: signup → setup → first value moment
- Activation rate = users reaching aha moment / signups
- Benchmarks: 20-40% activation is typical; best-in-class >60%

### Retention
- **Cohort analysis**: group users by signup week/month, track % active over time
- **Retention curves**: plot retention by cohort; healthy = flattens (asymptote); unhealthy = trends to zero
- **Types**: User retention, revenue retention (net/gross), feature retention
- **N-day, unbounded, bracket retention** methods
- **Smile curve**: retained cohorts improve over time (resurrection + product improvements)
- Target: find where the curve flattens → that's your natural usage frequency

### Revenue
- ARPU, ARPA, ARPPU
- Expansion revenue (upsells, cross-sells, seat expansion)
- Contraction MRR vs. churn MRR
- Revenue per employee as efficiency metric

### Referral
- Viral coefficient (K-factor) = invites sent × conversion rate
- Viral cycle time (shorter = exponential faster)
- **Viral loop types**: word-of-mouth, incentivized (two-sided), usage (inherent/collaborative), content/UGC, API/integration
- NPS as leading indicator of organic referral

---

## 3. SaaS Metrics Deep Dive

### Revenue Metrics
- **MRR/ARR**: Monthly/Annual Recurring Revenue
  - New MRR + Expansion MRR − Contraction MRR − Churned MRR = Net New MRR
- **NDR (Net Dollar Retention)**: (Starting MRR + Expansion − Contraction − Churn) / Starting MRR
  - Best-in-class: >120%; good: >110%; concerning: <100%
- **GRR (Gross Revenue Retention)**: (Starting MRR − Contraction − Churn) / Starting MRR
  - Best-in-class: >95%; good: >90%
- **Quick Ratio**: (New MRR + Expansion MRR) / (Churned MRR + Contraction MRR)
  - >4 = hypergrowth; >2 = healthy; <1 = shrinking

### Unit Economics
- **LTV (Lifetime Value)**: ARPA × Gross Margin% / Revenue Churn Rate
- **CAC (Customer Acquisition Cost)**: Total S&M spend / New customers acquired
- **LTV:CAC ratio**: Target >3:1; >5:1 may mean underinvesting in growth
- **CAC Payback Period**: CAC / (ARPA × Gross Margin%). Target <18 months; best-in-class <12
- **Months to recover CAC** by segment — prioritize fastest-payback segments

### Efficiency Metrics
- **Rule of 40**: Revenue growth rate % + profit margin % ≥ 40
- **Burn Multiple**: Net burn / Net new ARR. <1x = amazing; 1-2x = good; >3x = bad
- **Magic Number**: Net new ARR / Prior quarter S&M spend. >0.75 = efficient; <0.5 = fix GTM
- **Hype Ratio**: ARR / Total capital raised. >1x at growth stage = capital efficient

### Churn Analysis
- **Logo churn**: % customers lost
- **Revenue churn**: % MRR lost (can differ significantly from logo churn)
- **Negative churn**: Expansion > churn → revenue grows even without new customers
- **Churn prediction signals**: declining usage, fewer logins, support tickets up, key user departure, missed QBRs, no expansion, contract approaching renewal with no champion engagement
- **Churn segmentation**: by plan tier, company size, industry, cohort vintage, acquisition channel

---

## 4. Product-Led Growth (PLG)

### Core Principles
- Product is the primary driver of acquisition, activation, and expansion
- Self-serve onboarding replaces sales-led demos for initial adoption
- Usage data drives expansion triggers and upgrade prompts

### PLG Motions
1. **Freemium**: Free tier with usage/feature limits → conversion to paid (target 2-5% conversion)
2. **Free trial**: Time-limited full access (7/14/30 days) → conversion (target 15-25%)
3. **Reverse trial**: Start with full features, downgrade to free after trial
4. **Open core**: Core OSS + commercial features (GitLab, Elastic model)
5. **Usage-based**: Pay-as-you-go with committed tiers (Snowflake, Twilio model)

### Freemium Conversion Optimization
- Identify features with highest correlation to conversion
- Strategic feature gating: gate collaboration/scale, not core value
- In-app upgrade prompts at natural friction points (not walls)
- Usage-based nudges ("You've used 80% of free storage")
- Social proof at upgrade points

### Onboarding Optimization
- **Reduce TTV**: Minimize steps between signup and first value
- **Progressive profiling**: Don't ask everything upfront
- **Empty state design**: Show what success looks like
- **Checklists/progress bars**: Guide users through activation milestones
- **Tooltips > tours**: Contextual help beats long walkthroughs
- **Template/example content**: Pre-populate so users see value instantly
- **Personalized paths**: Route users by role/use case/intent at signup

---

## 5. Growth Experimentation

### ICE Scoring
Rate each experiment 1-10 on:
- **Impact**: If it works, how big is the effect?
- **Confidence**: How sure are we it will work? (data-backed = high)
- **Ease**: How fast/cheap to implement?
- Score = (I + C + E) / 3 → prioritize highest scores

### RICE Scoring
- **Reach**: How many users/events per quarter?
- **Impact**: Minimal (0.25), Low (0.5), Medium (1), High (2), Massive (3)
- **Confidence**: High (100%), Medium (80%), Low (50%)
- **Effort**: Person-weeks
- Score = (R × I × C) / E → prioritize highest scores

### Experiment Process
1. **Hypothesis**: "If we [change], then [metric] will [improve by X%] because [reason]"
2. **Design**: Control vs. variant, sample size calculation, primary metric, guardrail metrics
3. **Run**: Minimum 1-2 weeks; achieve statistical significance (p<0.05, 80%+ power)
4. **Analyze**: Primary metric + segments + guardrails. Watch for novelty effects.
5. **Decide**: Ship, iterate, or kill. Document learnings regardless.
6. **Backlog grooming**: Re-score experiments monthly as context changes

### Growth Experiment Categories
- Acquisition: landing pages, ad copy, channels, partnerships, SEO
- Activation: onboarding flow, first-run experience, aha moment acceleration
- Retention: re-engagement emails, feature discovery, habit loops
- Monetization: pricing, packaging, upgrade prompts, trial length
- Referral: incentive structure, sharing mechanics, invite flow

---

## 6. Pricing Strategy

### Models
- **Flat-rate**: Simple, predictable; limits upside
- **Per-seat**: Scales with team size; aligns with collaboration value
- **Usage-based**: Aligns cost with value; unpredictable revenue
- **Hybrid**: Base platform fee + usage/seats (most common at scale)
- **Value-based**: Price anchored to customer ROI/value delivered

### Pricing Principles
- Price on value metric (the unit that scales with customer value)
- 3-4 tiers max for self-serve; custom/enterprise for high-touch
- Anchor high → discount feels like a deal
- Annual commit discount (typically 15-20%) to improve retention + cash flow
- Usage-based pricing floor for revenue predictability
- Packaging: differentiate by features, limits, support level, SLA

### Pricing Research Methods
- Van Westendorp Price Sensitivity Meter
- Conjoint analysis for feature/price tradeoffs
- Willingness-to-pay interviews (ask about value, not price)
- Competitive benchmarking (but don't price from competitors)

---

## 7. Retention & Engagement

### Engagement Frameworks
- **Hook Model** (Trigger → Action → Variable Reward → Investment)
- **Habit loops**: Identify natural usage frequency; design triggers around it
- **Aha moment mapping**: Correlate early actions with 30/60/90-day retention via regression

### Re-engagement Tactics
- Lifecycle email sequences (onboarding, activation, re-engagement, win-back)
- Push notifications (use sparingly; personalize by behavior)
- In-app notifications for feature discovery
- "Your weekly digest" — show value even when not logged in
- Win-back campaigns for churned users (30/60/90 day cadence)

### Churn Prevention
- Health scoring: composite of usage frequency, feature breadth, recency, support sentiment
- Automated alerts when health score drops below threshold
- CSM intervention playbooks by risk level
- Exit surveys to capture churn reasons → feed back to product

---

## 8. Community-Led Growth (CLG)

- Build community around the problem space, not just the product
- User-generated content as acquisition channel (templates, tutorials, showcases)
- Community champions program → power users become advocates
- Community → feedback loop → product improvements → more community value
- Measure: community-sourced signups, community-influenced expansion, time-to-answer

---

## 9. Cohort Analysis Templates

### User Retention Cohort Table
```
Cohort    | M0    | M1    | M2    | M3    | M4    | M5    | M6
----------|-------|-------|-------|-------|-------|-------|-------
Jan 2025  | 100%  | 45%   | 38%   | 35%   | 33%   | 32%   | 31%
Feb 2025  | 100%  | 48%   | 40%   | 37%   | 35%   | 34%   |
Mar 2025  | 100%  | 50%   | 43%   | 39%   | 37%   |       |
```

### Revenue Retention Cohort
Same structure but tracking MRR per cohort. NDR >100% means cohort revenue grows over time.

### Key Patterns to Watch
- **Improving cohorts**: Later cohorts retain better → product/onboarding is improving
- **Degrading cohorts**: Growth is masking declining quality or channel saturation
- **Cohort convergence**: All cohorts flatten to similar asymptote → stable product
- **Segment analysis**: Cut cohorts by acquisition channel, plan, company size, geography

---

## 10. Growth Model / Financial Projections

### Bottoms-Up Revenue Model
```
Inputs:
  - Monthly visitors (by channel)
  - Visitor → Signup rate
  - Signup → Activated rate  
  - Activated → Paid conversion rate (or trial → paid)
  - ARPA (by tier)
  - Monthly logo churn rate
  - Monthly expansion rate (NDR proxy)
  - Gross margin %

Outputs:
  - MRR/ARR trajectory
  - LTV, CAC, LTV:CAC
  - Payback period
  - Burn rate and runway
  - Rule of 40 score
  - Burn multiple
```

### Scenario Planning
- Bear / Base / Bull cases varying: conversion, churn, expansion, growth rate
- Sensitivity analysis: which input variable has the biggest impact on ARR?

---

## 11. Dashboards & Reporting

### Weekly Growth Dashboard
- NSM + input metrics (WoW change)
- Funnel: visitors → signups → activated → paid (conversion rates)
- Net new MRR breakdown (new, expansion, contraction, churn)
- Quick ratio

### Monthly Board/Investor Dashboard
- ARR + growth rate (MoM, YoY)
- NDR, GRR
- LTV:CAC, payback period
- Burn multiple, Rule of 40
- Cash balance + runway
- Logo + revenue churn
- Cohort retention trends

### Operational Metrics
- Activation rate by cohort
- Feature adoption rates
- Support ticket volume + resolution time
- NPS/CSAT trends

---

## Usage

When asked about growth, metrics, SaaS strategy, pricing, retention, experimentation, or startup scaling:
1. Identify which framework(s) apply
2. Ask clarifying questions about stage, business model, and current data
3. Apply relevant metrics, benchmarks, and tactics from above
4. Recommend specific experiments with ICE/RICE scores when appropriate
5. Provide templates for tracking and reporting

This skill replaces the previous `growth`, `startup-metrics`, and `saas` skills.
