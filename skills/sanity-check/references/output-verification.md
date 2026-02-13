# Output Verification Protocol

## Purpose

This is the final gate before delivery. Everything you've built passes through here.
The goal is to catch what execution missed: fabrications, missing pieces, unspoken
uncertainties, and irreversible actions.

## The Verification Checklist

### 1. Delivery Match Audit

**Question:** Does the output actually satisfy the original request?

Walk through the user's request clause by clause:
- For each thing they asked for → confirm it's present in the output
- For each thing present in the output → confirm they asked for it
- Any mismatch is either a gap (missing) or bloat (unrequested)

**Common miss:** The user asked for X "with" Y, and you delivered X but forgot Y.
This happens when Y seemed like a minor qualifier but was actually important.

### 2. Hallucination Scan

This is the most critical check. Hallucinations are confident-sounding fabrications
that the user has no reason to question.

**Scan for these specific hallucination vectors:**

| Vector | What to Check | How to Verify |
|--------|--------------|---------------|
| **Library/Package names** | Did I reference a real package? | Check the package exists (npm, pip, etc.) |
| **API endpoints** | Did I use a real endpoint? | Check documentation or actual URL |
| **Version numbers** | Did I cite a specific version? | Verify it exists |
| **Configuration values** | Did I suggest specific config? | Verify against docs |
| **File paths** | Did I reference files? | Verify they exist on the filesystem |
| **Function signatures** | Did I use correct params? | Check actual API/docs |
| **Statistics/Numbers** | Did I cite specific data? | Can I source it? |
| **Historical claims** | Did I state something happened? | Can I verify it? |
| **Error messages** | Did I predict specific errors? | Are they real error messages? |
| **Compatibility claims** | Did I say X works with Y? | Is this verified? |

**The Fabrication Test:** For each specific claim in your output, ask: "How do I know this?"
- If the answer is "I read it in a file/doc" → Safe
- If the answer is "I'm very confident from training" → Probably safe, note if high-stakes
- If the answer is "It seems right" → **DANGER. Verify or qualify.**
- If the answer is "I don't know, I just generated it" → **HALLUCINATION. Remove or fix.**

### 3. Uncertainty Disclosure

Honest uncertainty is not a weakness — it's a feature. Users can handle "I'm not sure about X"
far better than they can handle discovering X was wrong after relying on it.

**Rules:**
- If you're uncertain about something important → say so explicitly
- If you've made a judgment call → flag it as your judgment, not fact
- If there are multiple valid approaches → mention the alternatives briefly
- If the output works but has known limitations → state them

**Format for uncertainty:**
- "Note: I used [approach] here, but [alternative] might be better if [condition]."
- "I haven't verified [specific thing] — please confirm before relying on it."
- "This should work for [common case], but may need adjustment for [edge case]."

### 4. Reversibility Assessment

Before delivering, assess what happens if the output is wrong or unwanted.

| Reversibility Level | Description | Action Required |
|---|---|---|
| **Fully reversible** | User can undo with no consequences | Deliver normally |
| **Mostly reversible** | Undo is possible but requires effort | Note this to user |
| **Partially reversible** | Some effects cannot be undone | Warn user explicitly |
| **Irreversible** | Cannot be undone at all | Require explicit confirmation |

**Examples of irreversible actions:**
- Deleting files without backup
- Publishing content to public platforms
- Sending emails or messages
- Modifying production databases
- Overwriting files without preserving originals

### 5. The Final Smell Test

After all formal checks, do one gut check:

- If a senior engineer reviewed this output, what would they question?
- If this output causes a problem at 3 AM, is there enough context to debug it?
- Am I proud of this work, or am I shipping it because I'm "done"?

If anything feels off, investigate before delivering. The instinct that something
isn't right is usually correct.

## Post-Delivery Obligations

After delivering output, you're not done caring about quality:

- If the user reports issues, take them seriously — don't defend, diagnose
- If you discover you made an error, proactively flag it
- If you realize you were uncertain about something and didn't say so, say so now
