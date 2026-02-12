# master-payments

> Complete payment processing, billing automation, and revenue management. Covers Stripe Payment Intents/PaymentElement, Stripe Connect (Standard/Express/Custom), subscription lifecycle, usage-based/hybrid billing, dunning, proration, invoicing, tax automation, multi-currency, PCI DSS v4.0 compliance, SCA/3DS2, fraud prevention, webhook verification, idempotency patterns, revenue recognition (ASC 606), and reconciliation.

---

## 1. Payment Integration Fundamentals

### Payment Intents API (Stripe)

```javascript
// Server-side: Create PaymentIntent
const paymentIntent = await stripe.paymentIntents.create({
  amount: 2000, // cents
  currency: 'usd',
  automatic_payment_methods: { enabled: true },
  metadata: { order_id: 'ord_123' },
  idempotency_key: `pi_${orderId}_${attempt}`,
});

// Return client_secret to frontend
```

```javascript
// Client-side: PaymentElement (recommended over CardElement)
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';

function CheckoutForm() {
  const stripe = useStripe();
  const elements = useElements();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: 'https://example.com/success' },
    });
    if (error) handleError(error);
  };

  return (
    <form onSubmit={handleSubmit}>
      <PaymentElement />
      <button type="submit">Pay</button>
    </form>
  );
}
```

### Payment Methods

| Method | Use Case | SCA Required |
|--------|----------|-------------|
| Cards (Visa/MC/Amex) | Global default | Yes (EU/UK) |
| ACH Direct Debit | US recurring/B2B | No |
| SEPA Direct Debit | EU recurring | No |
| Bank redirects (iDEAL, Bancontact) | EU one-time | Built-in |
| Wallets (Apple Pay, Google Pay) | Mobile/web checkout | Built-in |
| BNPL (Klarna, Afterpay) | Higher conversion | Built-in |
| Wire/invoice | B2B enterprise | No |

### Idempotency

```javascript
// Always use idempotency keys for mutations
const charge = await stripe.charges.create(
  { amount: 1000, currency: 'usd', source: 'tok_xxx' },
  { idempotencyKey: `charge_${orderId}` }
);

// Key generation pattern: {operation}_{entity_id}_{version/attempt}
// Keys expire after 24h on Stripe
// Store keys in DB to prevent regeneration on retry
```

**Rules:**
- Every POST/mutation gets an idempotency key
- Keys must be deterministic (same input → same key)
- Store the key→result mapping server-side for at-least-once delivery
- Never reuse keys across different operations

---

## 2. Stripe Connect

### Account Types

| Type | Onboarding | Dashboard | Payout Control | Best For |
|------|-----------|-----------|---------------|----------|
| **Standard** | Stripe-hosted | Full Stripe dashboard | Stripe manages | Marketplaces (low control) |
| **Express** | Stripe-hosted (simplified) | Limited dashboard | Stripe manages | Platforms, gig economy |
| **Custom** | You build it | None (you build) | You manage | Full white-label |

### Payment Flows

```javascript
// Direct charge (Standard accounts)
const charge = await stripe.paymentIntents.create({
  amount: 10000,
  currency: 'usd',
  application_fee_amount: 1000, // platform fee
}, { stripeAccount: 'acct_connected' });

// Destination charge (Express/Custom)
const charge = await stripe.paymentIntents.create({
  amount: 10000,
  currency: 'usd',
  transfer_data: {
    destination: 'acct_connected',
    amount: 9000, // connected account receives this
  },
});

// Separate charges and transfers (most flexible)
const payment = await stripe.paymentIntents.create({
  amount: 10000, currency: 'usd',
});
const transfer = await stripe.transfers.create({
  amount: 9000,
  currency: 'usd',
  destination: 'acct_connected',
  transfer_group: 'order_123',
});
```

### Onboarding

```javascript
// Create connected account
const account = await stripe.accounts.create({
  type: 'express',
  country: 'US',
  capabilities: { card_payments: { requested: true }, transfers: { requested: true } },
});

// Generate onboarding link
const link = await stripe.accountLinks.create({
  account: account.id,
  refresh_url: 'https://example.com/reauth',
  return_url: 'https://example.com/return',
  type: 'account_onboarding',
});
```

---

## 3. Subscription Lifecycle

### States

```
created → incomplete → active → past_due → canceled
                    ↗          ↘
              trialing      unpaid → canceled
                              ↓
                          paused (if enabled)
```

### Implementation

