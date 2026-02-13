# N-th Order Effects Analysis Framework

Every decision creates ripples. This framework forces structured evaluation of consequences beyond the immediate result.

## The Three-Layer Model

| Order | Question | Time Horizon | Visibility |
|---|---|---|---|
| **1st** | What is the direct result of this action? | Immediate | Obvious |
| **2nd** | What does that result cause? | Hours to days | Often missed |
| **3rd** | What does *that* cause? | Days to weeks | Rarely considered |

Most planning stops at 1st order. Most failures originate at 2nd or 3rd.

## Analysis Template

For any significant decision, fill in this chain:

```
ACTION: [What you're about to do]

1st ORDER: [Direct, immediate consequence]
  └─ 2nd ORDER: [What the 1st order consequence causes]
       └─ 3rd ORDER: [What the 2nd order consequence causes]

1st ORDER: [Another direct consequence]
  └─ 2nd ORDER: ...
       └─ 3rd ORDER: ...
```

### Worked Example: Adding a Caching Layer

```
ACTION: Add Redis caching to API responses

1st ORDER: API responses are faster (50ms → 5ms)
  └─ 2nd ORDER: Stale data becomes possible (cache TTL window)
       └─ 3rd ORDER: Users make decisions on outdated information
                     Operations team needs cache invalidation strategy
                     Bug reports increase for "data not updating"

1st ORDER: Database load decreases by ~80%
  └─ 2nd ORDER: DB performance issues are masked, not fixed
       └─ 3rd ORDER: When cache fails, DB gets 5× expected load and crashes
                     Team loses urgency to optimize slow queries

1st ORDER: New infrastructure dependency (Redis)
  └─ 2nd ORDER: Deployment complexity increases, new failure mode
       └─ 3rd ORDER: On-call burden increases
                     New team members need Redis knowledge
```

## Evaluation Dimensions

When analyzing effects, consider impact across these dimensions:

### People
- Who is affected beyond the immediate user?
- Does this change anyone's workflow without their input?
- Does this create work for someone who didn't ask for it?
- Does this shift responsibility or blame?

### Systems
- What systems are downstream of this change?
- What happens to those systems under the new behavior?
- Are there integration points that assume the old behavior?
- What monitoring or alerting needs to change?

### Incentives
- What behavior does this encourage?
- What behavior does this discourage?
- If everyone adopted this pattern, what would happen?
- Are the incentives aligned with the user's actual goals?

### Failure Modes
- What new ways can things break?
- What existing safety mechanisms does this bypass or weaken?
- What happens when this system is down?
- What's the blast radius of a failure?

## When to Run Full Analysis

**Full analysis (all three orders):**
- Architecture decisions
- New infrastructure or dependencies
- Changes to data models or schemas
- Anything affecting multiple teams or systems
- Irreversible changes

**Quick analysis (1st and 2nd order only):**
- Code refactoring within a single module
- Configuration changes
- Adding a new feature to an existing system
- Documentation changes

**Skip (1st order sufficient):**
- Bug fixes with clear scope
- Formatting or style changes
- Adding tests
- Updating dependencies (minor versions)

## The "Success Disaster" Test

Ask: **"If this works exactly as planned, what problems does success create?"**

This catches the most dangerous category of n-th order effects — the ones where nothing goes wrong, but the outcome still causes harm.

Examples:
- A feature is so popular it overwhelms infrastructure → success disaster
- Automation eliminates manual review that caught errors → success disaster
- Cost optimization works so well that the team loses budget for the service → success disaster

## Communicating Effects to Users

When you identify significant 2nd or 3rd order effects, present them clearly:

**Good format:**
> This will [1st order effect], which is what you want. Two things to consider:
> - [2nd order effect] — this means [practical consequence]
> - [3rd order effect] — longer term, this could lead to [consequence]
> 
> Want to proceed as-is, or should we [mitigation]?

**Bad format:**
> Here are all the possible consequences I can think of: [wall of text covering every conceivable outcome]

Focus on effects that are **non-obvious AND actionable**. Skip effects that are obvious or that the user can't do anything about.
