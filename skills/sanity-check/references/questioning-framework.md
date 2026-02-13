# Questioning Framework

When the sanity check identifies a risk, ambiguity, or concern — the quality of your questions determines whether you help or annoy.

## Core Principles

1. **Ask the question behind the question.** Don't ask what they want — ask what problem they're solving.
2. **Be specific.** "What database are you using?" not "Can you tell me more about your setup?"
3. **Explain WHY you're asking.** The user should understand the risk you've identified.
4. **Max 2-3 questions at once.** More than that is an interrogation, not a conversation.
5. **Frame around consequences, not preferences.** "What happens when X?" not "Do you want X?"
6. **Prefer "What happens when..." over "Do you want..."** — the former reveals constraints; the latter gets surface answers.

## Question Patterns

### Risk-Revealing Questions
Surface hidden risks the user may not have considered.

| Pattern | Example |
|---|---|
| "If [assumption] is wrong, this approach would [consequence]. Can you confirm [assumption]?" | "If the API rate-limits at 100 req/min, this batch approach would take 3 hours. Can you confirm the rate limit?" |
| "This will work for [A], but do you also need it to handle [B]?" | "This will work for single-tenant, but do you also need it to handle multi-tenant?" |
| "The fastest approach has a tradeoff: [tradeoff]. The alternative takes [time] but avoids [risk]. Which matters more?" | "The fastest approach stores credentials in env vars. The alternative uses a secret manager but needs 30 min setup. Which matters more?" |

### Clarifying Questions
Resolve ambiguity before it becomes wasted work.

| Pattern | Example |
|---|---|
| "When you say [X], do you mean [A] or [B]? The approach differs significantly." | "When you say 'real-time', do you mean sub-second latency or updates within a few minutes? The architecture differs significantly." |
| "What does 'done' look like for this? I want to make sure I'm building toward the right target." | Direct — calibrates the deliverable |
| "Who is the audience for this? That affects [specific decision]." | "Who is the audience for this doc? That affects the technical depth and terminology." |

### Chesterton's Fence Questions
Understand existing systems before changing them.

| Pattern | Example |
|---|---|
| "Before I change this — can you help me understand why it works this way?" | Non-judgmental. Doesn't assume the current way is wrong. |
| "I notice [existing pattern]. Is that intentional, or is it something we should change?" | Gives the user a chance to explain before you break something. |
| "What would break if we removed [X]?" | Forces enumeration of dependencies. |

### Consequence Questions
Make the user think through downstream effects.

| Pattern | Example |
|---|---|
| "If this works perfectly, what new problem does it create?" | Forces 2nd-order thinking. |
| "What happens to [downstream system] when this changes?" | Identifies integration points. |
| "If we do this and it's wrong, how hard is it to undo?" | Reversibility assessment. |

## Anti-Patterns

### Questions That Waste Time
- **Too vague:** "Can you tell me more?" → Ask about the specific thing you need.
- **Already answerable:** Don't ask the user what you could look up yourself.
- **Performative:** Don't ask questions just to seem thorough. Every question should serve a purpose.

### Questions That Annoy
- **Interrogation mode:** More than 3 questions in a row without doing any work.
- **Obvious questions:** Asking things the user already stated in their request.
- **Repeated questions:** Asking for info they already provided in this conversation.
- **Permission-seeking:** "Is it okay if I...?" for routine, reversible actions. Just do it.

### Questions That Mislead
- **Leading questions:** "You probably want X, right?" → Let them decide.
- **False binary:** "Should I do A or B?" when C exists and is better.
- **Buried lede:** Asking a minor question when the real issue is a major risk you should state directly.

## When NOT to Ask

Not every uncertainty requires a question. Skip questions when:
- You can verify the answer yourself (read a file, check a config, search the web)
- The uncertainty is minor and doesn't materially affect the approach
- You can make a reasonable default and state it: "I'm assuming X. Let me know if that's wrong."
- The user has shown they prefer action over discussion

## Delivery Format

When you do ask, structure it for easy response:

**Good:**
> I want to check two things before building this:
> 1. Are you targeting Node 18+ or do you need Node 16 compat? (Affects which APIs I can use)
> 2. Should this handle concurrent writes? (If yes, I'll add locking — adds ~30 min)

**Bad:**
> Before I start, I have some questions. First, I was wondering about the Node version you're using because that affects API compatibility. Also, I'm curious about whether there might be concurrent writes because that would change the architecture. And while I'm asking, do you have a preference on the testing framework?

The good version is scannable, numbered, and explains why each question matters.
