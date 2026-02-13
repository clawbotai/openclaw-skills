# MEMORY.md — Long-Term Memory

## Steven (User)
- Steven Cody Reynolds, West Point '03, GMT-5 (America/Bogota)
- Email: steven.cody.reynolds@gmail.com, Phone: +15037700039
- Prefers quick action over explanations, dark-mode minimalist design
- Sends files via email to clawaibot@icloud.com
- Python 3.9 compatible, stdlib-only for skills

## Projects

### TØrr Statics
- Precision laboratory hardware company, Dover DE
- Products: ISOBAR Ø1 (dual-vial fluid transfer), POISE Ø27 (27G cannula hub)
- **CRITICAL**: Zero medical/FDA/tissue/needle/human language — General Laboratory Use Only
- Live site: torrstatics.com (CF Pages, v3.5, commit `fad53b7`)
- Design: Industrial Brutalist. Void Black #212123, Titanium #b2b2b2, Signal White #FFFFFF. IBM Plex Mono + Asap.
- Crypto payments: BIP-32 HD wallet, USDT/ETH, Etherscan verification. All prices $1 for testing.
- **Blocker**: CF Pages Functions returning 405 after D1 binding work. Root cause unclear.
- Brand assets: `assets/torr_hd_brandbook.pdf`, manufacturing PDFs in `assets/isobar/`, `assets/poise/`
- GitHub: clawbotai/torr-statics (private)

### MPMP
- Medical Practice Management Platform — functional medicine / peptide therapy
- HIPAA-compliant, Azoth OS integration (dual-mode: connected vs standalone)
- 5,151 LOC: FastAPI + PostgreSQL + Redis backend, Next.js 14 frontend
- Features: PHI encryption (AES-256-GCM), RBAC (4 roles), Magistral Calculator, FHIR builder, Stripe billing, SOAP notes with digital signing
- GitHub: clawbotai/mpmp (private)

### OpenClaw Skills Workspace
- 25 skills: 8 infrastructure, 5 engineering, 3 knowledge work, 9 domain expertise
- 9 domain skills derived from Anthropic knowledge-work-plugins (Apache-2.0)
- Cross-skill integration architecture with 9 pipelines (docs/SKILL-INTEGRATION-ARCHITECTURE.md)
- GitHub: clawbotai/openclaw-skills (public)

## Infrastructure
- **Cloudflare**: Account ID `467a2bd281c1d03aa46c1dc520262826`, tokens in Keychain
- **D1**: `torr-orders` database provisioned (ID: `6f241383-60fb-45d9-a75b-b0d4ead7ee2a`)
- **KV**: `ORDERS` namespace (ID: `9fcb14464b6a4ee595e0226efa4eff97`)
- **Crypto wallet**: `0xA010807fAeef36c957CA80F17bA01b3922f7901C`
- **Hetzner**: Account created, manual verification pending
- **Email**: clawaibot@icloud.com (iCloud requires BODY.PEEK[] not RFC822)

## Learned Behaviors (encoded in SOUL.md)
1. Python 3.9 compat — `Optional[X]` not `X | None`
2. No nested triple-quotes in docstrings
3. No `sys.exit()` in library functions — exceptions only
4. Always read code before trusting another AI's review (~40% useful, ~60% fabricated)
5. LLM code generation needs explicit constraint injection
6. `bin/skillrun` for all skill invocations
7. Back up before destructive replacements
8. Debug image coordinates with red marker first

## Key Decisions
- architect_skill.py is for scaffolding, not rebuilding complex systems
- Skills never import each other — LLM is the integration layer
- agent-memory as shared brain is P0 integration priority
- Passwordless auth for OMS (magic-link + wallet-signature)
- MPMP SOAP notes are immutable when signed
- torr-statics-site/ is a separate git repo (not tracked by parent)
