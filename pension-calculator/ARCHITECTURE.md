# Pension Optimization Engine — Architecture

## What Exists Today

A functional MVP built iteratively with ~45 Python scripts, a Flask server, and a vanilla JS webapp. It works for specific test cases (Piedad, Francisco, Yaneth) but is not production-ready. The code is exploratory — lots of one-off debug scripts, hardcoded paths, and duplicated logic.

**What works:**
- PDF/Excel ingestion of Colpensiones labor histories (`extract_semanas.py`)
- Pension calculation under Ley 797 de 2003 (IBL, replacement rate, weeks)
- Client-side calculator with Tailwind UI (`calculator.js`, `app.js`)
- Reverse calculator (Goal Seeker): "I want $X pension, what must I contribute?"
- History Booster: ROI analysis of retroactive contribution increases
- Full burden calculator (pension + health + ARL)
- Freemium paywall concept ($350,000 COP unlock)

**What doesn't work:**
- No deployment (local Flask only)
- No auth, no payments, no user accounts
- Index.html is stored as a Google Doc (not real HTML)
- Python backend requires `pdfplumber`, `pandas`, `openpyxl` — heavy deps
- No tests beyond ad-hoc debug scripts
- IPC data only goes to early 2024
- Hardcoded week counts in `calculate_pension.py` (`weeks = 1823.43`)

---

## Domain Model

### Colombian Pension System (RPM — Colpensiones)

**Key concepts:**
- **SMMLV** — Salario Mínimo Mensual Legal Vigente (annual minimum wage table, 1980–2025)
- **IBC** — Ingreso Base de Cotización (contribution base income per period)
- **IBL** — Ingreso Base de Liquidación (average indexed salary for pension calculation)
- **Semanas** — Weeks contributed (360-day accounting: 1 month = 30 days, 1 week = 7 days)
- **Tasa de Reemplazo** — Replacement rate: `r = 65.5% - 0.5 × (IBL / SMMLV)`, plus 1.5% per 50 weeks over 1,300, capped at 80%, floor at 55%
- **IPC** — Consumer Price Index for salary indexation
- **Contribution rates** — evolved from 10% (1967) to 16% (2008+)
- **Pension eligibility** — minimum 1,300 weeks + age (57F/62M)
- **Indemnización Sustitutiva** — lump-sum payout if weeks < 1,300

**IBL calculation (the hard part):**
1. Take last 10 years of contribution history before liquidation date
2. For each month: sum all IBC from concurrent employers, cap at 25 × SMMLV
3. Index each month's salary by IPC ratio (IPC_final / IPC_initial)
4. Average = sum of indexed salaries / count of contributed months
5. Compare with lifetime average; use whichever is higher

**Data sources:**
- Colpensiones PDF: Summary table (employer, dates, salary, weeks, simultaneous) + Detailed table (monthly IBC, days contributed)
- Colpensiones Excel: Same data, cleaner format
- Item [26] "TOTAL SEMANAS" in PDF text — authoritative week count

---

## Proposed Architecture

### Principles
1. **Separate computation from presentation** — the pension math is a pure function library, not tangled with UI
2. **Move PDF parsing to the server** — `pdfplumber` requires Python; keep the client lightweight
3. **All calculations reproducible** — every result traces to input data + formula version
4. **Freemium from day one** — free tier validates data; premium unlocks optimization suite
5. **Mobile-first** — target audience uses phones, not desktops

### System Components

```
┌──────────────────────────────────────────────────┐
│                   Client (SPA)                    │
│  Tailwind CSS + Vanilla JS (or SvelteKit later)  │
│                                                   │
│  Upload PDF/Excel → See validation → Paywall →    │
│  Dashboard (weeks, IBL, pension, projections)     │
└─────────────────────┬────────────────────────────┘
                      │ REST API (JSON)
┌─────────────────────▼────────────────────────────┐
│              API Server (FastAPI)                  │
│                                                   │
│  POST /api/upload    → Parse PDF/Excel            │
│  POST /api/calculate → Run pension math           │
│  POST /api/optimize  → Goal seeker / booster      │
│  POST /api/unlock    → Payment verification       │
│  GET  /api/data      → SMMLV/IPC/rates tables     │
│                                                   │
│  Auth: magic-link email (no passwords)            │
│  Storage: SQLite (user sessions, calculations)    │
└─────────────────────┬────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────┐
│            Core Library (Python)                   │
│                                                   │
│  parser.py      — PDF/Excel → LaborHistory        │
│  calculator.py  — weeks, IBL, replacement rate     │
│  optimizer.py   — goal seeker, booster, burden     │
│  models.py      — data classes, validation         │
│  data/          — SMMLV, IPC, contribution rates   │
└──────────────────────────────────────────────────┘
```

