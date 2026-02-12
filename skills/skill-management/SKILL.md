---
name: skill-management
description: Meta-skill for creating, customizing, validating, and composing OpenClaw skills. The framework for extending the system with new domain expertise. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Skill Management (Meta-Skill)

Create new skills or customize existing ones for an organization's specific tools and workflows. This is the meta-skill that enables OpenClaw to extend itself.

## Activation Triggers

Activate when the user's request involves:
- Creating a new skill or plugin
- Customizing an existing skill
- Validating a skill specification
- Combining or composing skills
- Skill architecture or design patterns

## Commands

### `/skills:create-skill`
Guided workflow for creating a new OpenClaw skill.

**Structure:**
1. SKILL.md (YAML frontmatter: `name` + `description`)
2. Activation Triggers (when does it fire?)
3. Commands (explicit user actions with workflows)
4. Auto-Firing Skills (domain knowledge with activation conditions)
5. Configuration schema (organizational customization)
6. Connectors table (tool integrations + degraded behavior)
7. Optional: `scripts/`, `references/`, `assets/`

**Design principles:** Self-contained, model-agnostic, connector-optional, configurable, composable, portable (human-readable markdown).

### `/skills:customize-skill`
Customize an existing skill: add company context, swap connectors, adjust workflows.

### `/skills:validate-skill`
Validate a skill specification for completeness, consistency, and quality.

**Checklist:**
- [ ] YAML frontmatter has `name` and `description`
- [ ] Activation triggers defined
- [ ] At least one command with workflow
- [ ] At least one auto-firing skill with activation condition
- [ ] Configuration schema present
- [ ] Degraded mode behavior documented
- [ ] No vendor-specific assumptions in core logic

## Auto-Firing Skills

### Skill Architecture
**Fires when:** User asks how skills work or best practices for design.
Skills are modular, self-contained packages. Keep SKILL.md lean with procedural instructions; move reference material to `references/`. No compiled code, no proprietary formats.

### Skill Composition
**Fires when:** User wants to combine skills or create cross-functional workflows.

**Patterns:**
- **Sequential**: Skill A output feeds skill B
- **Parallel**: Multiple skills process different aspects of same request
- **Conditional**: Route to different skills based on request type
- **Hierarchical**: Meta-skill orchestrates sub-skills

**Cross-functional examples:**
- **Deal Review**: Legal (contract) + Sales (strategy) + Finance (revenue recognition)
- **Product Launch**: PM (spec/roadmap) + Marketing (campaign) + Support (KB prep) + Sales (battlecard)
- **Incident Response**: Legal (compliance) + Support (customer comms) + Search (context) + Productivity (task tracking)

## Configuration

```yaml
skill_registry: []     # Installed skills with versions
organization_context: {} # Shared context: company name, industry, tools, terminology
default_connectors: {}  # Org-wide connector config shared across skills
```

## Connectors

This meta-skill primarily uses the filesystem to read/write skill definitions. No external connectors required.
