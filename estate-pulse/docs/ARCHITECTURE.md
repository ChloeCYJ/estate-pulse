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
  -> UI page/controller modules
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

## Data And Runtime Rules

- Keep SQLite fallback and PostgreSQL runtime support compatible together.
- `apartment_complex`, `manual_listing`, `user_finance_profile`, transaction tables, and `analysis_result` remain core persisted domains.
- `analysis_result` is the saved analysis history source.
- Additive schema compatibility should happen in code, not by manual DB file edits.

## Current Product Surfaces

- Legacy Streamlit pages remain the main app shell.
- Commercial SearchHome is available through the UI mode flag.
- Analysis, comparison, saved analysis, and admin/debug surfaces still rely on the existing Python boundaries unless a later phase explicitly migrates them.

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