### Data Flow

```
User uploads PDF
  → API receives file
  → parser.py extracts labor history (employer, dates, salary, weeks)
  → Returns structured JSON to client

Client displays validation
  → Total weeks, employer list, date ranges
  → "Verified" badge if Item [26] matches computed weeks
  → FREE — this is the hook

User clicks "Unlock Full Report" ($350,000 COP)
  → Payment via Stripe / MercadoPago / crypto
  → API marks session as premium

Premium dashboard loads
  → calculator.py computes IBL, replacement rate, estimated pension
  → optimizer.py runs goal seeker: "contribute $X/month for Y years → $Z pension"
  → optimizer.py runs history booster: "retroactive increase saves $W/month"
  → Full burden calculator: pension + health + ARL = true monthly cost
```

### Core Library Design

```python
# models.py
@dataclass
class LaborPeriod:
    employer_id: str
    employer_name: str
    start: date
    end: date
    salary: Decimal        # Last reported salary (IBC)
    weeks: Decimal         # Reported weeks
    simultaneous: Decimal  # Overlapping weeks to subtract
    total: Decimal         # Net weeks (authoritative from Colpensiones)

@dataclass  
class LaborHistory:
    periods: list[LaborPeriod]
    grand_total_weeks: Decimal  # Item [26] from PDF
    source: str                 # "pdf" | "excel"
    
@dataclass
class PensionResult:
    total_weeks: Decimal
    ibl: Decimal
    ibl_method: str           # "last_10_years" | "lifetime"
    replacement_rate: Decimal
    monthly_pension: Decimal
    smmlv_year: int
    eligible: bool
    weeks_remaining: Decimal  # to reach 1,300

@dataclass
class OptimizationScenario:
    target_pension: Decimal
    horizon_years: int
    required_monthly_ibc: Decimal
    total_cost: Decimal       # Including health + ARL
    roi_vs_baseline: Decimal
```

### API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/upload` | POST | none | Parse PDF/Excel, return structured history |
| `/api/validate` | POST | none | Compute weeks + basic stats (free tier) |
| `/api/calculate` | POST | premium | Full IBL + pension calculation |
| `/api/optimize/goal` | POST | premium | Reverse calc: target → required contribution |
| `/api/optimize/boost` | POST | premium | History booster simulation |
| `/api/optimize/burden` | POST | premium | Full burden (pension + health + ARL) |
| `/api/data/smmlv` | GET | none | SMMLV table |
| `/api/data/ipc` | GET | none | IPC series |
| `/api/unlock` | POST | none | Process payment, return session token |

### Deployment

**Option A — Cloudflare Pages + Workers (recommended):**
- Static frontend on CF Pages
- Python API as a standalone service (Fly.io / Railway — needs `pdfplumber`)
- CF can't run Python with native deps, so the API must be hosted separately

**Option B — Single VPS:**
- FastAPI serves both API and static files
- Docker container: Python 3.11 + pdfplumber + uvicorn
- Reverse proxy via Caddy/nginx with auto-TLS

**Option C — Hybrid:**
- CF Pages for frontend
- CF Workers for lightweight endpoints (SMMLV lookup, payment verification)
- Fly.io for the heavy PDF parsing endpoint only

**Recommendation:** Option C. Keep the frontend fast on CF's edge CDN. The PDF parsing is the only part that truly needs a Python runtime. Everything else (calculation, optimization) could run client-side in JS if we port the math — which already exists in `calculator.js`.