```javascript
// Create subscription
const subscription = await stripe.subscriptions.create({
  customer: 'cus_xxx',
  items: [{ price: 'price_monthly' }],
  payment_behavior: 'default_incomplete', // require payment confirmation
  payment_settings: {
    save_default_payment_method: 'on_subscription',
  },
  expand: ['latest_invoice.payment_intent'],
  trial_period_days: 14,
});

// Upgrade/downgrade (proration)
await stripe.subscriptions.update('sub_xxx', {
  items: [{ id: 'si_xxx', price: 'price_annual' }],
  proration_behavior: 'create_prorations', // or 'none', 'always_invoice'
});

// Cancel
await stripe.subscriptions.update('sub_xxx', {
  cancel_at_period_end: true, // graceful
});
// or immediate:
await stripe.subscriptions.cancel('sub_xxx', {
  prorate: true,
  invoice_now: true,
});
```

### Proration Strategies

| Strategy | When | Effect |
|----------|------|--------|
| `create_prorations` | Default | Credit unused, charge new rate |
| `none` | Downgrades | Change takes effect next period |
| `always_invoice` | Upgrades | Invoice immediately |

---

## 4. Usage-Based & Hybrid Billing

### Metered Billing

```javascript
// Create metered price
const price = await stripe.prices.create({
  currency: 'usd',
  recurring: { interval: 'month', usage_type: 'metered' },
  unit_amount: 10, // $0.10 per unit
  product: 'prod_xxx',
});

// Report usage (aggregate or set)
await stripe.subscriptionItems.createUsageRecord('si_xxx', {
  quantity: 100,
  timestamp: Math.floor(Date.now() / 1000),
  action: 'increment', // or 'set'
});
```

### Tiered Pricing

```javascript
const price = await stripe.prices.create({
  currency: 'usd',
  recurring: { interval: 'month' },
  billing_scheme: 'tiered',
  tiers_mode: 'graduated', // or 'volume'
  tiers: [
    { up_to: 1000, unit_amount: 50 },    // first 1000: $0.50/unit
    { up_to: 10000, unit_amount: 30 },   // next 9000: $0.30/unit
    { up_to: 'inf', unit_amount: 10 },   // rest: $0.10/unit
  ],
  product: 'prod_xxx',
});
```

### Hybrid Model (Base + Usage)

```javascript
// Subscription with multiple items
const subscription = await stripe.subscriptions.create({
  customer: 'cus_xxx',
  items: [
    { price: 'price_base_monthly' },      // flat $49/mo
    { price: 'price_api_calls_metered' },  // + $0.001/call
    { price: 'price_storage_metered' },    // + $0.10/GB
  ],
});
```

---

## 5. Dunning & Failed Payment Recovery

### Retry Schedule

```javascript
// Stripe Smart Retries (recommended) — ML-optimized timing
// Or configure manual schedule in Dashboard:
// Retry 1: 3 days after failure
// Retry 2: 5 days after retry 1
// Retry 3: 7 days after retry 2
// Mark uncollectible after final retry
```

### Dunning Workflow

```
payment_failed
  → Send email: "Payment failed, please update"
  → Wait 3 days, retry
  → Send email: "Second attempt failed"
  → Wait 5 days, retry
  → Send email: "Final notice — account will be suspended"
  → Wait 7 days, retry
  → If still failed: pause/cancel subscription
```

### Implementation

```javascript
// Webhook handler
app.post('/webhooks/stripe', async (req, res) => {
  const event = stripe.webhooks.constructEvent(
    req.body, req.headers['stripe-signature'], webhookSecret
  );

  switch (event.type) {
    case 'invoice.payment_failed':
      const invoice = event.data.object;
      const attempt = invoice.attempt_count;
      await sendDunningEmail(invoice.customer, attempt);
      if (attempt >= 4) await pauseAccount(invoice.customer);
      break;

    case 'invoice.payment_succeeded':
      await reactivateAccount(event.data.object.customer);
      break;

    case 'customer.subscription.deleted':
      await deprovisionAccess(event.data.object);
      break;
  }

  res.json({ received: true });
});
```

### Recovery Tactics

- **In-app banners** — more effective than email alone
- **Payment method update link** — Stripe hosted portal or custom
- **Involuntary churn reduction** — card updater, network tokens
- **Grace period** — maintain access during retry window
- **Win-back** — offer discount after cancellation

---

## 6. Invoicing

### Automatic vs Manual

