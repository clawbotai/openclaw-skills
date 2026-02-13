# Output Verification Checklist

Run this before delivering any non-trivial output. The checks are ordered by impact — the first few catch the most common failures.

## Level 1: Delivery Match (Always Run)

- [ ] **Re-read the original request.** Not your interpretation — the user's actual words.
- [ ] **Enumerate what was asked for.** List each explicit deliverable.
- [ ] **Check each off against your output.** Is every requested item present?
- [ ] **Check for extras.** Is anything present that was NOT requested? If so, is it clearly marked as optional/bonus, or are you scope-creeping?
- [ ] **Format check.** Did the user specify a format? (file type, structure, naming convention) Does your output match?

## Level 2: Factual Integrity (Always Run)

- [ ] **File references.** Every file path you mention — does it exist? Did you verify?
- [ ] **Library/API references.** Every library, API, or tool you cited — is it real? Is the version current? Is the API signature correct?
- [ ] **Numbers and versions.** Any specific version numbers, port numbers, config values — are they verified or generated from memory?
- [ ] **Commands.** Every shell command, CLI invocation, or code snippet — would it actually run? Did you test it or are you assuming?
- [ ] **URLs.** Every URL you included — is it valid? Does it point where you say it does?

## Level 3: Uncertainty Disclosure (Run for complex/high-stakes output)

- [ ] **Confidence inventory.** For each major claim or recommendation — how confident are you? (verified / high / moderate / guessing)
- [ ] **Hedge where appropriate.** For moderate-confidence claims, add qualifiers: "I believe...", "This should work but verify...", "Based on my understanding..."
- [ ] **Unknown unknowns.** Are there aspects of this problem you don't have enough context to evaluate? Say so.
- [ ] **Edge cases.** What scenarios haven't you considered? Are there inputs, environments, or conditions that could break your solution?

## Level 4: Reversibility & Safety (Run when output involves actions)

- [ ] **Reversibility.** Can the user undo everything you've done/proposed? If not, did you warn them?
- [ ] **Destructive operations.** Did you use `trash` over `rm`? Did you back up before replacing?
- [ ] **External side effects.** Does your output trigger anything external? (emails, API calls, deployments, notifications)
- [ ] **Credential exposure.** Are there any secrets, tokens, or passwords in your output that shouldn't be there?
- [ ] **Permission changes.** Did you modify any permissions, access controls, or security settings?

## Level 5: Completeness & Usability (Run for delivered artifacts)

- [ ] **Self-contained.** Can the user use your output without asking follow-up questions? If not, did you explain what's missing?
- [ ] **Dependencies stated.** Are all prerequisites, dependencies, and setup steps documented?
- [ ] **Error handling.** If this is code — what happens when things go wrong? Are errors handled or do they crash silently?
- [ ] **Copy-paste ready.** If you provided commands or code — can the user copy-paste and run without editing? If not, are the placeholders obvious?

## Quick Version (for simple tasks)

When the task is straightforward, run the 4-question version:

1. Does this answer what was asked?
2. Is everything I stated actually true?
3. Am I uncertain about anything I didn't disclose?
4. Can the user undo this if needed?

## Common Output Failures

| Failure | Description | Prevention |
|---|---|---|
| **Phantom files** | Referencing files that don't exist | Verify every path with read/ls before citing |
| **Stale APIs** | Using deprecated or changed API signatures | Check docs or verify with a test call |
| **Wrong defaults** | Assuming default config values that differ by environment | State assumptions explicitly |
| **Silent truncation** | Output is incomplete but looks complete | Check if you addressed every part of the request |
| **Format mismatch** | Delivering markdown when they wanted JSON, or vice versa | Re-read the request for format cues |