### Payment Integration

Colombian market → **MercadoPago** or **Stripe** (both support COP).

Flow:
1. User completes free validation
2. Clicks "Unlock" → redirected to payment page
3. On success → webhook sets session as premium
4. Premium endpoints check session token

Price: $350,000 COP (~$80 USD) one-time per report.

---

## Migration Plan

### Phase 1: Consolidate Core Library
Extract from the 45 scripts into clean modules:
- `parser.py` ← `extract_semanas.py` (the real logic, 358 lines)
- `calculator.py` ← `calculate_pension.py` + `calculator.js` (reconcile Python/JS)
- `optimizer.py` ← `solve_pension_gap.py` + `boost_history.py` + `calculate_full_burden.py`
- `models.py` ← new, typed data classes
- `data/` ← `data.json` (SMMLV, IPC, contribution rates) — keep as JSON, load at startup

### Phase 2: Build API
- FastAPI with the core library
- `/upload` endpoint replaces Flask `server.py`
- Add input validation, error handling, structured responses
- Dockerize

### Phase 3: Rebuild Frontend
- Clean HTML/CSS (the Google Doc index is not usable)
- Tailwind + vanilla JS (or SvelteKit if we want routing)
- File upload → validation view → paywall → dashboard
- Mobile-first responsive design

### Phase 4: Deploy + Payments
- Frontend to CF Pages
- API to Fly.io (or Railway)
- MercadoPago integration for $350k COP unlock
- Magic-link auth for returning users

### Phase 5: Data Completeness
- Update IPC series through 2025
- Update SMMLV for 2026
- Add RAIS (private fund) comparison calculations
- Add age-based eligibility projections

---

## Files Worth Keeping vs. Discarding

### Keep (core logic):
- `logic/extract_semanas.py` — PDF parser (production-grade, handles edge cases)
- `logic/calculate_pension.py` — IBL + replacement rate (needs cleanup but logic is sound)
- `logic/solve_pension_gap.py` — goal seeker algorithm
- `logic/boost_history.py` — history booster simulation
- `logic/calculate_full_burden.py` — full cost calculator
- `logic/server.py` — Flask skeleton (replace with FastAPI)
- `webapp/calculator.js` — client-side pension math (already ported to JS)
- `webapp/app.js` — UI controller (28KB, substantial)
- `webapp/data.js` — reference data (SMMLV, IPC, rates)
- `webapp/style.css` — Tailwind styles
- `data/data.json` — canonical reference data
- `data/*.xlsx` — test fixtures
- `data/*.pdf` — test fixtures
- `Business_Summary.txt` — product spec
- `TABLAFACIL.xlsx` — reference spreadsheet

### Discard (debug/one-off):
- `logic/debug_*.py`, `logic/inspect_*.py`, `logic/check_*.py` — ad-hoc investigation scripts
- `logic/compare_*.py`, `logic/verify_*.py` — one-time validation
- `logic/diagnostic_ibl.py`, `logic/deep_inspect.py` — debugging
- `archive/*` — old versions and logs
- `webapp/debug_piedad.js` — test-specific
- `webapp/xlsx.full.min.js` — SheetJS lib (install from npm instead)

---

## Decisions (Confirmed)

1. **All client-side** — no backend server. PDF parsing via pdf.js, Excel via SheetJS, all calculation in JS.
2. **MercadoPago** for payments ($350,000 COP one-time unlock)
3. **Single report** — stateless, no user accounts. Upload → calculate → pay → report → done.
4. **Full RAIS simulation** — sliding scale 0-25% assumed return rate for private fund comparison.
5. **Terms of service gate** — mandatory acceptance before showing results.
6. **All Spanish** UI.
7. **Clean, professional, bank-like** aesthetic. No branding yet.
8. **Responsive** — adaptive to all screen sizes (mobile-first).
9. **Static site on CF Pages** — zero server infrastructure.
10. **Password-locked PDFs** — Colpensiones PDFs are locked with cédula number. Prompt user for cédula before upload, use it to decrypt the PDF client-side via pdf.js password parameter.
11. **MVP push** — build it right, build it now.
