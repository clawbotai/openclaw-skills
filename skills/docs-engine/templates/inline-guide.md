# Guide to Writing Good Inline Documentation

How to add comments that actually help people understand your code.

---

## The Golden Rule

**Explain WHY, not WHAT.** The code already says what it does. Comments should explain the reasoning, context, and intent that the code can't express on its own.

```python
# Bad — tells us what we can already see:
x = x + 1  # increment x by 1

# Good — tells us WHY:
x = x + 1  # Account for zero-indexing when displaying to users
```

## When to Comment

**Always comment:**
- Business logic that isn't obvious from the code
- Workarounds and hacks (with links to issues/tickets)
- Magic numbers and regex patterns
- Non-obvious performance decisions
- API contracts and assumptions
- Security-sensitive code (why it's done this way)

**Don't comment:**
- Obvious code (`i++` doesn't need a comment)
- Code that should be rewritten to be clearer
- Closing braces (`} // end if` — just use shorter functions)

## Section Headers

Break long files into readable sections with headers:

```bash
# =============================================================================
# Database Connection Setup
# =============================================================================

# --- Connection pooling ---
# We use a pool of 10 connections because our load tests showed that
# anything less causes timeouts under peak traffic (see: PERF-142)
```

```javascript
// =============================================================================
// Authentication Middleware
// =============================================================================

// --- Token Validation ---
// Tokens expire after 24h. We check expiry BEFORE signature verification
// because expiry is cheaper to compute and rejects most invalid tokens.
```

## Function Documentation

Every public function should have a doc comment. Here's the pattern for each language:

### JavaScript/TypeScript (JSDoc)
```javascript
/**
 * Calculates the shipping cost based on weight and destination.
 *
 * Uses tiered pricing: domestic orders under 2kg get flat rate,
 * everything else uses the carrier's rate table.
 *
 * @param {number} weightKg - Package weight in kilograms
 * @param {string} country - ISO 3166-1 alpha-2 country code
 * @returns {number} Shipping cost in USD cents
 * @throws {Error} If country code is not recognized
 *
 * @example
 * calculateShipping(1.5, 'US')  // => 599 (flat rate)
 * calculateShipping(3.0, 'DE')  // => 2450 (carrier rate)
 */
```

### Python (Google style)
```python
def calculate_shipping(weight_kg: float, country: str) -> int:
    """Calculates shipping cost based on weight and destination.

    Uses tiered pricing: domestic orders under 2kg get flat rate,
    everything else uses the carrier's rate table.

    Args:
        weight_kg: Package weight in kilograms.
        country: ISO 3166-1 alpha-2 country code.

    Returns:
        Shipping cost in USD cents.

    Raises:
        ValueError: If country code is not recognized.

    Example:
        >>> calculate_shipping(1.5, 'US')
        599
    """
```

### Bash
```bash
# Calculate shipping cost based on weight and destination.
#
# Uses tiered pricing: domestic under 2kg = flat rate,
# everything else uses carrier rate table.
#
# Args:
#   $1 - Weight in kg (e.g., "1.5")
#   $2 - Country code (e.g., "US")
#
# Outputs:
#   Shipping cost in USD cents to stdout
#
# Returns:
#   0 on success, 1 if country code unknown
#
# Example:
#   cost=$(calculate_shipping 1.5 US)  # => 599
calculate_shipping() {
```

## Flow Narrative

For complex files, add a narrative at the top explaining the overall flow:

```python
"""
Order Processing Pipeline
=========================

This module handles the journey of an order from submission to fulfillment:

1. validate_order()  — Checks inventory, pricing, and customer data
2. process_payment() — Charges the customer (retries up to 3 times)
3. create_shipment() — Generates shipping label and notifies warehouse
4. send_confirmation() — Emails the customer with tracking info

If any step fails, the order moves to a "needs attention" queue
rather than silently failing. See: handle_failure().

The entire pipeline is idempotent — safe to retry on the same order ID.
"""
```

## Comment Maintenance

- Update comments when you change code (stale comments are worse than no comments)
- Delete comments that no longer apply
- If you find yourself writing a long comment, consider if the code should be refactored instead
