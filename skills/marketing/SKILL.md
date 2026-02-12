---
name: marketing
description: Content creation, campaign planning, brand voice management, SEO audits, competitive analysis, and performance reporting. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Marketing

Content creation, campaign planning, brand voice management, competitive analysis, SEO audits, and performance reporting for marketing teams.

## Activation Triggers

Activate when the user's request involves:
- Creating marketing content (blog, social, email, landing pages)
- Campaign planning or strategy
- Brand voice or messaging guidelines
- SEO analysis or optimization
- Competitive messaging analysis
- Marketing performance reporting

## Commands

### `/marketing:create-content`
Create content for any channel. Apply brand voice and SEO best practices.

**Channel-specific:**
- **Blog**: 1500-2500 words, H2/H3 structure, featured image
- **Social**: Platform-specific lengths and formats
- **Email**: Subject < 50 chars, preview text, scannable body, single CTA
- **Landing page**: Hero, benefits, social proof, CTA above fold

### `/marketing:plan-campaign`
Complete campaign plan: strategy, channel selection, content calendar, budget allocation, success metrics.

**Framework:** Awareness vs. Demand Gen vs. Retention. Channel selection: awareness (social, display) → consideration (content, email) → decision (retargeting, sales).

### `/marketing:seo-audit`
Comprehensive SEO audit: keyword research, on-page analysis, content gaps, technical checks, competitor comparison.

**Methodology:** Search intent classification (informational/navigational/transactional/commercial), content pillar/cluster model, internal linking strategy, SERP feature opportunities.

### `/marketing:competitive-brief`
Competitive messaging analysis: positioning comparison, content gaps, differentiation opportunities.

### `/marketing:performance-report`
Cross-channel performance reports with insights and recommendations.

## Auto-Firing Skills

### Content Creation
**Fires when:** User asks to write or draft marketing content.

### Brand Voice
**Fires when:** User mentions brand voice, tone, or messaging consistency.
Voice documentation, tone adaptation by channel/audience, style guide enforcement, terminology management.

### Campaign Planning
**Fires when:** User discusses campaign strategy or multi-channel marketing.

### SEO Strategy
**Fires when:** User asks about SEO, organic search, or keywords.

### Competitive Intelligence
**Fires when:** User asks about competitors or market landscape.
Messaging comparison, content gap analysis, channel strategy comparison, launch monitoring.

## Configuration

```yaml
brand_voice: {}        # Voice attributes, tone guidelines, terminology
target_audiences: []   # Persona definitions with pain points
competitors: []        # Competitor list with URLs and positioning
content_calendar: {}   # Active editorial schedule
style_guide: ""        # Writing style rules
channel_accounts: {}   # Social handles, email lists
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Design (Canva/Figma) | Templates, brand assets | Text-only content |
| Marketing Automation (HubSpot) | Campaign management, analytics | Manual tracking |
| Analytics (Amplitude) | Conversion funnels, attribution | User provides data |
| SEO (Ahrefs) | Keyword data, backlinks | Web search for research |
| Knowledge Base (Notion) | Content calendar, brand guidelines | User provides guidelines |
