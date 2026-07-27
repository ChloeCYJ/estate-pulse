# Commercial UI Phase 1 - SearchHome Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Track progress by checking off items only after the related tests or verification commands pass.

**Goal:** Implement the Commercial UI Phase 1 SearchHome inside the existing Streamlit app using a single package-based Streamlit Components v2 package, while preserving legacy Dashboard behavior behind a feature flag and keeping all business logic in Python.

**Architecture:** Streamlit remains the app shell and owns routing, session state, service/repository calls, and fallback rendering. Python page adapters build JSON-serializable ViewModels and dispatch UI events. React + TypeScript + Vite render only the SearchHome screen inside one reusable `commercial_ui` package that can later host Analysis, Comparison, and Saved Analysis renderers.

**Tech Stack:** Python 3.14.6, Streamlit 1.59.0, unittest, React 19, TypeScript 5, Vite 7, Vitest, Testing Library, ESLint, Playwright, Node 24.18.0, `npm.cmd`, `npx.cmd`

## Global Constraints

- Keep business calculations, repository access, and external API calls in Python.
- Do not implement `AnalysisDashboard`, `ComparisonDashboard`, or `SavedAnalysisDashboard` in this phase.
- Do not delete or rewrite the legacy Dashboard before rollback is verified.
- Do not add unrelated refactors to `app.py`, service/repository/domain layers, or existing UI pages.
- Keep the `.venv` rollback environment untouched.
- Use explicit, pinned frontend dependency versions where added.
- Use `npm.cmd` / `npx.cmd` instead of bare `npm` / `npx`.

---

### Task 1: Lock the SearchHome Integration Boundary

**Files:**
- Modify: `app.py`
- Modify: `config/settings.py`
- Create: `modules/ui/page_ids.py`
- Create: `modules/ui/search_home_page.py`

**Responsibilities:**
- Add a `ESTATE_PLUS_UI_MODE=legacy|commercial` feature flag, defaulting to `legacy`.
- Extract stable page identifiers and sidebar keys so Python can route commercial navigation events safely.
- Add a SearchHome page controller boundary that can render either the legacy Dashboard or the commercial SearchHome.

**Tests / verification:**
- Add feature-flag tests first.
- Preserve existing page routing behavior in legacy mode.

- [ ] Add failing coverage for `ESTATE_PLUS_UI_MODE` parsing and default behavior
- [ ] Add failing coverage for commercial SearchHome route selection
- [ ] Implement only the minimum routing changes needed to switch Dashboard between legacy and commercial modes

### Task 2: Add Python ViewModel and Event Adapter Coverage

**Files:**
- Create: `modules/ui/viewmodels/__init__.py`
- Create: `modules/ui/viewmodels/search_home.py`
- Create: `tests/test_search_home_viewmodel.py`
- Create: `tests/test_search_home_page.py`

**Responsibilities:**
- Define the SearchHome Python ViewModel contract.
- Serialize service title/description, search query, search status, recent analyses, empty-state status, and display errors.
- Handle SearchHome trigger payloads:
  - `search_submitted`
  - `recent_analysis_selected`
  - `navigation_selected`

**ViewModel contract:**
- `service_title: str`
- `service_description: list[str]`
- `search_query: str`
- `search_status: "idle" | "loading" | "success" | "no_results" | "error"`
- `empty_state: bool`
- `display_error: { code: str, message: str } | null`
- `recent_analyses: list[RecentAnalysisCard]`
- `search_results: list[SearchResultItem]`
- `navigation: list[NavigationItem]`

**Event contract:**
- `search_submitted: { query: string }`
- `recent_analysis_selected: { analysis_id: string }`
- `navigation_selected: { target: string }`

**Tests / verification:**
- Unit-test `None`, empty list, no-results, and system-error cases separately.
- Unit-test that domain/repository objects are not leaked into the ViewModel.