```javascript
// Automatic invoice (subscription-generated)
// Stripe creates and finalizes automatically each billing period

// Manual/one-off invoice
const invoice = await stripe.invoices.create({
  customer: 'cus_xxx',
  collection_method: 'send_invoice', // or 'charge_automatically'
  days_until_due: 30,
  auto_advance: true,
});

await stripe.invoiceItems.create({
  customer: 'cus_xxx',
  invoice: invoice.id,
  amount: 50000,
  currency: 'usd',
  description: 'Consulting — January 2026',
});

await stripe.invoices.finalizeInvoice(invoice.id);
await stripe.invoices.sendInvoice(invoice.id);
```

### Invoice Lifecycle

```
draft → open → paid
              → void
              → uncollectible
```

### Credits & Refunds

```javascript
// Customer balance (credit)
await stripe.customers.createBalanceTransaction('cus_xxx', {
  amount: -5000, // negative = credit
  currency: 'usd',
  description: 'Goodwill credit',
});

// Refund
const refund = await stripe.refunds.create({
  payment_intent: 'pi_xxx',
  amount: 2000, // partial refund
  reason: 'requested_by_customer',
});
```

---

## 7. Tax Automation

### Stripe Tax

```javascript
const paymentIntent = await stripe.paymentIntents.create({
  amount: 10000,
  currency: 'usd',
  automatic_tax: { enabled: true },
  customer: 'cus_xxx', // must have address
});

// For subscriptions
const subscription = await stripe.subscriptions.create({
  customer: 'cus_xxx',
  items: [{ price: 'price_xxx' }],
  automatic_tax: { enabled: true },
});
```

### Tax Considerations

| Region | Tax Type | Rate | Threshold |
|--------|----------|------|-----------|
| US | Sales tax | Varies by state | Economic nexus (state-specific) |
| EU | VAT | 17-27% | €10K (One-Stop Shop) |
| UK | VAT | 20% | £85K |
| Canada | GST/HST | 5-15% | CAD $30K |
| Australia | GST | 10% | AUD $75K |

**Alternatives:** TaxJar, Avalara — for complex multi-jurisdiction or non-Stripe processors.

### Tax-Exempt Handling

```javascript
// Set customer tax exemption
await stripe.customers.update('cus_xxx', {
  tax_exempt: 'exempt', // 'none', 'exempt', 'reverse'
});

// Tax IDs
await stripe.customers.createTaxId('cus_xxx', {
  type: 'eu_vat',
  value: 'DE123456789',
});
```

---

## 8. Multi-Currency

### Strategy

```javascript
// Present prices in local currency
const price = await stripe.prices.create({
  product: 'prod_xxx',
  unit_amount: 4900,
  currency: 'eur', // create per-currency prices
  recurring: { interval: 'month' },
});

// Or use Stripe Adaptive Pricing (auto-converts)
```

### Settlement Currency

- Configure per-currency settlement in Stripe Dashboard
- Minimize FX fees by matching presentment and settlement currencies
- Use multi-currency payouts for Connect platforms

### Considerations

- **Rounding:** Always work in smallest currency unit (cents, pence)
- **Zero-decimal currencies:** JPY, KRW — amount is face value, not cents
- **Display:** Use `Intl.NumberFormat` for locale-aware formatting

---

## 9. PCI DSS v4.0 Compliance

### SAQ Levels

| Level | Integration | PCI Scope |
|-------|-----------|-----------|
| **SAQ A** | Stripe.js + Elements / Checkout | Minimal — card data never touches your server |
| **SAQ A-EP** | Custom form posting to Stripe | Medium — your page serves the form |
| **SAQ D** | Server-side card handling | Full — avoid this |

### Requirements (SAQ A)

- Use HTTPS everywhere
- No card data in logs, URLs, or error messages
- Keep Stripe.js loaded from `js.stripe.com` (never self-host)
- CSP headers restricting frame/script sources
- Quarterly vulnerability scans (if applicable)
- Annual self-assessment questionnaire

### Best Practices

- **Never** log, store, or transmit raw card numbers
- Use PaymentElement — handles SCA, card updates, multiple methods
- Tokenize everything — use `pm_` or `tok_` references only
- Server-side: only pass PaymentIntent IDs, never card details
- Rotate API keys periodically; restrict to minimum permissions

---

## 10. SCA / 3D Secure 2

### When Required

- **EU/UK:** Strong Customer Authentication required (PSD2)
- **Exemptions:** Low-value (<€30, cumulative <€100), low-risk (TRA), recurring after first, merchant-initiated

