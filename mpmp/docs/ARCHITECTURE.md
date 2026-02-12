# MPMP — Architecture Document

## System Overview

The Medical Practice Management Platform (MPMP) is a HIPAA-compliant, modular system for functional medicine practices specializing in peptide therapy and magistral compounding. It integrates with the Azoth OS ecosystem via HL7 FHIR standards for prescription routing and real-time inventory synchronization.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │ Provider  │ │ Clinical │ │ Admin    │ │ Patient Portal    │  │
│  │ Dashboard │ │ Engine   │ │ Console  │ │ (Restricted)      │  │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ └────────┬──────────┘  │
│        │             │            │                │             │
│  ┌─────┴─────────────┴────────────┴────────────────┴──────────┐ │
│  │              Zustand State + WebSocket Client               │ │
│  └─────────────────────────┬───────────────────────────────────┘ │
└────────────────────────────┼─────────────────────────────────────┘
                             │ HTTPS / WSS
┌────────────────────────────┼─────────────────────────────────────┐
│                     BACKEND (FastAPI)                             │
│  ┌─────────────┐ ┌────────┴────────┐ ┌──────────────────────┐   │
│  │ Auth/RBAC   │ │ REST API v1     │ │ WebSocket Hub        │   │
│  │ (OIDC+JWT)  │ │ (/api/v1/...)   │ │ (inventory events)   │   │
│  └──────┬──────┘ └────────┬────────┘ └──────────┬───────────┘   │
│         │                  │                      │               │
│  ┌──────┴──────────────────┴──────────────────────┴───────────┐  │
│  │                    SERVICE LAYER                            │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │  │
│  │  │ Patient  │ │ Clinical │ │ Magistral│ │ Azoth Router │  │  │
│  │  │ Service  │ │ Notes    │ │ Calc     │ │ (FHIR)       │  │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘  │  │
│  └───────┼─────────────┼────────────┼──────────────┼──────────┘  │
│          │             │            │              │              │
│  ┌───────┴─────────────┴────────────┴──────────────┴───────────┐ │
│  │              MIDDLEWARE PIPELINE                              │ │
│  │  [Audit Logger] → [PHI Encryption] → [Rate Limiter]         │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
└─────────────────────────────┼────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
   ┌──────┴──────┐    ┌──────┴──────┐    ┌──────┴──────┐
   │ PostgreSQL  │    │   Redis     │    │ Azoth OS    │
   │ (PHI, EHR,  │    │ (Sessions,  │    │ (FHIR API,  │
   │  Audit Log) │    │  Idempotency│    │  Webhooks)  │
   │  AES-256    │    │  Job Queue) │    │  HMAC Auth  │
   └─────────────┘    └─────────────┘    └─────────────┘
```

## Tech Stack Decisions

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Next.js 14 (App Router) + TypeScript Strict | SSR for portal SEO, RSC for performance |
| State | Zustand + WebSocket | Lightweight, no boilerplate, real-time inventory |
| Backend | FastAPI (Python 3.11+) | Type-safe, async, excellent for FHIR JSON parsing |
| ORM | SQLAlchemy 2.0 + Alembic | Mature, supports encryption hooks, migration-first |
| Database | PostgreSQL 16 | HIPAA-ready, row-level security, JSONB for FHIR |
| Cache/Queue | Redis 7 | Idempotency keys, session store, Celery broker |
| Auth | Custom JWT + OIDC (future Clerk/Auth0) | 15-min access tokens, refresh rotation |
| PDF Engine | ReportLab | Python-native, no Puppeteer overhead |
| Email | AWS SES (or SendGrid) | HIPAA BAA available |
| Infra | Docker Compose (dev) → AWS ECS (prod) | Encrypted EBS, VPC isolation |

## Data Flow: Prescription Lifecycle

```
Provider signs protocol
        │
        ▼
┌─────────────────────┐
│ AZOTH_OS_SYNC check │
└────────┬────────────┘
         │
    ┌────┴────┐
    │  FALSE  │──▶ Generate AES-256 encrypted PDF
    └─────────┘    Enqueue SMTP job (Redis/Celery)
    │  TRUE   │──▶ Build FHIR MedicationRequest
    └─────────┘    OAuth2 Client Credentials → POST to Azoth
                   Store azoth_tracking_id locally
                   Emit WebSocket event to Provider + Patient
```

## Security Architecture

### PHI Protection Layers
1. **Transport**: TLS 1.3 enforced on all endpoints
2. **Application**: AES-256-GCM encryption for marked columns (first_name, last_name, dob, demographics, soap_data)
3. **Storage**: AWS EBS encryption (or equivalent managed encryption)
4. **Access**: RBAC enforced at middleware level, audit-logged
5. **External**: azoth_alias_id (UUID) used for ALL FHIR payloads — zero PHI leaves the system

### Authentication Flow
```
Login → OIDC Provider → JWT (15min access + 7d refresh)
     → RBAC middleware checks role on every request
     → Idle timeout: 15 minutes → forced logout
     → MFA required for Provider/SuperAdmin roles
```

### Webhook Security (Inbound from Azoth)
```
Request arrives at /api/v1/webhooks/inventory-update
    → Extract X-Azoth-Signature header
    → HMAC-SHA256(raw_body, AZOTH_WEBHOOK_SECRET)
    → Constant-time comparison
    → Check Redis for event_id (idempotency)
    → Process or drop
```

## Module Map

| Module | Phase | Dependencies |
|--------|-------|-------------|
| Auth/RBAC | 1 | PostgreSQL, Redis |
| Audit Logging | 1 | PostgreSQL |
| Patient EHR | 2 | Auth, Audit |
| SOAP Notes | 2 | Patient EHR, Auth |
| Scheduling | 2 | Patient EHR |
| Billing (Stripe) | 2 | Patient EHR |
| Magistral Calculator | 3 | Inventory |
| PDF/SMTP Fallback | 3 | Magistral Calc |
| Webhook Receiver | 4 | Redis, WebSocket |
| FHIR Router | 5 | Magistral Calc, OAuth2 |
| Patient Portal | 6 | All above |

## Database Schema (ERD Summary)

```
users ──────────┐
  │ id, role,   │
  │ email,      │
  │ mfa_secret  │
  └──────┬──────┘
         │ 1:1
  ┌──────┴──────┐        ┌──────────────┐
  │  patients   │───────▶│ appointments │
  │ azoth_alias │  1:N   │ telehealth   │
  │ PHI (AES)   │        └──────────────┘
  └──────┬──────┘
         │ 1:N
  ┌──────┴──────┐        ┌──────────────┐
  │ clinical_   │        │ prescriptions│
  │ notes       │        │ azoth_track  │
  │ SOAP (AES)  │        │ dosage_str   │
  └─────────────┘        └──────┬───────┘
                                │ refs
                         ┌──────┴───────┐
                         │ inventory_   │
                         │ cache        │
                         │ webhook_sync │
                         └──────────────┘

  ┌─────────────┐
  │ audit_logs  │  ← immutable append-only
  │ every R/W/D │
  └─────────────┘
```