- [ ] Write failing tests for recent analysis serialization and label formatting
- [ ] Write failing tests for search success, no-results, and error ViewModel states
- [ ] Write failing tests for search and recent-analysis event dispatch
- [ ] Write failing tests for navigation event dispatch to existing routes

### Task 3: Build the Streamlit Components v2 Package Shell

**Files:**
- Create: `commercial_ui/pyproject.toml`
- Create: `commercial_ui/README.md`
- Create: `commercial_ui/commercial_ui/__init__.py`
- Create: `commercial_ui/commercial_ui/component.py`
- Create: `commercial_ui/commercial_ui/pyproject.toml`
- Create: `tests/test_commercial_component_contract.py`

**Responsibilities:**
- Register one package-based component using `st.components.v2.component(...)`.
- Use a qualified component name and package-local manifest with `asset_dir`.
- Expose one Python wrapper that mounts the component with `page`, `view_model`, `frontend_state`, and trigger callbacks.
- Support future screen renderers through a single shared component package.

**Tests / verification:**
- Unit-test the Python wrapper payload envelope.
- Unit-test the fallback behavior when the build output is missing.

- [ ] Add failing tests for the component envelope and fallback-safe mounting wrapper
- [ ] Implement the package metadata and Python wrapper without adding any React screen logic yet
- [ ] Confirm the package can be imported from the app runtime

### Task 4: Scaffold the Frontend Workspace and Shared Contracts

**Files:**
- Create: `commercial_ui/frontend/package.json`
- Create: `commercial_ui/frontend/package-lock.json`
- Create: `commercial_ui/frontend/tsconfig.json`
- Create: `commercial_ui/frontend/tsconfig.node.json`
- Create: `commercial_ui/frontend/vite.config.ts`
- Create: `commercial_ui/frontend/eslint.config.js`
- Create: `commercial_ui/frontend/src/index.tsx`
- Create: `commercial_ui/frontend/src/contracts/index.ts`
- Create: `commercial_ui/frontend/src/formatters/koreanCurrency.ts`
- Create: `commercial_ui/frontend/src/formatters/koreanCurrency.test.ts`
- Create: `commercial_ui/frontend/src/streamlit.ts`

**Responsibilities:**
- Set up Vite production output under `commercial_ui/commercial_ui/frontend/build`.
- Define the shared TypeScript envelope, ViewModel, and trigger types.
- Centralize the Korean currency formatter used by the SearchHome renderer.

**Tests / verification:**
- `npm.cmd run typecheck`
- `npm.cmd run lint`
- `npm.cmd run test`
- `npm.cmd run build`

- [ ] Add the pinned frontend dependency manifest and scripts
- [ ] Add failing formatter and type-level contract tests
- [ ] Implement the frontend contract layer and build pipeline

### Task 5: Implement the Shared Design System and SearchHome Renderer

**Files:**
- Create: `commercial_ui/frontend/src/design-system/tokens.css`
- Create: `commercial_ui/frontend/src/design-system/global.css`
- Create: `commercial_ui/frontend/src/components/AppShellFrame.tsx`
- Create: `commercial_ui/frontend/src/components/SearchInput.tsx`
- Create: `commercial_ui/frontend/src/components/RecentAnalysisCard.tsx`
- Create: `commercial_ui/frontend/src/components/StatePanel.tsx`
- Create: `commercial_ui/frontend/src/renderers/SearchHomeRenderer.tsx`
- Create: `commercial_ui/frontend/src/renderers/SearchHomeRenderer.test.tsx`

**Responsibilities:**
- Implement a restrained, finance-service style UI with one primary color family.
- Render:
  - estate service header
  - value proposition copy
  - search input and button
  - recent analysis cards
  - idle / loading / no-results / error states
  - narrow-screen responsive layout
- Emit only the approved triggers back to Python.

**Design tokens:**
- `color`
- `typography`
- `spacing`
- `radius`
- `shadow`
- `breakpoint`
- `z-index`