### Implementation

```javascript
// Stripe handles SCA automatically with PaymentIntents + PaymentElement
// For off-session payments:
const paymentIntent = await stripe.paymentIntents.create({
  amount: 2000,
  currency: 'eur',
  customer: 'cus_xxx',
  payment_method: 'pm_xxx',
  off_session: true,
  confirm: true,
});

// Handle authentication_required error
try {
  await stripe.paymentIntents.confirm('pi_xxx');
} catch (err) {
  if (err.code === 'authentication_required') {
    // Bring customer back on-session to authenticate
    await notifyCustomerToAuthenticate(err.payment_intent.id);
  }
}
```

### Optimization

- Request exemptions via `payment_method_options.card.request_three_d_secure: 'automatic'`
- Use Stripe Radar for TRA exemptions
- Store mandates for recurring SEPA/ACH

---

## 11. Fraud Prevention

### Stripe Radar

```javascript
// Radar rules (configured in Dashboard or API)
// Block if: risk_level = 'highest'
// Review if: risk_level = 'elevated'
// Allow if: metadata['trusted_customer'] = 'true'

// Custom Radar rules examples:
// Block cards from high-risk countries
// Block if velocity > 3 charges in 1 hour
// Review if amount > $500 and new customer
```

### Additional Measures

| Layer | Implementation |
|-------|---------------|
| **Velocity checks** | Rate limit by IP, customer, card fingerprint |
| **Address verification (AVS)** | Block on zip/address mismatch |
| **CVC check** | Always require; block on failure |
| **Device fingerprinting** | Stripe.js provides automatically |
| **3DS challenge** | Force for high-risk transactions |
| **Blocklists** | Email domains, IPs, BINs |
| **Manual review queue** | For flagged transactions |

### Chargeback Management

- Respond within deadline (usually 7-21 days)
- Include compelling evidence: logs, delivery proof, communication
- Track dispute rate — stay under 0.75% (Visa) / 1% (Mastercard)
- Use Stripe's dispute auto-response for clear-cut cases

---

## 12. Webhook Verification & Architecture

### Verification

```javascript
const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET;

app.post('/webhooks/stripe', express.raw({ type: 'application/json' }), (req, res) => {
  let event;
  try {
    event = stripe.webhooks.constructEvent(
      req.body,
      req.headers['stripe-signature'],
      endpointSecret
    );
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }

  // Process event idempotently
  await processWebhookIdempotently(event);
  res.json({ received: true });
});
```

### Idempotent Processing

```javascript
async function processWebhookIdempotently(event) {
  // Check if already processed
  const existing = await db.webhookEvents.findUnique({ where: { id: event.id } });
  if (existing?.processedAt) return; // already handled

  // Record receipt
  await db.webhookEvents.upsert({
    where: { id: event.id },
    create: { id: event.id, type: event.type, data: event.data, receivedAt: new Date() },
    update: {},
  });

  // Process
  await handleEvent(event);

  // Mark processed
  await db.webhookEvents.update({
    where: { id: event.id },
    data: { processedAt: new Date() },
  });
}
```

### Essential Webhook Events

| Event | Action |
|-------|--------|
| `checkout.session.completed` | Provision access |
| `invoice.payment_succeeded` | Confirm billing, send receipt |
| `invoice.payment_failed` | Dunning flow |
| `customer.subscription.updated` | Sync plan changes |
| `customer.subscription.deleted` | Deprovision |
| `charge.dispute.created` | Alert team, gather evidence |
| `payment_method.attached` | Update default method |

---

## 13. Revenue Recognition (ASC 606)

### Five-Step Model

1. **Identify the contract** — signed agreement, accepted terms
2. **Identify performance obligations** — distinct deliverables (license, support, setup)
3. **Determine transaction price** — fixed + variable consideration
4. **Allocate price** — standalone selling price per obligation
5. **Recognize revenue** — as obligations are satisfied (point-in-time or over time)

### SaaS Patterns

| Model | Recognition |
|-------|-------------|
| Monthly subscription | Ratably over the month |
| Annual subscription | Ratably over 12 months |
| Usage-based | As usage occurs |
| Setup/onboarding fee | Over expected customer life (if not distinct) or at delivery (if distinct) |
| Professional services | As delivered / milestones |

### Implementation

