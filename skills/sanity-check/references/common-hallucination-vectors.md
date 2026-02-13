# Common Hallucination Vectors & Countermeasures

## Understanding Hallucination in Agent Contexts

Agent hallucinations are more dangerous than chatbot hallucinations because agents ACT
on their fabrications. A chatbot that hallucinates a fake API endpoint produces a wrong
answer. An agent that hallucinates a fake API endpoint writes code that calls it, which
the user then debugs for hours before discovering the endpoint doesn't exist.

Research identifies agent hallucinations as exhibiting "hallucinatory accumulation" —
where an early fabrication forces subsequent fabrications to maintain consistency,
creating an internally coherent but externally false chain of reasoning.

## The Top 10 Hallucination Vectors

### 1. Package/Library Names
**Pattern:** Generating a plausible-sounding package name that doesn't exist.
**Why it happens:** Training data contains thousands of package names; the model
pattern-matches to generate similar-sounding ones.
**Detection:** Before referencing any package, verify it exists.
**Countermeasure:** Use `pip search`, `npm search`, or check the package registry.
If you can't verify, say "I believe this package is called X — please verify."

### 2. API Endpoints and Parameters
**Pattern:** Generating API URLs, parameter names, or response formats from memory.
**Why it happens:** APIs change frequently; training data contains multiple versions.
**Detection:** If you're writing an API endpoint from memory, it's probably wrong.
**Countermeasure:** Check official documentation. If unavailable, explicitly flag:
"I've written this based on my understanding of the API — verify against current docs."

### 3. Version Numbers
**Pattern:** Citing specific version numbers (e.g., "v2.4.1") that don't exist.
**Why it happens:** Version numbers are semi-random; the model can't reliably recall them.
**Detection:** Any time you generate a specific version number, question it.
**Countermeasure:** Use "latest" or check the actual current version. Never fabricate.

### 4. Configuration Values
**Pattern:** Suggesting specific configuration settings, defaults, or magic numbers.
**Why it happens:** Configuration details are highly specific and poorly memorized.
**Detection:** If you're suggesting a config value, can you source it?
**Countermeasure:** Reference the documentation. If generating from memory, flag it.

### 5. File Paths and Directory Structures
**Pattern:** Referencing files or directories that don't exist on the actual system.
**Why it happens:** The model has seen many project structures and interpolates.
**Detection:** Before referencing any path, verify it exists in the actual filesystem.
**Countermeasure:** Use `ls`, `find`, or the `view` tool to confirm paths exist.

### 6. Error Messages
**Pattern:** Generating realistic-looking error messages for debugging guidance.
**Why it happens:** Error messages follow patterns; the model can generate convincing fakes.
**Detection:** If you're quoting an error message you didn't actually see, it's fabricated.
**Countermeasure:** Only reference error messages that actually appeared in output.

### 7. Function Signatures and Parameters
**Pattern:** Using wrong parameter names, types, or orderings for real functions.
**Why it happens:** APIs evolve; the model may have stale or merged knowledge.
**Detection:** If writing code that calls a specific function, verify the signature.
**Countermeasure:** Check docs, source code, or type definitions.

### 8. "I recall that..." Claims
**Pattern:** Stating factual claims with false confidence, prefaced by certainty language.
**Why it happens:** The model confuses "I generated a plausible response" with "I know this."
**Detection:** Any claim you preface with confident language — pause and assess.
**Countermeasure:** Apply the confidence calibration from SKILL.md § 1.6.

### 9. Cross-Contamination Between Similar Tools
**Pattern:** Mixing up syntax, features, or behavior between similar tools.
(e.g., React vs Vue patterns, PostgreSQL vs MySQL syntax, npm vs yarn commands)
**Why it happens:** Similar tools share vocabulary; the model blends them.
**Detection:** When working with tool-specific syntax, verify you're using the right one.
**Countermeasure:** Confirm which specific tool/framework is in use before writing code.

### 10. "Best Practice" Fabrication
**Pattern:** Stating something is a "best practice" or "industry standard" when it isn't.
**Why it happens:** The model learned many opinions stated as facts in training data.
**Detection:** If you claim something is a best practice, can you source it?
**Countermeasure:** Present recommendations as recommendations, not universal truths.

## The Self-Verification Protocol

When you suspect you might be hallucinating, run this protocol:

### Step 1: Isolate the Claim
Identify the specific factual claim that feels uncertain.

### Step 2: Source Check
Can you point to WHERE you know this from?
- A file you read → probably fine
- Documentation you consulted → probably fine
- "Training knowledge" → proceed with caution
- "It seems right" → HIGH RISK. Verify or qualify.

### Step 3: Consistency Check
Does this claim align with everything else you know about this topic?
If it contradicts something, one of them is wrong.

### Step 4: Plausibility Check
Would an expert in this domain agree with this claim?
If you can imagine an expert saying "actually, that's not quite right" — investigate.

### Step 5: Decide
- **Verified:** Use the claim confidently
- **Unverified but plausible:** Use with qualification ("I believe...", "Please verify...")
- **Uncertain:** Don't use. Find the answer or acknowledge the gap.
- **Likely wrong:** Remove it immediately

## The "Phantom Specificity" Red Flag

The single strongest signal that you're hallucinating is **phantom specificity** — when
your output contains very specific details (exact numbers, precise names, particular
versions) that you didn't derive from a source.

**Examples of phantom specificity:**
- "The latency was reduced by 43%" (where did 43 come from?)
- "Use the `--optimize-level=3` flag" (does that flag exist?)
- "This was introduced in v3.2.1" (can you verify?)
- "The default buffer size is 8192" (source?)

When you notice phantom specificity in your own output, treat it as a hallucination
until proven otherwise. Real knowledge comes with sources. Fabrications come with
confidence.

## Cultural Countermeasures

Beyond specific checks, cultivate these habits:

1. **Prefer general over specific** when you can't verify specifics
2. **Say "I think" instead of "it is"** when you're not certain
3. **Check before you cite** — never reference something you haven't verified
4. **When in doubt, ask** — the user prefers a question to a fabrication
5. **Verify what you build** — test code, check files exist, validate outputs
