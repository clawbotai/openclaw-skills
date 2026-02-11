# Master QA Skill

> Comprehensive quality assurance engineering and leadership skill. Covers strategy, automation, infrastructure, and team processes.

---

## 1. QA Strategy & Philosophy

### Shift-Left Testing
- Integrate testing from requirements/design phase, not after development
- Participate in story refinement: identify edge cases, acceptance criteria gaps, testability concerns
- Write test scenarios **before** implementation (BDD-style Given/When/Then)
- Review PRs for testability, not just correctness

### Testing Pyramid
Maintain the right ratio of tests by speed and scope:

```
        /  E2E  \          (~5-10%) — Critical user journeys only
       / Integration \      (~20-30%) — API contracts, service interactions
      /    Unit Tests   \   (~60-70%) — Fast, isolated, high coverage
```

- **Unit**: Pure logic, edge cases, error paths. Fast, deterministic, no I/O.
- **Integration**: Database queries, API calls, message queues. Use testcontainers/docker.
- **E2E**: Real browser/device. Only happy paths + critical flows. Expensive — be selective.

### Quality Gates
- PR merge: unit + integration pass, coverage ≥ threshold (e.g., 80% lines, 70% branches)
- Staging deploy: E2E smoke suite passes
- Production deploy: canary metrics (error rate, latency p99) within bounds
- Block merges on: coverage regression, new critical/high severity bugs, accessibility violations

---

## 2. Test Automation

### Frameworks & Tools

| Layer | Recommended | Alternatives |
|-------|------------|--------------|
| Unit (JS/TS) | Vitest | Jest |
| Unit (Python) | pytest | unittest |
| Unit (Go) | testing + testify | — |
| Unit (Java) | JUnit 5 + AssertJ | TestNG |
| Integration | Testcontainers | docker-compose fixtures |
| API/Contract | Pact, Supertest | REST Assured, Dredd |
| E2E Browser | Playwright | Cypress, WebdriverIO |
| Mobile | Detox, Maestro | Appium |
| Performance | k6 | Artillery, Locust, Gatling |
| Visual Regression | Playwright screenshots | Percy, Chromatic, BackstopJS |
| Accessibility | axe-core, Playwright a11y | pa11y, Lighthouse CI |
| Mutation | Stryker (JS), mutmut (Python) | PIT (Java) |

### Playwright Best Practices
```typescript
// Use locators, not selectors
page.getByRole('button', { name: 'Submit' })  // ✅
page.locator('#btn-submit')                     // ❌ fragile

// Use web-first assertions (auto-waiting)
await expect(page.getByText('Success')).toBeVisible()

// Isolate tests: each test gets fresh context
test.describe('checkout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/cart')
  })
})

// Use API to set up state, not UI
await request.post('/api/seed', { data: testFixture })

// Tag tests for selective execution
// @smoke @regression @critical
```

### Cypress Best Practices
```javascript
// Use data-testid attributes
cy.get('[data-testid="submit-btn"]')

// Never use cy.wait(ms) — use assertions
cy.get('.results').should('have.length.greaterThan', 0)

// Use cy.intercept for network control
cy.intercept('POST', '/api/orders', { fixture: 'order.json' }).as('createOrder')
cy.get('[data-testid="place-order"]').click()
cy.wait('@createOrder')

// Use custom commands for reuse
Cypress.Commands.add('login', (user) => {
  cy.session(user.email, () => {
    cy.request('POST', '/api/auth', user)
  })
})
```

---

## 3. Specialized Testing Types

### Contract Testing (Pact)
- **Consumer-driven**: Consumer defines expected interactions → Provider verifies
- Run consumer tests in CI → publish pact to Pact Broker
- Provider verification runs against published pacts
- Use `can-i-deploy` check before deploying any service
- Eliminates need for complex integration environments

```bash
# CI pipeline
pact-broker can-i-deploy --pacticipant MyService --version $GIT_SHA --to production
```

