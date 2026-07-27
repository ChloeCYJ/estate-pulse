# Estate Pulse

Estate Pulse is a Streamlit-based real-estate investment analysis app.
It supports apartment/listing management, funding analysis, saved analysis
history, watchlist/comparison flows, and policy/rule administration.

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

## Test Commands

Full Python suite:

```powershell
.\.venv314\Scripts\python -m unittest discover -s tests -v
```

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
