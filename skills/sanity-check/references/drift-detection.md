# Drift Detection Protocol

## What Is Drift?

Drift is the gradual, often imperceptible divergence between what was asked and what is
being built. Unlike a wrong turn (which is sudden and obvious), drift is incremental.
Each individual step seems reasonable, but the cumulative effect is a destination nobody
intended to reach.

Research on AI agent behavior identifies drift as one of the most pernicious failure modes
because it evades both the agent's self-monitoring and the user's oversight. The output
"looks right" — it just isn't what was needed.

## The Mechanics of Drift

Drift typically follows a predictable pattern:

```
Step 1: Clear intent established
Step 2: Minor interpretation choice (reasonable)
Step 3: Sub-problem discovered
Step 4: Sub-problem becomes interesting → attention shifts
Step 5: Solution to sub-problem requires new assumption
Step 6: New assumption opens new design space
Step 7: Agent is now solving a different problem entirely
```

The critical transition happens between Steps 3 and 4. When a sub-problem captures
attention, the agent begins optimizing for the sub-problem instead of the original goal.

## Drift Detection Checkpoints

### Checkpoint A: The Re-Read Test

Every 3-4 tool calls, re-read the user's original message. Not your summary — their
actual words. Ask yourself:

- If I showed the user what I'm doing right now, would they say "yes, that's what I wanted"?
- Or would they say "wait, why are you doing that?"

If there's any doubt, you've drifted.

### Checkpoint B: The Scope Inventory

List everything you've created, modified, or planned. For each item, answer:

- Did the user ask for this? (Explicitly or clearly implied)
- If not, why am I doing it?
- If I removed this item, would the user's actual need still be met?

Anything that fails all three questions is scope creep, not drift — but scope creep
is drift's cousin and equally dangerous.

### Checkpoint C: The Complexity Ratio

Compare the complexity of your solution to the complexity of the request.

| Request Complexity | Appropriate Solution Complexity |
|---|---|
| "Fix this typo" | 1 file change |
| "Add a button" | Small component + integration |
| "Build me a dashboard" | Multiple files, moderate architecture |
| "Design a system" | Significant architecture, multiple components |

If your solution complexity significantly exceeds what the request warrants, either:
- You've discovered genuine complexity (surface it to the user), or
- You've drifted into over-engineering (pull back)

### Checkpoint D: The Assumption Audit

List your current operating assumptions. Compare to the assumptions you identified at
Gate 1 (intake). New assumptions that appeared during execution are drift indicators —
they mean you've moved into territory the original analysis didn't cover.

For each new assumption: Is it necessary? Is it verified? Does the user know about it?

## Drift Correction Protocol

When you detect drift:

### Mild Drift (still aligned, just expanded)
1. Acknowledge internally that you've expanded scope
2. Complete the current atomic unit of work
3. Return to the original intent
4. Note the expansion — mention it to the user if relevant

### Moderate Drift (solving adjacent problem)
1. Stop current work
2. Re-anchor to original intent
3. Evaluate whether the adjacent problem needs solving
4. If yes → ask the user before proceeding
5. If no → discard the tangent and return

### Severe Drift (solving wrong problem entirely)
1. Stop immediately
2. Acknowledge to the user: "I want to make sure I'm on track with what you need."
3. Restate your understanding of their goal
4. Ask for confirmation before continuing
5. If you've produced work product, assess whether any of it is salvageable

## Drift-Prone Contexts

Be especially vigilant in these situations:

- **Long tasks** — More steps = more opportunities to drift
- **Vague requirements** — Ambiguity is drift fuel
- **Interesting sub-problems** — Intellectual curiosity is the enemy of focus
- **Refactoring** — "While I'm here, I might as well..." is the drift mantra
- **Error recovery** — Fixing one thing often leads to "fixing" adjacent things
- **Multiple files/systems** — Each context switch is a drift opportunity

## The Intent Anchor Pattern

To combat drift, maintain an **intent anchor** — a one-sentence statement of the user's
goal that you can reference at any point. Write it mentally at Gate 1 and check against
it at every checkpoint.

**Format:** "[User] needs [outcome] so that [purpose]."

**Examples:**
- "User needs a PPTX summarizing Q3 results so that they can present to the board."
- "User needs a bug fix in the auth module so that login works on Safari."
- "User needs a sanity-check skill so that Claude projects maintain quality under pressure."

If your current work doesn't serve the intent anchor, you've drifted.
