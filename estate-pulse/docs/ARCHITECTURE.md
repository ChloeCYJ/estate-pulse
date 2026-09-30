# Estate Pulse Architecture

## Purpose

This document defines the long-lived system structure and layer boundaries for
Estate Pulse. It does not define task workflow or review process.

## Runtime Stack

- Python `3.14.6`
- Streamlit `1.59.0`
- Node.js `24.18.0`
- SQLite by default
- PostgreSQL when `DATABASE_URL` is set

## High-Level Shape

```text
Streamlit shell
  -> Auth0 OIDC session -> internal app_user/auth_identity
  -> Local administrator secrets -> administrator-only session
  -> UI page/controller modules
    -> canonical commercial page/session state
    -> Services
      -> Repositories
      -> Analyzers
  -> Streamlit Components v2 bridge
    -> React renderers
```

## Layer Responsibilities

### Streamlit shell

- Starts the app from `app.py`
- Owns page routing, session state, feature flags, and Python-side fallback
- Calls page controllers and commercial component adapters

### UI modules

- Live under `modules/ui/`
- Render Streamlit pages or assemble ViewModels for React renderers
- Must not write SQL directly
- Must not own business calculations

### Services

- Live under `modules/services/`
- Combine repositories and analyzers into workflows
- Own analysis orchestration, rule selection, policy import, comparison, and ranking flows

### Repositories

- Live under `modules/repositories/`
- Own persistence, SQL, and DB-specific access details
- Must not contain scoring or UI decisions

### Analyzers

- Live under `modules/analyzers/`
- Own deterministic calculations and scoring
- Examples: required cash, shortage cash, jeonse ratio, bargain score, liquidity score

### Commercial UI package

- Lives under `commercial_ui/`
- Uses Streamlit Components v2 package-based integration
- React renders customer-facing UI only
- Python adapters own event handling and ViewModel creation
- `CommercialPageState` is the canonical route and active-analysis state for commercial pages
- SearchHome and AnalysisDashboard use page-level envelopes and typed trigger events

## Data And Runtime Rules

- Keep SQLite fallback and PostgreSQL runtime support compatible together.
- `apartment_complex`, `manual_listing`, `user_finance_profile`, transaction tables, and `analysis_result` remain core persisted domains.
- `analysis_result` is the saved analysis history source.
- Saved AnalysisDashboard detail is loaded by `analysis_id` from persisted snapshot columns.
- Saving an already-computed live analysis persists the active result without recomputation or fresh external lookups.
- Additive schema compatibility should happen in code, not by manual DB file edits.
- `app_user` and `auth_identity` map the stable OIDC `(issuer, subject)` pair; email is display data and never an account-link key.
- Commercial `user_finance_profile` and `analysis_result` access is scoped by internal `user_id`; legacy unowned rows remain available only to legacy paths.
- Streamlit completes Auth0 login/logout and passes only a sanitized auth ViewModel to React. Tokens and raw claims never enter component state.
- The local administrator principal is verified from an Argon2 hash in Streamlit secrets, remains separate from customer identities, and gates the legacy administrator renderer in Python.
- Local administrator authentication has no automatic timeout or failed-attempt lockout by product decision; production ingress must provide HTTPS and rate limiting.

## Current Product Surfaces

- Streamlit remains the app shell in both UI modes.
- Commercial SearchHome, AnalysisDashboard, and personal finance profile are available through the UI mode flag.
- Commercial comparison hands off to the existing legacy comparison page.
- Admin/debug surfaces remain legacy until dedicated commercial replacements are verified.
- The legacy administrator surface is reachable through `?admin=1` in either UI mode only after local administrator authentication.

## Important Paths

- `app.py`
- `config/settings.py`
- `modules/ui/`
- `modules/services/`
- `modules/repositories/`
- `modules/analyzers/`
- `commercial_ui/`
- `tests/`

## Related Documents

- `README.md`: runtime setup and app commands
- `docs/COMMERCIAL_UI.md`: commercial UI scope and current phase
- `docs/CODEX_GUIDE.md`: task workflow
- `docs/REVIEW_GUIDE.md`: review checklist
