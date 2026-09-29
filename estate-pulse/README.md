# Estate Pulse

Estate Pulse is a Streamlit-based real-estate investment analysis app.
It supports apartment/listing management, funding analysis, saved analysis
history, watchlist/comparison flows, and policy/rule administration.

Commercial mode provides React-based SearchHome, AnalysisDashboard, and personal
asset screens while Streamlit/Python retains authentication and business logic.

## Runtime

- Python `3.14.6`
- Streamlit `1.59.0`
- Node.js `24.18.0`
- npm `11.16.0`
- Active Python venv: `.venv314`

Keep the legacy Python 3.9 `.venv` for rollback until replacement work is fully verified.

## Project Structure

```text
estate-pulse/
  app.py
  requirements.txt
  commercial_ui/
  config/
  docs/
  modules/
  scripts/
  tests/
```

## Python Environment Setup

```powershell
py -3.14 -m venv .venv314
.\.venv314\Scripts\python -m pip install --upgrade pip setuptools wheel
.\.venv314\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Runtime pin files:

- `.python-version` -> `3.14.6`
- `.nvmrc` -> `24.18.0`

If PowerShell blocks `npm.ps1`, use `npm.cmd` and `npx.cmd`.

## Frontend Dependency Setup

Commercial UI frontend commands run from `commercial_ui/frontend`.

```powershell
cmd /c npm.cmd install
```

## Run The App

### Commercial authentication setup

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and replace
every placeholder locally. The real secrets file is ignored and must never be
committed. Create one Auth0 Regular Web Application, configure
`http://localhost:8501/oauth2callback` as an allowed callback URL and the local
app origin as an allowed logout URL, then enable Google, Kakao, and Naver social
connections in Auth0 Universal Login. Use separate Auth0 applications and
secrets for local and production deployments. Streamlit uses the named
`auth0` provider through `st.login("auth0")`.

Legacy mode:

```powershell
$env:ESTATE_PLUS_UI_MODE='legacy'
.\.venv314\Scripts\python -m streamlit run app.py
```

Commercial mode:

```powershell
$env:ESTATE_PLUS_UI_MODE='commercial'
.\.venv314\Scripts\python -m streamlit run app.py
```

If `DATABASE_URL` is unset, the app uses the default local SQLite path.
When `DATABASE_URL` is set, the app uses PostgreSQL runtime support.

## Commercial Mode Status

- SearchHome can search registered complexes, start analysis, and reopen recent saved analyses.
- AnalysisDashboard renders live or saved snapshot results and supports save, back, and legacy-comparison handoff events.
- `CommercialPageState` owns commercial navigation and the active analysis result.
- Legacy mode remains the rollback path.
- Google, Kakao, and Naver login is brokered by Auth0 and resolved to an internal user from OIDC issuer/subject claims.
- Each authenticated user has one editable personal finance profile and user-scoped saved analyses.

## Test Commands

Full Python suite:

```powershell
.\.venv314\Scripts\python -m unittest discover -s tests -v
```

PostgreSQL smoke tests require `TEST_DATABASE_URL` to target a dedicated `*_test` database. Report them as unverified when that environment is not configured.

Frontend checks from `commercial_ui/frontend`:

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

## Major Documents

- [AGENTS.md](/D:/CodexProject/estate-pulse/AGENTS.md)
- [docs/ARCHITECTURE.md](/D:/CodexProject/estate-pulse/docs/ARCHITECTURE.md)
- [docs/COMMERCIAL_UI.md](/D:/CodexProject/estate-pulse/docs/COMMERCIAL_UI.md)
- [docs/CODEX_GUIDE.md](/D:/CodexProject/estate-pulse/docs/CODEX_GUIDE.md)
- [docs/REVIEW_GUIDE.md](/D:/CodexProject/estate-pulse/docs/REVIEW_GUIDE.md)
- [commercial_ui/README.md](/D:/CodexProject/estate-pulse/commercial_ui/README.md)

Use `docs/superpowers/plans/active/` for the current phase plan and the
archive folders under `docs/superpowers/` for older context only when needed.
