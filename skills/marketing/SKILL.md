---
name: marketing
description: Content creation, campaign planning, brand voice management, SEO audits, competitive analysis, and performance reporting. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Marketing

Content creation, campaign planning, brand voice management, SEO audits, competitive intelligence, and performance reporting. Maintains brand voice consistency across all channels.

## Activation Triggers

Activate when the user's request involves:
- Content creation (blog, social, email marketing, landing pages)
- Campaign planning or launch coordination
- SEO audit or keyword strategy
- Brand voice or messaging guidelines
- Competitive marketing analysis
- Marketing performance reporting or attribution

## Commands

### `/marketing:create-content`
Create content aligned with brand voice and channel requirements.

**Workflow:**
1. **Brief** — objective, audience, channel, key message, CTA
2. **Research** — topic depth, competitor content, trending angles, keyword opportunities
3. **Draft** — write in brand voice, channel-appropriate format and length
4. **Optimize** — SEO (if web), engagement hooks (if social), deliverability (if email)
5. **Review** — brand voice checklist, fact-check claims, legal compliance (disclaimers if needed)

**Channel formats:**
| Channel | Length | Tone | Key Element |
|---------|--------|------|-------------|
| Blog post | 1,000–2,500 words | Educational/authoritative | SEO-optimized headers, internal links |
| LinkedIn | 100–300 words | Professional/insightful | Hook in first line, personal angle |
| Twitter/X | <280 chars | Sharp/conversational | One idea per post, no links in first tweet |
| Email | 150–300 words | Direct/personal | Subject line A/B variants, single CTA |
| Landing page | 500–1,000 words | Persuasive/benefit-focused | Hero→Problem→Solution→Proof→CTA |

### `/marketing:plan-campaign`
Design a multi-channel campaign.

**Workflow:**
1. **Objective** — awareness, lead gen, activation, retention? SMART goal.
2. **Audience** — segments, personas, pain points, where they hang out
3. **Messaging** — core message, supporting messages per channel
4. **Channel mix** — organic (content, social, SEO, email) + paid (SEM, social ads, display)
5. **Timeline** — phases (pre-launch, launch, sustain), content calendar
6. **Budget allocation** — by channel, expected CPL/CAC
7. **Measurement** — KPIs per phase, attribution model, reporting cadence
8. **Assets needed** — copy, creative, landing pages, tracking setup

### `/marketing:seo-audit`
Audit a page or site for search optimization.

**Checklist:**
1. **Technical** — crawlability (robots.txt, sitemap), page speed (Core Web Vitals), mobile-friendly, HTTPS, canonical URLs, structured data (JSON-LD)
2. **On-page** — title tags (<60 chars, keyword), meta descriptions (<155 chars), H1-H3 hierarchy, keyword density (1-2%), internal linking, image alt text
3. **Content** — search intent match, content depth vs competitors, freshness, E-E-A-T signals
4. **Off-page** — backlink profile, domain authority, referring domains, anchor text distribution
5. **Opportunities** — keyword gaps, featured snippet targets, content clusters to build

### `/marketing:competitive-brief`
Competitive marketing intelligence.

**Sections:**
1. **Positioning** — how they describe themselves vs how market perceives them
2. **Messaging** — key themes, value props, differentiators claimed
3. **Channels** — where they're active, estimated spend, content frequency
4. **Content strategy** — topics, formats, distribution, engagement levels
5. **SEO** — ranking keywords, organic traffic estimate, content gaps
6. **Strengths** — what they do well (acknowledge honestly)
7. **Opportunities** — gaps you can exploit, audiences they ignore, channels they underuse

### `/marketing:performance-report`
Marketing performance report with insights.

**Metrics by channel:**
- **Web**: sessions, bounce rate, pages/session, conversion rate, top pages
- **Email**: open rate, CTR, unsubscribes, revenue attributed
- **Social**: followers, engagement rate, reach, top posts, share of voice
- **Paid**: impressions, clicks, CTR, CPC, conversions, ROAS
- **Content**: page views, time on page, backlinks earned, keyword rankings

**Report structure:** Executive summary → channel breakdown → wins → losses → recommendations → next period priorities

## Auto-Firing Skills

### Brand Voice
**Fires when:** Creating any external-facing content.
Maintain voice profile: tone (e.g., authoritative but approachable), vocabulary (preferred terms, banned words), formatting (e.g., Oxford comma, em dash usage), personality traits. Flag deviations.

### Content Strategy
**Fires when:** User discusses blog, content calendar, or topics.
Content pillars, topic clusters for SEO, content recycling (blog → social → email → slide deck), seasonal relevance, competitor content gap analysis.

### Campaign Execution
**Fires when:** User discusses launch or promotion.
Pre-launch checklist: tracking pixels, UTM parameters, landing page live, email sequences loaded, social scheduled, team briefed, customer support briefed.

### SEO Intelligence
**Fires when:** User discusses search, keywords, or organic traffic.
Keyword research methodology: seed → expansion → intent classification (informational/navigational/transactional/commercial) → difficulty assessment → prioritization (traffic × business value ÷ difficulty).

### Competitive Monitoring
**Fires when:** User mentions competitors or market positioning.
Track: messaging changes, new product launches, pricing changes, content themes, hiring signals (what roles = what strategy), customer reviews (G2/Capterra).

## Configuration

```yaml
brand_voice:
  tone: ""                     # e.g., "authoritative, technical, minimal"
  banned_words: []             # Words to never use
  preferred_terms: {}          # Mapping of terms to preferred versions
company_name: ""
target_audience: []            # Primary audience segments
competitors: []                # Competitor names to monitor
content_pillars: []            # Core topic areas
seo_target_keywords: []        # Priority keywords
social_channels: []            # Active social platforms
email_platform: ""             # ESP identifier
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| CMS (WordPress/Ghost) | Content publishing | Output markdown for manual publishing |
| Analytics (GA4/Plausible) | Traffic and conversion data | User provides screenshots/exports |
| SEO (Ahrefs/SEMrush) | Keyword data, backlinks, rankings | Web search for keyword insights |
| Email (Mailchimp/ConvertKit) | Email campaigns, list management | Draft emails for manual send |
| Social (Buffer/Hootsuite) | Social scheduling, analytics | Output content for manual posting |
| Ads (Google Ads/Meta) | Paid campaign management | Campaign specs for manual setup |