**Tests / verification:**
- Component tests for idle, recent data, loading, no-results, error, and mobile-friendly DOM states
- Accessibility checks for landmarks, button labels, and focus-visible keyboard flow

- [ ] Write failing renderer tests for each visual state and trigger emission
- [ ] Implement the shared token system before page CSS
- [ ] Implement SearchHome renderer and shared components
- [ ] Verify no raw repository/service logic exists in the frontend

### Task 6: Wire the Commercial SearchHome Into Streamlit

**Files:**
- Modify: `app.py`
- Modify: `modules/ui/dashboard.py` only if needed for fallback delegation
- Modify: `README.md`

**Responsibilities:**
- Mount the commercial SearchHome on the Dashboard route when `ESTATE_PLUS_UI_MODE=commercial`.
- Keep the legacy Dashboard for `ESTATE_PLUS_UI_MODE=legacy`.
- Log React render failures and fall back deliberately instead of silently hiding them.
- Document development and production commands for the component package.

**Tests / verification:**
- Legacy feature-flag test
- Commercial feature-flag test
- Streamlit smoke test in commercial mode

- [ ] Wire the page controller into the Dashboard entrypoint
- [ ] Verify recent-analysis selection reaches Python and triggers route state updates
- [ ] Verify search events reach Python and rebuild the ViewModel
- [ ] Document dev/build/runtime commands in existing project docs

### Task 7: Verify Frontend, Python, Smoke, and Visual Output

**Files:**
- Create: `artifacts/commercial-ui/search-home/desktop-idle.png`
- Create: `artifacts/commercial-ui/search-home/desktop-recent.png`
- Create: `artifacts/commercial-ui/search-home/desktop-loading.png`
- Create: `artifacts/commercial-ui/search-home/desktop-no-results.png`
- Create: `artifacts/commercial-ui/search-home/desktop-error.png`
- Create: `artifacts/commercial-ui/search-home/mobile-idle.png`
- Create: `artifacts/commercial-ui/search-home/mobile-recent.png`

**Responsibilities:**
- Run all required commands in `.venv314` and Node 24.
- Capture Playwright screenshots for the required SearchHome states.
- Verify the existing major pages still render after the Dashboard routing change.

**Required verification order:**
1. Targeted Python tests
2. Full Python suite
3. `npm.cmd install`
4. `npm.cmd run typecheck`
5. `npm.cmd run lint`
6. `npm.cmd run test`
7. `npm.cmd run build`
8. Streamlit commercial smoke test
9. Playwright screenshot capture
10. Manual regression spot-check for existing analysis/comparison/history paths

- [ ] Run the targeted SearchHome Python tests
- [ ] Run the full Python suite
- [ ] Run all frontend install/typecheck/lint/test/build commands
- [ ] Run the Streamlit smoke test with `ESTATE_PLUS_UI_MODE=commercial`
- [ ] Save the required screenshots under `artifacts/commercial-ui/search-home/`
- [ ] Re-check that legacy mode still renders the old Dashboard

## Rollback Strategy

- The default renderer mode remains `legacy`.
- `ESTATE_PLUS_UI_MODE=commercial` enables the React SearchHome only for the Dashboard route.
- If the component build is missing or the mount path raises an exception, Python logs the root cause and renders the existing legacy Dashboard.
- No existing user-facing page is deleted or renamed in Phase 1.

## Visual Fixtures To Produce

- Desktop `1440x1000`
  - idle
  - recent analyses
  - loading
  - no results
  - error
- Mobile `390x844`
  - idle
  - recent analyses

## Completion Gate

- The database connection contract regression remains green.
- Legacy mode still renders the current Dashboard.
- Commercial mode renders the React SearchHome inside Streamlit.
- Search and recent-analysis triggers reach Python.
- The frontend build output is served by the package-based component without 404s.
- Full Python tests, frontend checks, smoke test, and screenshot capture all complete successfully.
