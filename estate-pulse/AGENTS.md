# Estate Pulse AGENTS

## Runtime

- Python: `3.14.6`
- Streamlit: `1.59.0`
- Node.js: `24.18.0`
- Active Python venv: `.venv314`
- Keep the legacy Python 3.9 `.venv` intact for rollback only.
- In PowerShell, use `npm.cmd` and `npx.cmd` instead of bare `npm` and `npx`.

## Core Boundaries

- Streamlit owns app shell, routing, session state, feature flags, and Python calls.
- Services own workflows and orchestration.
- Repositories own DB access and SQL.
- Analyzers own deterministic calculations and scoring.
- React + TypeScript render customer-facing UI through Streamlit Components v2.
- React consumes JSON-serializable ViewModels produced by Python adapters.

## Never Move Into React

- DB access
- Repository calls
- External API calls
- Business calculations
- Pricing, funding, score, or policy logic

## UI Rules

- Preserve existing analysis behavior unless the task explicitly changes it.
- Keep legacy UI available until the replacement has a verified rollback path.
- Prefer page-level React entry points over one component per card.
- Keep shared design tokens in one frontend module.
- Do not add duplicated inline HTML or per-page raw CSS.
- Korean monetary values must use the shared formatter.
- Always implement loading, empty, partial-data, and error states when working on customer-facing UI.

## Change Protection

- Start by checking `git status --short`.
- Do not overwrite existing user changes in tracked files without understanding them first.
- Preserve existing changes in `AGENTS.md`, `README.md`, and `docs/superpowers/`.
- Do not refactor unrelated files.
- Only implement the requested scope.
- Keep changes minimal and localized.

## Protected Paths

Never modify, restore, delete, compile, or inspect:

- `.venv/`
- `.git/`
- `__pycache__/`
- `*.pyc`
- `.env`
- `*.db`

## Required Test Commands

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

Run the commands that prove your claim before reporting success. Do not declare completion without fresh evidence.

## Document Map

- `README.md`: project entrypoint, runtime setup, app run commands, test commands
- `docs/ARCHITECTURE.md`: system structure and layer responsibilities
- `docs/COMMERCIAL_UI.md`: current commercial UI scope, feature flag, phase focus, verification
- `docs/CODEX_GUIDE.md`: investigation, planning, implementation, verification, reporting workflow
- `docs/REVIEW_GUIDE.md`: review and completion checklist
- `docs/superpowers/plans/active/`: active plan for the current phase
- `docs/superpowers/specs/archive/` and `docs/superpowers/plans/archive/`: reference-only history
- `commercial_ui/README.md`: package-local frontend build and asset workflow

## Minimum Read Set

Default read set for AnalysisDashboard Phase 2 and later:

1. `AGENTS.md`
2. `docs/ARCHITECTURE.md`
3. `docs/COMMERCIAL_UI.md`
4. `docs/superpowers/plans/active/<current-plan>.md`

Read archive docs only when the active documents do not answer the question.