```javascript
// Stripe Revenue Recognition (add-on)
// Automatically generates deferred revenue schedules
// For manual tracking:
const revenueSchedule = {
  invoiceId: 'in_xxx',
  totalAmount: 120000, // $1,200 annual
  startDate: '2026-01-01',
  endDate: '2026-12-31',
  monthlyRecognition: 10000, // $100/month
  recognized: 0,
  deferred: 120000,
};
```

### Deferred Revenue

- Collected but unearned revenue = liability on balance sheet
- Recognize monthly as service is delivered
- Critical for annual/multi-year contracts
- Audit trail: link every revenue entry to invoice + obligation

---

## 14. Reconciliation

### Daily Reconciliation Process

1. **Fetch Stripe balance transactions** for the period
2. **Match against internal records** (orders, invoices, subscriptions)
3. **Flag discrepancies** — missing records, amount mismatches, duplicate charges
4. **Reconcile fees** — Stripe fees, Connect application fees, refunds
5. **Verify payouts** — bank deposits match expected amounts

### Automated Reconciliation

```javascript
async function dailyReconciliation(date) {
  const balanceTransactions = await stripe.balanceTransactions.list({
    created: { gte: startOfDay(date), lt: endOfDay(date) },
    limit: 100,
  });

  const discrepancies = [];

  for (const txn of balanceTransactions.data) {
    const internalRecord = await db.payments.findByStripeId(txn.source);
    if (!internalRecord) {
      discrepancies.push({ type: 'missing_internal', stripe: txn });
    } else if (internalRecord.amount !== txn.amount) {
      discrepancies.push({ type: 'amount_mismatch', stripe: txn, internal: internalRecord });
    }
  }

  if (discrepancies.length > 0) {
    await alertFinanceTeam(discrepancies);
  }

  return { processed: balanceTransactions.data.length, discrepancies: discrepancies.length };
}
```

### Key Metrics

- **Reconciliation rate** — % of transactions matched (target: 99.9%+)
- **Time to reconcile** — hours from transaction to match
- **Discrepancy rate** — unmatched transactions (investigate if >0.1%)
- **Payout accuracy** — bank deposits vs expected

---

## 15. Workflows

### New Payment Integration

1. Choose integration: Checkout (fastest), PaymentElement (flexible), Custom (full control)
2. Set up webhook endpoint with signature verification
3. Implement idempotent event processing
4. Add error handling for all payment states
5. Test with Stripe test mode and test cards
6. Verify PCI compliance level (SAQ A recommended)
7. Enable Radar rules for fraud prevention
8. Set up monitoring and alerts

### New Subscription Product

1. Create Product and Prices in Stripe
2. Implement subscription creation flow
3. Handle trial → active transition
4. Set up dunning for failed payments
5. Implement upgrade/downgrade with proration
6. Handle cancellation (graceful vs immediate)
7. Set up usage reporting if metered
8. Implement tax calculation
9. Test full lifecycle with test clocks

### Payment Issue Debugging

1. Check PaymentIntent status and last_payment_error
2. Review webhook delivery logs
3. Check Radar evaluation for blocks
4. Verify customer payment method validity
5. Check for SCA/3DS requirements
6. Review idempotency key usage
7. Check for rate limiting

---

## 16. Testing

### Stripe Test Cards

| Card | Behavior |
|------|----------|
| `4242424242424242` | Success |
| `4000000000003220` | 3DS2 required |
| `4000000000009995` | Decline (insufficient funds) |
| `4000000000000341` | Attaching succeeds, charge fails |
| `4000002500003155` | 3DS2 authentication fails |

### Test Clocks (Subscriptions)

```javascript
// Create test clock
const clock = await stripe.testHelpers.testClocks.create({
  frozen_time: Math.floor(Date.now() / 1000),
});

// Create customer on clock
const customer = await stripe.customers.create({
  test_clock: clock.id,
});

// Advance time to test billing cycles
await stripe.testHelpers.testClocks.advance(clock.id, {
  frozen_time: futureTimestamp,
});
```

### Checklist

- [ ] Successful payment (multiple methods)
- [ ] Failed payment handling
- [ ] 3DS authentication flow
- [ ] Webhook delivery and processing
- [ ] Idempotency (duplicate webhook handling)
- [ ] Subscription create/upgrade/downgrade/cancel
- [ ] Trial expiration
- [ ] Dunning flow (payment failure → retry → recovery/cancellation)
- [ ] Refund (full and partial)
- [ ] Multi-currency amounts
- [ ] Tax calculation accuracy
- [ ] Reconciliation matching
- [ ] Error states and edge cases
