# Estate Pulse Commercial UI

## Goal

Commercial UI upgrades the customer-facing experience while preserving the
existing Python business logic and Streamlit app shell.

## Validated Runtime

- Python `3.14.6`
- Streamlit `1.59.0`
- Node.js `24.18.0`
- npm `11.16.0`
- Active Python venv: `.venv314`

In PowerShell, use `npm.cmd` and `npx.cmd`.

## Architecture

- Streamlit owns routing, session state, feature flags, and Python integration.
- Python adapters build typed, JSON-serializable ViewModels.
- React + TypeScript render customer-facing screens through Streamlit Components v2.
- React sends events to Python. Python decides what to do next.

## Hard Boundaries

React must not:

- access the DB directly
- call repositories directly
- call external APIs directly
- perform business calculations
- replace Python domain models with frontend logic

## Current Status

- Runtime migration is complete on Python `3.14.6` and Streamlit `1.59.0`.
- SearchHome Phase 1 is complete.
- AnalysisDashboard Phase 2 core flow is implemented: canonical page state, live analysis handoff, saved snapshot reopen, save-without-recompute, and legacy comparison routing.
- Auth0-brokered Google, Kakao, and Naver login is connected at the Streamlit boundary.
- Authenticated users can create or edit one personal finance profile; analyses and saved results are scoped to that internal user.
- The legacy administrator surface uses a separate Auth0-independent local account and is never authorized by a customer session.
- Streamlit Components v2 package-based integration is in place under `commercial_ui/`.
- Legacy mode remains available as the rollback path.

## Shadow DOM Token Rule

Components v2 renders inside Shadow DOM. Shared visual tokens must be exposed at
the component `:host` boundary and consumed from one frontend design-token
module. Do not scatter duplicated per-screen CSS variables across renderers.

## Current Phase

Current active phase: Commercial MVP release verification and hardening.

### Completed implementation

- Auth0 session resolution and sanitized account actions
- User-owned current finance profile creation and editing
- Login/profile completion followed by pending-analysis resume
- User-scoped recent, detail, and saved analysis operations
- Loading, empty, validation, storage-error, and auth-required states

### MVP release blockers

- Google, Kakao, and Naver end-to-end login checks with real Auth0 credentials
- PostgreSQL smoke tests with a dedicated `TEST_DATABASE_URL`
- Deployed-flow smoke for login, profile save, analysis, save/reopen, logout, and ownership isolation
- AnalysisDashboard visual capture plus desktop/mobile responsive review

### MVP boundary

- Comparison continues through the verified legacy Streamlit page.
- A native Commercial comparison screen is not required for the first MVP release.
- Legacy mode remains the rollback path until production verification is complete.

### Post-MVP

- Native Commercial comparison
- Commercial watchlist and ranking screens
- Account linking and membership withdrawal
- Multiple finance profiles or scenarios per user
- Dedicated Commercial admin and debug screens

### Explicitly out of scope for the current phase

- new product features
- repository or analyzer redesign
- moving calculations into React
- direct API/DB access from React
- replacing admin or debug pages
- deleting legacy UI before rollback is verified

## Authentication boundary

- Streamlit calls the named `auth0` provider and resolves verified `iss`/`sub` claims to an internal account.
- Auth0 Universal Login exposes Google, Kakao, and Naver; provider OAuth exchanges do not run in React.
- React receives display name, email, provider label, profile-existence state, and sanitized errors only.
- Real credentials belong only in ignored `.streamlit/secrets.toml`; the committed example contains placeholders.
- Local administrator credentials remain in the `[local_admin]` secrets section and never enter Commercial React data.

## Important Code Paths

- `app.py`
- `config/settings.py`
- `modules/ui/page_ids.py`
- `modules/ui/search_home_page.py`
- `modules/ui/viewmodels/`
- `commercial_ui/component.py`
- `commercial_ui/frontend/src/renderers/`
- `commercial_ui/frontend/src/design-system/`
- `commercial_ui/frontend/src/contracts/`

## Feature Flag

`ESTATE_PLUS_UI_MODE`

- `legacy`: use the existing Streamlit home
- `commercial`: use SearchHome, AnalysisDashboard, account actions, and personal assets

Keep rollback through the legacy mode available during future phases.

## Minimum Read Set

Default read set for AnalysisDashboard work:

1. `AGENTS.md`
2. `docs/ARCHITECTURE.md`
3. `docs/COMMERCIAL_UI.md`
4. `docs/superpowers/plans/active/<current-plan>.md`

Read archive docs only when these active documents do not answer the question.

## Verification Commands

Python:

```powershell
.\.venv314\Scripts\python -m unittest discover -s tests -v
```

Frontend from `commercial_ui/frontend`:

```powershell
cmd /c npm.cmd run typecheck
cmd /c npm.cmd run lint
cmd /c npm.cmd run test
cmd /c npm.cmd run build
```

Streamlit smoke:

```powershell
.\.venv314\Scripts\python -m streamlit run app.py
```

## Related Docs

- `README.md` for setup and app commands
- `docs/ARCHITECTURE.md` for system boundaries
- `commercial_ui/README.md` for package-local frontend operations
- `docs/superpowers/specs/archive/` and `docs/superpowers/plans/archive/` for historical detail
