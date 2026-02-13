# N-th Order Effects Analysis Framework

## Conceptual Foundation

Every decision creates ripples. First-order effects are obvious — they're what you
intended. Second-order effects are what your first-order effects cause. Third-order
effects are what happens when the second-order effects interact with the broader system.

Most catastrophic software failures aren't caused by first-order effects. They're caused
by second and third-order effects that nobody analyzed.

**Principle:** You cannot predict all downstream effects, but you can develop the discipline
to look for them systematically. The goal is not omniscience — it's diligence.

## The Three-Layer Analysis

For any significant decision, explicitly walk through three layers:

### Layer 1: Direct Effects (What happens immediately)

This is the easy part. What does this change do, directly?

- What state changes occur?
- What becomes possible that wasn't before?
- What becomes impossible that was possible before?
- Who or what is directly affected?

### Layer 2: Consequential Effects (What the direct effects cause)

This is where most analysis stops — and where most problems begin.

**Prompt questions:**
- Now that [Layer 1 effect] exists, how does behavior change?
- What systems consume the output of this change?
- What assumptions do downstream systems make that this change might violate?
- If someone relies on [Layer 1 effect], what new risks do they face?
- What does this incentivize? What does it disincentivize?

**Common Layer 2 patterns:**
| Layer 1 Effect | Common Layer 2 Effect |
|---|---|
| Added caching | Stale data problems |
| Added automation | Loss of human oversight |
| Improved speed | Increased demand / load |
| Added a feature | Increased maintenance burden |
| Changed a data format | Downstream parser failures |
| Added a dependency | Supply chain vulnerability |
| Simplified an interface | Lost power-user capabilities |
| Added monitoring | Alert fatigue |
| Changed permissions | Workflow disruption |

### Layer 3: Systemic Effects (What emerges from Layer 2 interactions)

This layer is speculative but important. It asks: what happens when Layer 2 effects
interact with each other and with the broader environment?

**Prompt questions:**
- If Layer 2 effects accumulate over time, what trend emerges?
- What happens when this scales to 10x / 100x users/load/data?
- If this becomes the standard approach, what pressure does that create?
- What happens when someone copies this pattern without understanding the context?
- Is there a "success disaster" — the plan works but creates a worse problem?

## Decision Framework

After analyzing all three layers:

| Finding | Action |
|---|---|
| All layers look clean | Proceed |
| Layer 2 has manageable risks | Proceed with documentation of risks |
| Layer 2 has significant risks | Surface to user, propose mitigations |
| Layer 3 has concerning patterns | Flag to user as consideration, not blocker |
| Any layer shows irreversible harm | Stop and discuss with user |

## Practical Application

### For Code Changes
1. What does this code do? (Layer 1)
2. What calls this code? What consumes its output? (Layer 2)
3. If this code has a bug or changes behavior, what's the blast radius? (Layer 3)

### For Architecture Decisions
1. What does this architecture enable? (Layer 1)
2. What constraints does it impose? What does it make hard? (Layer 2)
3. If we're locked into this for 2 years, what problems emerge? (Layer 3)

### For Process Changes
1. What does this process change improve? (Layer 1)
2. How do people adapt their behavior? Do workarounds emerge? (Layer 2)
3. What culture does this create long-term? (Layer 3)

### For Data Decisions
1. What data is created, moved, or deleted? (Layer 1)
2. Who else uses this data? What decisions depend on it? (Layer 2)
3. If this data is wrong, stale, or missing — what cascade of failures occurs? (Layer 3)

## The "Inversion" Technique

When standard forward analysis isn't revealing enough, invert:

1. Imagine the worst outcome this decision could produce
2. Work backwards: What chain of events leads to that outcome?
3. Assess: Is any link in that chain plausible?
4. If yes: What would prevent it?

This is essentially a structured pre-mortem applied at each layer.

## When NOT to Over-Analyze

This framework is a tool, not a religion. Apply proportional effort:

| Task Type | Analysis Depth |
|---|---|
| Quick fix, low stakes | Layer 1 only (30 seconds) |
| New feature, moderate stakes | Layers 1-2 (2-3 minutes) |
| Architecture decision, high stakes | All three layers (5-10 minutes) |
| Irreversible action | All three layers + user discussion |

Don't spend 10 minutes analyzing the second-order effects of fixing a typo.
Do spend 10 minutes analyzing the second-order effects of changing a database schema.
