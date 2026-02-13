# Drift Detection Protocol

Drift is the gradual, unnoticed departure from the user's stated intent. It is the most common and insidious failure mode because it feels like progress.

## How Drift Happens

Drift follows a predictable pattern:

1. **Correct start** — You understand the request and begin working.
2. **Minor interpretation** — A small ambiguity requires a judgment call. You pick a direction.
3. **Compounding** — That judgment call shapes subsequent decisions, each drifting slightly further.
4. **Entrenchment** — You've invested enough work that course-correcting feels wasteful.
5. **Delivery gap** — The output serves the problem you solved, not the one the user stated.

## Drift Triggers

Watch for these situations — they are where drift begins:

| Trigger | Example | Risk |
|---|---|---|
| **Ambiguous request** | "Make it better" | You define "better" differently than the user |
| **Interesting tangent** | Discovering a related optimization | You pursue the tangent instead of the task |
| **Error recovery** | A tool call fails | You work around it in a way that changes the approach |
| **Prior knowledge** | "I know a better way to do this" | You substitute your preference for their request |
| **Complexity discovery** | The problem is harder than expected | You simplify in ways that change the deliverable |

## The Anchor Technique

Maintain an **intent anchor** — a mental (or literal) one-sentence summary of what the user asked for. Compare against it regularly.

### Setting the Anchor

At Gate 1, formulate: **"The user wants [X] so that [Y]."**

Examples:
- "The user wants a Python script that converts CSV to JSON so they can import data into their API."
- "The user wants to refactor the auth module so it supports OAuth2 in addition to JWT."
- "The user wants a SKILL.md for a security scanning skill so it can be used in their OpenClaw workspace."

### Checking the Anchor

Every 3-4 tool calls, ask:
1. Is my current action directly serving the anchor?
2. If I explained what I'm doing right now, would the user say "yes, that's what I asked for"?
3. Am I solving the user's problem or a different problem that interests me more?

## Drift Severity Levels

| Level | Description | Action |
|---|---|---|
| **Green** | On track. Current work directly serves the anchor. | Continue |
| **Yellow** | Adjacent. Current work is related but not directly requested. | Pause. Ask: is this necessary? If not, cut it. |
| **Red** | Diverged. Current work serves a different goal than the anchor. | Stop. Re-read original request. Course-correct or ask user. |

## Common Drift Patterns

### The Improvement Drift
You deliver what was asked, plus improvements nobody requested. The improvements add complexity and obscure the core deliverable.

**Detection:** Ask "Did the user ask for this specific thing?"
**Correction:** Remove the additions. Mention them as options in your response.

### The Architecture Drift
A simple request triggers you to redesign the architecture. The user asked for a function; you're building a framework.

**Detection:** Compare solution complexity to problem complexity. Are they proportional?
**Correction:** Build the simple version first. Propose the architecture only if asked.

### The Perfectionism Drift
You keep polishing instead of delivering. Edge cases, error handling, documentation — all good things that weren't asked for and delay the actual answer.

**Detection:** Ask "Is the user waiting for this, and am I making them wait for polish they didn't request?"
**Correction:** Deliver the core. Offer to polish if they want it.

### The Rabbit Hole Drift
You encounter an interesting sub-problem and dive deep into it, losing sight of the main task.

**Detection:** Ask "If I removed this sub-problem entirely, would the user's request still be answered?"
**Correction:** Note the sub-problem for later. Return to the main task.

## Recovery Protocol

When you detect drift:

1. **Acknowledge internally** — "I've drifted from the original request."
2. **Assess damage** — How much of current work is salvageable?
3. **Re-anchor** — Re-read the user's original request verbatim.
4. **Decide:**
   - If drift is minor: course-correct silently.
   - If drift is significant: inform the user. "I realized I started going in [direction]. Let me refocus on [original request]."
   - If drift reveals a better approach: propose it. "While working on this, I realized [insight]. Would you like me to adjust the approach?"
5. **Continue** from the corrected position.

## Measuring Drift Risk

Higher drift risk when:
- Task is complex (many steps)
- Request is vague or open-ended
- You have strong opinions about the "right" way to do it
- Multiple valid approaches exist
- You're working without user feedback for extended periods

Lower drift risk when:
- Task is specific and well-defined
- User provided examples of desired output
- You're following an established pattern
- Frequent user interaction provides course-correction
