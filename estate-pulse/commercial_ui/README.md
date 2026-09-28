# Estate Pulse Commercial UI Package

This document covers package-local frontend operations only.
For product scope, architecture, and phase status, see
`docs/COMMERCIAL_UI.md`.

## Package Shape

```text
commercial_ui/
  component.py
  README.md
  frontend/
    package.json
    vite.config.ts
    src/
      contracts/
      design-system/
      formatters/
      renderers/
```

## Supported Pages

- `search-home`: search, recent analyses, analysis request preparation
- `analysis-dashboard`: live/saved analysis display, save, back, retry, and comparison triggers

The frontend receives JSON-serializable ViewModels and emits typed events. Streamlit/Python owns routing, session state, authentication, repository access, and all calculations.

## Frontend Dependency Install

Run from `commercial_ui/frontend`:

```powershell
cmd /c npm.cmd install
```

## Development Watch

```powershell
cmd /c npm.cmd run dev
```

- Keep Streamlit running in a separate terminal.
- The watch build writes assets to `commercial_ui/frontend/build`.

## Production Build

```powershell
cmd /c npm.cmd run build
```

## Validation Commands

```powershell
cmd /c npm.cmd run typecheck
cmd /c npm.cmd run lint
cmd /c npm.cmd run test
```

## Streamlit Run

From the repository root:

```powershell
$env:ESTATE_PLUS_UI_MODE='commercial'
.\.venv314\Scripts\python -m streamlit run app.py
```

To return to legacy mode:

```powershell
$env:ESTATE_PLUS_UI_MODE='legacy'
.\.venv314\Scripts\python -m streamlit run app.py
```

## Visual Capture

Recommended viewport sizes:

- Desktop: `1440 x 1000`
- Mobile: `390 x 844`

Capture commercial UI screenshots after either the watch build or production build is available and Streamlit is running in commercial mode.

SearchHome capture is available through `visual:search-home`. AnalysisDashboard capture remains required before Phase 2 can be archived.

## Build Asset Locations

- Dev/watch output: `commercial_ui/frontend/build`
- Packaged assets loaded by Streamlit: `commercial_ui/build`

Ensure the production build output is the asset set that Python packages and serves.