### Mutation Testing
- Validates test suite quality by injecting faults (mutants) into source code
- If tests still pass → mutant survived → test gap found
- Target: ≥80% mutation score on critical business logic
- Run weekly or on PRs touching core modules (expensive — don't run on everything)

```bash
# Stryker (JS/TS)
npx stryker run --mutate 'src/core/**/*.ts'
```

### Property-Based Testing
- Generate random inputs to find edge cases humans miss
- Use for: parsers, serializers, algorithms, data transformations
- Tools: fast-check (JS), Hypothesis (Python), jqwik (Java)

```typescript
import fc from 'fast-check'
test('encode/decode roundtrip', () => {
  fc.assert(fc.property(fc.string(), (s) => {
    expect(decode(encode(s))).toBe(s)
  }))
})
```

### Visual Regression Testing
- Capture screenshots of UI components/pages, compare against baselines
- Integrate into PR workflow: visual diff review before merge
- Use Playwright's built-in: `await expect(page).toHaveScreenshot('name.png', { maxDiffPixelRatio: 0.01 })`
- For component-level: Chromatic (Storybook) or Percy
- Update baselines intentionally, never auto-accept

### Accessibility Testing (WCAG)
- Automate what you can (~30-40% of WCAG issues): axe-core in CI
- Manual audit for the rest: keyboard navigation, screen reader, color contrast
- Target: WCAG 2.1 AA minimum
- Integrate axe into Playwright:

```typescript
import AxeBuilder from '@axe-core/playwright'
test('a11y check', async ({ page }) => {
  await page.goto('/dashboard')
  const results = await new AxeBuilder({ page }).analyze()
  expect(results.violations).toEqual([])
})
```

### Performance Testing
- **Load testing**: Expected traffic patterns (k6 scenarios)
- **Stress testing**: Find breaking points
- **Soak testing**: Memory leaks, resource exhaustion over time
- **Spike testing**: Sudden traffic bursts
- Run in CI against staging (not production) with defined SLOs

```javascript
// k6 example
import http from 'k6/http'
import { check, sleep } from 'k6'

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // ramp up
    { duration: '5m', target: 100 },  // sustain
    { duration: '2m', target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
}

export default function () {
  const res = http.get('https://staging.example.com/api/health')
  check(res, { 'status 200': (r) => r.status === 200 })
  sleep(1)
}
```

### Chaos Engineering
- Inject failures in controlled environments to validate resilience
- Start small: kill a pod, add latency, block a dependency
- Tools: Chaos Monkey, Litmus, Gremlin, Toxiproxy
- Prerequisites: observability, runbooks, rollback capability
- Always have a kill switch and run during business hours initially

---

## 4. Test Infrastructure & CI

### CI Test Orchestration
```yaml
# Parallel pipeline structure
stages:
  - lint-and-static-analysis    # seconds
  - unit-tests                   # < 2 min (parallelized by module)
  - integration-tests            # < 5 min (testcontainers, parallel)
  - contract-tests               # < 2 min
  - e2e-smoke                    # < 10 min (critical paths only)
  - e2e-full                     # < 30 min (nightly or pre-release)
  - performance                  # scheduled, not per-PR
```

- **Parallelize**: Split test suites across workers (Playwright sharding, Jest `--shard`)
- **Cache**: Dependencies, Docker layers, test fixtures
- **Fail fast**: Run fastest tests first; abort on first failure in PR checks
- **Selective execution**: Only run tests affected by changed files (nx affected, jest `--changedSince`)

### Flaky Test Detection & Management
- Track test reliability: pass rate per test over rolling window
- Auto-quarantine tests below threshold (e.g., <98% pass rate)
- Quarantined tests: still run but don't block pipeline; create ticket for fix
- Common causes: timing dependencies, shared state, network calls, date/time
- Fixes: explicit waits/assertions, test isolation, deterministic data, mock time

```bash
# Example: track flaky tests
# Store results in DB, flag tests that failed then passed on retry
# Dashboard: test name, pass rate, last flake date, owner
```

### Test Data Management
- **Factories**: Generate test data programmatically (factory-bot pattern)
- **Fixtures**: Static data for deterministic scenarios (JSON/YAML files)
- **Seeding**: API-based setup/teardown, not UI-driven
- **Isolation**: Each test creates its own data; never depend on shared state
- **Sensitive data**: Use fakers (faker.js, Faker), never real PII in tests
- **Database**: Use transactions + rollback, or ephemeral databases per test suite

### Coverage Gates
- Enforce in CI: fail PR if coverage drops below threshold
- Track trends: coverage should increase or stay flat over time
- Focus on meaningful coverage: branch coverage > line coverage
- Exclude generated code, config files, type definitions
- Tools: Istanbul/nyc (JS), coverage.py (Python), JaCoCo (Java)

```bash
# Example threshold enforcement
nyc check-coverage --branches 70 --lines 80 --functions 80
```

---

## 5. Test Observability

- **Structured test results**: JUnit XML / JSON reports in CI
- **Dashboards**: Test pass rate, duration trends, flaky test leaderboard, coverage trends
- **Alerting**: Notify on: coverage drops, new flaky tests, test suite duration regression
- **Distributed tracing in tests**: Correlate test failures with service traces (OpenTelemetry)
- **Test impact analysis**: Map tests to code paths; run only affected tests
- Tools: Allure, ReportPortal, Datadog CI Visibility, Buildkite Analytics

---

## 6. AI-Assisted Testing

- **Test generation**: Use LLMs to draft unit tests from source code (review & refine, don't blindly merge)
- **Test maintenance**: AI-assisted selector updates when UI changes
- **Root cause analysis**: Feed failure logs + traces to LLM for diagnosis
- **Exploratory testing**: AI-driven crawlers (e.g., QA Wolf, Meticulous)
- **Risk assessment**: Use change analysis to prioritize which tests to run
- **Caveat**: AI-generated tests need human review for meaningful assertions and edge cases

---

## 7. QA Leadership & Process

### Test Planning
- Create test plans per epic/feature: scope, approach, risks, environments, data needs
- Risk-based testing: prioritize by business impact × likelihood of failure
- Define exit criteria before testing begins

### Bug Management
- Severity: Critical (blocking) / High (major feature broken) / Medium (workaround exists) / Low (cosmetic)
- Bug report template:

```markdown
## Bug Report
**Summary**: [one-line description]
**Severity**: Critical | High | Medium | Low
**Environment**: [browser, OS, device, API version]
**Steps to Reproduce**:
1. ...
2. ...
**Expected**: ...
**Actual**: ...
**Evidence**: [screenshots, logs, video, network trace]
**Workaround**: [if any]
```

### Metrics & Reporting
- **Escaped defects**: Bugs found in production (trend should decrease)
- **Defect density**: Bugs per KLOC or per feature
- **Test automation ratio**: Automated / (Automated + Manual) — target ≥80%
- **Mean time to detect (MTTD)**: How fast bugs are caught
- **Test suite health**: Pass rate, duration, flaky rate
- **Coverage trends**: Over time, by module

### Release Readiness
- Checklist: all critical/high bugs resolved, regression suite green, performance baselines met, a11y audit passed, security scan clean, stakeholder sign-off
- Go/no-go decision criteria defined upfront

### Team Practices
- Test reviews: review test code with same rigor as production code
- Knowledge sharing: test patterns catalog, brown bags on testing techniques
- On-call rotation for test infrastructure
- Retrospectives: include test effectiveness as a topic

---

## 8. Templates

### Test Plan Template
```markdown
# Test Plan: [Feature/Epic Name]

## Scope
- In scope: ...
- Out of scope: ...

## Approach
- Unit: [what's covered]
- Integration: [services/APIs tested]
- E2E: [user journeys]
- Non-functional: [perf, a11y, security]

## Risks
| Risk | Mitigation |
|------|-----------|
| ... | ... |

## Environments
- CI: automated suites
- Staging: E2E, performance
- Production: smoke, canary

## Test Data
- Source: factories / fixtures / seeded via API
- Sensitive data handling: [approach]

## Schedule
- Test development: [dates]
- Execution: [dates]
- Exit criteria: [define]
```

### E2E Test Structure
```
tests/
├── e2e/
│   ├── fixtures/          # Test data, auth states
│   ├── pages/             # Page Object Models
│   ├── helpers/           # Shared utilities
│   ├── smoke/             # Critical path (~5 min)
│   ├── regression/        # Full suite (~30 min)
│   └── playwright.config.ts
├── integration/
│   ├── api/               # API integration tests
│   └── db/                # Database integration tests
└── unit/                  # Co-located with source (preferred)
```

---

## Usage

When asked to do QA work:
1. **Assess**: What type of testing is needed? What exists already?
2. **Plan**: Define approach using testing pyramid, risk-based prioritization
3. **Implement**: Write tests following the patterns and best practices above
4. **Integrate**: Ensure CI pipeline runs tests at the right stage
5. **Monitor**: Set up observability, track metrics, manage flaky tests
6. **Improve**: Continuously refine coverage, speed, and reliability
