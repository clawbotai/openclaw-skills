# Common Hallucination Vectors

Hallucinations are not random — they cluster around specific categories where LLMs are most likely to generate plausible-sounding but fabricated information.

## High-Risk Categories

### 1. Version Numbers and Release Dates
**Risk:** Extremely high. LLMs routinely generate plausible but incorrect version numbers.

**Examples:**
- "Use React 19.2.1" (may not exist)
- "This was deprecated in Python 3.11" (may be wrong version)
- "Node.js 22 LTS released in October 2024" (plausible but unverified)

**Mitigation:** Never cite a specific version from memory. Check `package.json`, `pyproject.toml`, release notes, or official docs.

### 2. API Signatures and Parameters
**Risk:** Very high. APIs change frequently; training data is outdated.

**Examples:**
- Function parameter names that were renamed between versions
- Optional parameters that became required (or vice versa)
- Return types that changed
- Deprecated methods presented as current

**Mitigation:** Read the actual source code or official API docs. Never trust a function signature from memory for anything non-trivial.

### 3. File Paths and Directory Structures
**Risk:** High. LLMs generate "expected" paths that don't match reality.

**Examples:**
- "The config is at `~/.config/tool/config.yaml`" (might be `.toml`, or in a different directory)
- "Check `src/utils/helpers.js`" (file might not exist)
- "The log is at `/var/log/service/error.log`" (path differs by OS/distro)

**Mitigation:** Use `ls`, `find`, or `read` to verify paths before citing them. Never assume a file exists.

### 4. Configuration Options and Defaults
**Risk:** High. Config schemas change between versions and differ between tools.

**Examples:**
- "Set `max_connections: 100` in the config" (option might not exist or have a different name)
- "The default timeout is 30 seconds" (might be 60, or might vary by context)
- "Add this to your `tsconfig.json`" (option might require a specific TypeScript version)

**Mitigation:** Check the tool's actual config schema or documentation. Use `--help` flags.

### 5. Error Messages and Their Causes
**Risk:** Moderate-high. LLMs generate diagnostic reasoning that sounds authoritative but may be wrong.

**Examples:**
- "This error means X" (it might mean Y in this specific context)
- "This is caused by Z" (correlation, not causation)
- "Fix this by doing W" (fixes a different manifestation of the symptom)

**Mitigation:** Read the actual error message and trace it to the source. Don't pattern-match from training data.

### 6. URLs and Links
**Risk:** Moderate-high. URLs change, pages move, sites restructure.

**Examples:**
- Documentation links that return 404
- GitHub links to files that were moved or deleted
- Stack Overflow links that don't exist

**Mitigation:** If you cite a URL, verify it with `web_fetch` or note that you haven't verified it.

### 7. Performance Claims and Benchmarks
**Risk:** Moderate. LLMs generate plausible-sounding but fabricated performance numbers.

**Examples:**
- "This reduces latency by 40%"
- "Redis can handle 100K ops/sec" (depends heavily on configuration)
- "This approach is O(n log n)" (might be wrong for the specific implementation)

**Mitigation:** Don't cite specific performance numbers unless you have a source. Use qualifiers: "typically faster", "should reduce load".

### 8. Security Advisories and CVEs
**Risk:** High. LLMs fabricate CVE numbers and vulnerability descriptions.

**Examples:**
- "CVE-2024-XXXXX affects this library" (CVE may not exist)
- "This has a known XSS vulnerability" (may be confused with a similar library)
- Security best practices that are outdated or incorrect for the specific version

**Mitigation:** Never cite a specific CVE without verifying it. Use `web_search` to confirm. Reference official security advisories.

## Detection Heuristics

You are likely hallucinating when:

1. **You're generating from memory** rather than reading from a source
2. **The detail is very specific** (exact version, exact parameter name, exact URL)
3. **You feel confident** but can't point to where you learned it
4. **The information is time-sensitive** (versions, APIs, security advisories)
5. **You're filling a gap** — you need a detail to complete your response and one conveniently appears

## Response Protocol

When you detect a potential hallucination:

| Situation | Action |
|---|---|
| Can verify quickly (file read, web search) | Verify before including |
| Can't verify but low stakes | Include with qualifier: "I believe..." or "Please verify..." |
| Can't verify and high stakes | Don't include. Say you're not sure and suggest how to verify. |
| Caught after delivery | Immediately correct. Don't hope the user won't notice. |

## The "Source or Hedge" Rule

For every specific factual claim, you should be able to either:
1. **Point to a source** — "I verified this in [file/doc/search result]"
2. **Hedge appropriately** — "I believe this is correct but haven't verified"

If you can do neither, you're hallucinating. Remove the claim.
