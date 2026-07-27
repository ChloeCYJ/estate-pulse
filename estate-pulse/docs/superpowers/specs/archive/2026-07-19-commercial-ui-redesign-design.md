# Estate Plus Commercial UI Redesign Design

## Scope

- Goal: redesign only the user-facing core UI while preserving existing Estate Pulse behavior and Python business logic.
- In scope:
  - Streamlit app shell, page routing, session state, and Python service calls remain.
  - React + TypeScript replace the visual layer for the core user screens.
  - Streamlit Custom Components v2 package-based component architecture is the target integration model.
  - The final top-level user menu is reduced to `단지 검색`, `단지 비교`, and `저장한 분석`.
  - Analysis result is treated as a detail screen entered from search results or saved analyses, not as a permanent top-level user menu.
  - The final React migration target is limited to `SearchHome`, `AnalysisDashboard`, `ComparisonDashboard`, and `SavedAnalysisDashboard`.
  - Phase 1 implementation scope is `SearchHome` only.
- Out of scope:
  - New product capability
  - Service, repository, analyzer, or DB schema redesign
  - Admin/debug page React migration
  - Authentication, billing, Next.js, FastAPI API layer
  - `AnalysisDashboard`, `ComparisonDashboard`, and `SavedAnalysisDashboard` implementation during Phase 1

## Confirmed Decisions

### Technical decisions

- Streamlit is upgraded to `>=1.51,<2.0`.
- Node.js uses `24 LTS`.
- The current Python runtime must be checked before implementation starts.
- If Python is lower than `3.10`, implementation must stop and only impact scope should be reported.
- The project keeps its existing Python package management workflow.
- `uv` migration is out of scope.
- New dependencies must be pinned to explicitly compatible versions instead of floating to latest.
- Streamlit Components v2 package-based component structure is required.
- React + TypeScript + Vite is the required frontend stack.

### Product structure decisions

- Final top-level user menu:
  - `단지 검색`
  - `단지 비교`
  - `저장한 분석`
- `SearchHome` ultimately replaces the current `Dashboard`, but the legacy `Dashboard` remains until the replacement has a verified rollback path.
- `AnalysisDashboard` is a detail screen rather than a fixed top-level menu.

### Component package decision

- The frontend is organized as one package-based component package with multiple screen-specific renderers.
- The preferred package shape is:

```text
commercial_ui/
  frontend/
    src/
      renderers/
        SearchHomeRenderer.tsx
      components/
      design-system/
      contracts/
      formatters/
  component.py
  pyproject.toml
```

- Future renderers such as `AnalysisDashboardRenderer.tsx`, `ComparisonDashboardRenderer.tsx`, and `SavedAnalysisRenderer.tsx` must fit into the same package without collapsing all screen logic into one giant component.

## Current UI Structure Analysis

### Current state classification

- `Already Implemented`
  - Repository, service, analyzer layering is established.
  - Streamlit app shell and manual page routing exist in [app.py](/D:/CodexProject/estate-pulse/app.py).
  - Core user flows already exist: dashboard, complex/listing/profile management, analysis, watchlist, comparison, ranking.
  - Tests cover most calculation, repository, service, and label logic.
- `Partially Implemented`
  - Some user pages have refined variants (`analysis_view_refined.py`, `watchlist_view_refined.py`, `ranking_view_refined.py`) while others remain legacy Streamlit tables/forms.
  - Analysis result UX is richer than other pages but still Streamlit-widget driven.
  - Search-assisted complex registration exists through JUSO, but it is embedded in the complex CRUD page rather than a dedicated user-facing search home.
- `Missing`
  - Shared design system and reusable visual tokens
  - React rendering layer
  - Python-to-React view-model adapter layer
  - Screen-level component packaging for Streamlit Components v2
  - Dedicated saved-analysis screen

### App shell and routing

- [app.py](/D:/CodexProject/estate-pulse/app.py) initializes every repository and service in one place, then routes by sidebar `radio`.
- Routing is manual, not Streamlit multipage-native.
- User pages and admin pages share the same runtime composition root.
- Sidebar labels are hardcoded in `app.py`, which couples navigation text, route selection, and renderer selection.

### UI module inventory

- Large user-facing Streamlit files:
  - [modules/ui/analysis_view.py](/D:/CodexProject/estate-pulse/modules/ui/analysis_view.py)
  - [modules/ui/analysis_view_refined.py](/D:/CodexProject/estate-pulse/modules/ui/analysis_view_refined.py)
  - [modules/ui/dashboard.py](/D:/CodexProject/estate-pulse/modules/ui/dashboard.py)
  - [modules/ui/comparison_view.py](/D:/CodexProject/estate-pulse/modules/ui/comparison_view.py)
  - [modules/ui/watchlist_view_refined.py](/D:/CodexProject/estate-pulse/modules/ui/watchlist_view_refined.py)
  - [modules/ui/ranking_view_refined.py](/D:/CodexProject/estate-pulse/modules/ui/ranking_view_refined.py)
- CRUD-oriented Streamlit forms:
  - [modules/ui/complex_form.py](/D:/CodexProject/estate-pulse/modules/ui/complex_form.py)
  - [modules/ui/listing_form.py](/D:/CodexProject/estate-pulse/modules/ui/listing_form.py)
  - [modules/ui/finance_profile_form.py](/D:/CodexProject/estate-pulse/modules/ui/finance_profile_form.py)
- Admin remains large and separate:
  - [modules/ui/admin_view.py](/D:/CodexProject/estate-pulse/modules/ui/admin_view.py)
  - [modules/ui/policy_event_admin_view.py](/D:/CodexProject/estate-pulse/modules/ui/policy_event_admin_view.py)
- Common UI module is effectively missing:
  - [modules/ui/__init__.py](/D:/CodexProject/estate-pulse/modules/ui/__init__.py) is empty.
  - Shared labels, tables, metric cards, and layout primitives are duplicated across page files.

### Current rendering characteristics

- Streamlit widgets, `st.dataframe`, `st.metric`, `st.expander`, `st.tabs`, and `plotly_chart` dominate the user experience.
- Visual composition is page-local rather than systemized.
- Repeated display formatting and label mapping live inside UI files.
- Analysis UI is especially monolithic:
  - [modules/ui/analysis_view.py](/D:/CodexProject/estate-pulse/modules/ui/analysis_view.py) is about 1,900 lines and mixes page composition, formatting, presentation decisions, and scenario UX.
  - [modules/ui/analysis_view_refined.py](/D:/CodexProject/estate-pulse/modules/ui/analysis_view_refined.py) still imports many helpers from the legacy analysis file, so the refined page is not independently bounded.

### UI to service/repository boundary status

- Good:
  - SQL is still isolated in repositories.
  - Main calculation logic remains in analyzers and services.
- Weak points:
  - CRUD pages directly call repositories from Streamlit views instead of going through a page-specific adapter layer.
  - User-facing rendering consumes raw repository/service rows and reshapes them inline.
  - Session state keys are scattered in page modules, especially complex registration and analysis pages.
  - There is no explicit UI view-model contract between Python and the renderer.

### Current page-by-page dependency boundary

- Dashboard
  - Directly reads `analysis_repository.list_recent()`
  - Directly reads `policy_event_service.list_high_impact_events()`
- Complex page
  - Uses `address_search_service` and `complex_registration_service`
  - Also directly calls `complex_repository.create/update/delete/list_all()`
- Listing page
  - Directly calls `complex_repository.list_all()` and `listing_repository.create/update/delete/list_all()`
- Finance profile page
  - Directly calls `finance_repository.create/update/delete/list_all()`
- Analysis page
  - Reads repository lists for selection
  - Uses `analysis_service` for transaction context and analysis execution
  - Reads `analysis_repository.list_recent()` for history
- Watchlist, comparison, ranking
  - Mix direct repository reads with `opportunity_service`

### Tooling and runtime status

- Python dependency file exists: [requirements.txt](/D:/CodexProject/estate-pulse/requirements.txt)
- No root `pyproject.toml`
- No `package.json`
- No frontend workspace
- No Vite config
- Installed Python version confirmed locally on July 19, 2026: `3.9.6`
- Installed Streamlit version confirmed locally: `1.50.0`
- Installed Node version confirmed locally: `v20.18.0`
- Installed npm version confirmed locally: `10.8.2`

### Implementation gate

- The current local Python runtime is `3.9.6`.
- Official Streamlit package-based Components v2 documentation requires `Python >= 3.10` and `Node.js >= 24 (LTS)`.
- Because the current Python runtime is lower than `3.10`, Phase 1 implementation must not proceed in this environment.
- Before implementation can start, the project runtime must be upgraded to a supported Python version, then Streamlit and Node updates can be applied on top of that.

### Streamlit Components v2 feasibility

- Official Streamlit documentation currently recommends Components v2 for new custom components and supports package-based components with TypeScript and Vite.
- However, the current project runtime is not yet ready for that target:
  - The package-based Components v2 template requires `Python >= 3.10`.
  - Streamlit `1.50.0` does not expose `st.components.v2.component`.
  - Streamlit Components v2 was announced in Streamlit `1.51.0`.
  - Official package-based component docs currently list `Node.js >= 24` as the template prerequisite.
- Conclusion:
  - Vite is the correct build strategy for the target architecture.
  - The target environment is explicitly:
    - Python `>=3.10`
    - Streamlit `>=1.51,<2.0`
    - Node.js `24 LTS`
  - Vite is not immediately usable in the current repository environment as-is because both Python and Node are below the required floor.

### Current test execution status

- Documented command:
  - `$env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python -B -m unittest discover -s tests -v`
- Actual run on July 19, 2026:
  - `249` tests executed
  - `246` passed
  - `3` failed in PostgreSQL smoke tests because `TEST_DATABASE_URL` was not set
- Implication:
  - Core Python logic is broadly covered and stable enough for UI-only migration.
  - PostgreSQL smoke verification requires environment setup during implementation validation.

### Current git state

- `git status --short`: clean worktree
- Recent commits:
  - `94222696` Refine estate analysis flow and add supporting tests
  - `f8b4d24e` Implement property analysis and cash calculation flow
  - `9d6b33b6` Clarify Codex and architecture guidance

## Areas That Must Not Change

- Existing repository interfaces unless absolutely required for serialization convenience
- Existing service orchestration and analyzer calculations
- Existing DB schema and persistence behavior
- SQLite fallback and PostgreSQL runtime support
- Admin pages, policy management pages, and debugging/operator workflows
- Existing JUSO, MOLIT, policy-event, and loan-rule runtime behavior
- Existing test semantics for calculation and persistence layers

## Recommended Architecture

### Recommendation

- Keep Streamlit as the application shell and orchestration layer.
- Add a single package-based custom component package that contains a shared React bundle and screen-level React entry components.
- Introduce a thin Python page-adapter and view-model layer between Streamlit pages and React.
- Keep existing legacy Streamlit pages available behind a feature flag for rollback.

### Why this structure

- It preserves the current Python business boundary.
- It avoids React-to-DB and React-to-service coupling.
- It introduces a clean serializer boundary that the current UI does not have.
- It lets the team migrate page by page instead of rewriting the whole app at once.
- It prevents a component explosion by rendering full screens rather than micro-components per card.

## Target Architecture

```text
Streamlit Shell
  - app.py
  - route selection
  - session_state
  - repository/service composition
  - feature flags / fallback routing

Python UI Adapter Layer
  - page controller per React screen
  - view-model builders
  - action dispatch handlers
  - formatting helpers for display-safe payloads

Streamlit Components v2 Package
  - one shared component package
  - one shared design system
  - screen-level React roots:
    - SearchHome
    - AnalysisDashboard
    - ComparisonDashboard
    - SavedAnalysisDashboard

Existing Python Domain
  - services
  - repositories
  - analyzers
  - config
```

### Integration model

- Streamlit owns:
  - routing
  - session state
  - service calls
  - persistence writes
  - fallback rendering
- React owns:
  - screen composition
  - design system consumption
  - responsive layout
  - UI-only local state such as selected tab, disclosure state, sort presentation, and transient input drafts
- Python-to-React data exchange is view-model only.
- React-to-Python communication is event payload only.

### Recommended package layout

```text
estate-pulse/
  app.py
  config/
  modules/
    ui/
      react_bridge.py
      pages/
        search_home_page.py
        analysis_dashboard_page.py
        comparison_dashboard_page.py
        saved_analysis_page.py
      viewmodels/
        common.py
        search_home.py
        analysis_dashboard.py
        comparison_dashboard.py
        saved_analysis.py
  commercial_ui/
    pyproject.toml
    component.py
    frontend/
      package.json
      tsconfig.json
      vite.config.ts
      src/
        renderers/
          SearchHomeRenderer.tsx
          AnalysisDashboardRenderer.tsx
          ComparisonDashboardRenderer.tsx
          SavedAnalysisRenderer.tsx
        components/
        design-system/
        contracts/
        formatters/
```

## Files To Create or Modify and Their Responsibilities

### Phase 1 limit

- Only `SearchHome` and the supporting shared component infrastructure are implemented in Phase 1.
- `AnalysisDashboard`, `ComparisonDashboard`, and `SavedAnalysisDashboard` remain design-only in this phase.

### Python app shell

- Modify [app.py](/D:/CodexProject/estate-pulse/app.py)
  - Keep dependency composition in one place.
  - Replace direct renderer mapping for target pages with page-controller functions.
  - Keep legacy page renderers registered for fallback.

- Modify [config/settings.py](/D:/CodexProject/estate-pulse/config/settings.py)
  - Add a UI renderer mode or per-page feature-flag setting.
  - Suggested values: `legacy`, `react`, `mixed`.

- Modify [requirements.txt](/D:/CodexProject/estate-pulse/requirements.txt)
  - Raise Streamlit floor to a Components v2-capable version.

### Python UI adapter layer

- Create `modules/ui/react_bridge.py`
  - Shared helper that mounts the custom component package.
  - Handles missing asset/build fallback to legacy Streamlit renderer.

- Create `modules/ui/pages/search_home_page.py`
  - Builds the Search Home view model from existing repositories/services.
  - Handles search/home page events and route transitions.

- Create `modules/ui/viewmodels/common.py`
  - Shared typed builders for money, percent, score, badge, table row, disclosure block, and nav item payloads.

- Create `modules/ui/viewmodels/search_home.py`
  - Search home serializer only.

### Streamlit component package

- Create `commercial_ui/pyproject.toml`
  - Python package metadata for editable install and distribution.

- Create `commercial_ui/component.py`
  - Python wrapper around `st.components.v2.component(...)`.
  - Exposes a single render function receiving `{page, view_model, ui_state}`.

- Create `commercial_ui/frontend/package.json`
  - React, TypeScript, Vite, testing scripts.

- Create `commercial_ui/frontend/vite.config.ts`
  - Streamlit-compatible relative asset output and hashed filenames.

- Create `commercial_ui/frontend/src/contracts/index.ts`
  - Frontend TypeScript interfaces mirroring Python view-model envelopes and event payloads.

- Create `commercial_ui/frontend/src/design-system/tokens.css`
  - Design tokens and CSS custom properties.

- Create `commercial_ui/frontend/src/design-system/theme.ts`
  - Theme helpers and utility mappings for status/score tones.

- Create `commercial_ui/frontend/src/index.tsx`
  - Shared component bootstrap and screen switch.

- Create `commercial_ui/frontend/src/renderers/SearchHomeRenderer.tsx`
  - Search home screen composition only.

### Tests

- Create `tests/test_ui_viewmodels.py`
  - Unit tests for Python serializer contracts and fallback-safe display fields.

- Create `tests/test_ui_page_controllers.py`
  - Unit tests for page event dispatch and session-state transitions.

- Create `commercial_ui/frontend/src/renderers/SearchHomeRenderer.test.tsx`
  - Frontend rendering tests for empty, loaded, and error-safe SearchHome states.

## Python <-> React Data Contract

### Contract rules

- React receives only serializable data.
- React never receives repository or service objects.
- React never computes business outputs.
- Python remains the source of truth for calculations, score meaning, confidence labels, and persistence-side identifiers.
- Critical money/score/date fields should include both raw and display-ready values to minimize formatting drift.

### Common envelope

```json
{
  "version": 1,
  "page": "analysis_dashboard",
  "view_model": {},
  "ui_state": {},
  "capabilities": {},
  "meta": {
    "generated_at": "2026-07-19T21:30:00+09:00",
    "locale": "ko-KR"
  }
}
```

### Common event payload

```json
{
  "type": "run_analysis",
  "payload": {
    "profile_id": 3,
    "complex_id": 12,
    "area_bucket": 84.9
  }
}
```

### Search Home view-model

- Navigation summary
- Service message / hero copy
- Search box state
- Registered complex suggestions
- Optional JUSO-powered address suggestions when enabled
- Recent analysis cards
- Empty-state blocks
- Quick actions linking to legacy CRUD pages where needed

Suggested shape:

```json
{
  "hero": {
    "title": "지금 검토할 단지를 빠르게 찾기",
    "subtitle": "기존 분석과 저장된 단지, 주소 검색을 한 화면에서 정리"
  },
  "search": {
    "query": "",
    "status": "idle",
    "results": []
  },
  "recent_analyses": [],
  "quick_links": []
}
```

### Analysis Dashboard view-model

- Header:
  - complex name
  - area bucket
  - selected price basis
  - reference date
  - confidence
- Summary metrics:
  - required cash
  - expected loan
  - shortage cash
  - investment score
  - monthly repayment when applicable
- Decision block:
  - final sentence
  - buyability tone
  - caution badges
- Tabs:
  - overall analysis
  - financing plan
  - price analysis
  - investment analysis
  - risk
- Disclosure blocks for raw source tables and applied rules

### Comparison Dashboard view-model

- Selected finance profile summary
- Selected 2 to 3 candidates
- Headline recommendation sentence
- Difference-first metric matrix
- Per-metric winner/highlight metadata
- Folded raw-detail section with original source context

### Saved Analysis Dashboard view-model

- List/card mode toggle
- Saved analysis cards with:
  - complex name
  - area
  - analyzed date
  - price basis
  - key cash metric
  - score
  - decision summary
- Optional detail drawer or separate routed detail state

## Page-Level Component Trees

### Search Home

- `AppShellFrame`
- `SearchHomeScreen`
- `HeroPanel`
- `UnifiedSearchBar`
- `SearchResultState`
- `RecentAnalysisRail`
- `QuickActionStrip`
- `EmptyStatePanel`

### Analysis Dashboard

- `AppShellFrame`
- `AnalysisDashboardScreen`
- `AnalysisHeader`
- `MetricScoreStrip`
- `DecisionBanner`
- `AnalysisTabNav`
- `OverviewTab`
- `FinancingTab`
- `PriceTab`
- `InvestmentTab`
- `RiskTab`
- `SourceDisclosure`
- `RawDataDisclosure`

### Comparison Dashboard

- `AppShellFrame`
- `ComparisonDashboardScreen`
- `SelectionBar`
- `ComparisonHeadline`
- `MetricDifferenceBoard`
- `CandidateSummaryCards`
- `DetailedSourceDisclosure`

### Saved Analysis Dashboard

- `AppShellFrame`
- `SavedAnalysisDashboardScreen`
- `FilterBar`
- `ViewModeToggle`
- `AnalysisCardList`
- `AnalysisCard`
- `AnalysisListTable`
- `EmptyStatePanel`

## Design Tokens

### Typography

- Primary: `Pretendard Variable`, fallback `Noto Sans KR`, sans-serif
- Numeric/meta: `JetBrains Mono`, monospace
- Scale:
  - `--font-display`: 40px
  - `--font-h1`: 32px
  - `--font-h2`: 24px
  - `--font-h3`: 18px
  - `--font-body`: 15px
  - `--font-meta`: 13px

### Color system

- Base
  - `--color-bg`: `#F5F2EA`
  - `--color-surface`: `#FFFCF7`
  - `--color-surface-strong`: `#F0EBE1`
  - `--color-ink`: `#1E2732`
  - `--color-muted`: `#667281`
  - `--color-border`: `#D7D0C3`
- Brand / emphasis
  - `--color-primary`: `#0F766E`
  - `--color-primary-soft`: `#D9F0EC`
  - `--color-accent`: `#C26B2E`
  - `--color-accent-soft`: `#F7E5D6`
- Status
  - `--color-success`: `#1D7A46`
  - `--color-warning`: `#B7791F`
  - `--color-danger`: `#B42318`
  - `--color-info`: `#2563EB`
- Score tones
  - `--score-strong`: `#0B6E4F`
  - `--score-mid`: `#997404`
  - `--score-weak`: `#B93815`

### Spacing

- `--space-1`: 4px
- `--space-2`: 8px
- `--space-3`: 12px
- `--space-4`: 16px
- `--space-5`: 24px
- `--space-6`: 32px
- `--space-7`: 48px

### Radius

- `--radius-sm`: 10px
- `--radius-md`: 16px
- `--radius-lg`: 24px
- `--radius-pill`: 999px

### Shadow

- `--shadow-sm`: `0 6px 18px rgba(23, 31, 38, 0.06)`
- `--shadow-md`: `0 16px 40px rgba(23, 31, 38, 0.10)`
- `--shadow-lg`: `0 28px 60px rgba(23, 31, 38, 0.14)`

## State Management

### Streamlit-owned state

- Active route
- Selected finance profile id
- Selected complex id / listing id / area bucket
- Last successful analysis result snapshot for current route
- Comparison selected candidate ids
- Saved-analysis selected row/detail target
- Search keyword and result cache
- Feature flag determining legacy vs React renderer

### React-owned local state

- Active tab
- Open/closed disclosures
- Local sort presentation
- Hover/focus-visible UI state
- Non-persistent filter input drafts before submit

### State flow rule

- React emits an event.
- Python validates and mutates `st.session_state`.
- Python calls the existing service/repository layer if needed.
- Python rebuilds the view model and reruns.
- React re-renders from the new serialized payload.

## Step-by-Step Migration Strategy

### Stage 0: Preconditions

- Upgrade Python to `>=3.10`.
- Upgrade Streamlit to `>=1.51,<2.0`.
- Upgrade Node to `24 LTS`.
- Confirm the team accepts a subpackage frontend workspace inside this repository.

### Stage 1: Shell and bridge

- Add the `commercial_ui/` package and Python wrapper.
- Add feature-flag fallback to keep the current `Dashboard` live.
- Introduce the `SearchHome` view-model builder and event adapter without changing business logic.
- Implement only the React `SearchHome` renderer in this phase.

### Stage 2: Search Home

- Replace the current dashboard-first landing experience with the Search Home React screen.
- Preserve access to recent analyses and existing search/registration paths.

### Stage 3: Analysis Dashboard

- Deferred to a later phase.

### Stage 4: Comparison Dashboard

- Deferred to a later phase.

### Stage 5: Saved Analysis Dashboard

- Deferred to a later phase.

### Stage 6: Stabilization

- Regression test legacy and React modes side by side.
- Keep complex/listing/finance/admin pages on Streamlit until the React core screens are accepted.

## Test Strategy

### Python tests

- Keep running the existing `unittest` suite.
- Add serializer tests for every view-model builder.
- Add controller tests for event dispatch, invalid payload rejection, and session-state transitions.
- Add page fallback tests to ensure legacy renderers still work when the component bundle is missing.

### Frontend tests

- Use `vitest` + React Testing Library.
- Cover:
  - empty state
  - loaded state
  - tab switching
  - disclosure behavior
  - event payload emission
  - responsive collapse behavior for comparison and saved-analysis lists

### Manual verification

- Streamlit run with legacy mode
- Streamlit run with React mode
- JUSO key missing state
- analysis result with buyable and non-buyable cases
- comparison with 2 and 3 candidates
- saved history with legacy snapshot fallback rows

### DB/runtime validation

- Re-run the existing unittest suite.
- Re-run PostgreSQL smoke tests when `TEST_DATABASE_URL` is configured.

## Accessibility Criteria

- Keyboard-operable navigation, tabs, buttons, disclosures, and selectable cards
- Visible focus state on every interactive control
- Minimum text contrast of WCAG AA
- Semantic heading order per screen
- `aria-live` region for analysis verdict changes and validation feedback
- Tabs use proper tablist, tab, and tabpanel semantics
- Touch targets at least 44px high
- Reduced-motion support for non-essential transitions
- Comparison highlights conveyed by text and iconography, not color alone

## Desktop and Narrow-Screen Behavior

### Desktop

- 12-column grid
- Summary metrics displayed in one row where space allows
- Comparison screen uses side-by-side diff matrix
- Saved analyses default to card grid or wide list view

### Narrow screens

- Breakpoints:
  - `<= 1280px`: compact cards
  - `<= 960px`: stack summary strips and collapse auxiliary panels
  - `<= 640px`: single-column layout
- Comparison screen collapses to candidate-by-candidate stacked sections on narrow screens
- Raw data tables move behind folded disclosures
- Sticky action/footer controls are allowed only when they do not hide content

## Existing Function Regression Risks

- Python `3.9.6` is below the minimum runtime required by the chosen Components v2 package-based architecture.
- Streamlit `1.50.0` cannot host Components v2, so version drift is the first implementation risk.
- Node `20.18.0` does not match the current official package-based template prerequisite.
- Analysis result formatting may drift if React re-implements money/score/date display without Python-backed contracts.
- Session-state mismatches can cause stale screen selection or incorrect rerender behavior.
- The current refined analysis page depends on helpers from the legacy analysis file, so partial migration can leave hidden coupling.
- Watchlist/ranking/dashboard concepts overlap; route and information architecture changes can unintentionally hide existing behavior if not mapped explicitly.
- Legacy history rows depend on snapshot-first plus live fallback behavior; the React UI must preserve that distinction.

## Rollback Strategy

- Keep all existing Streamlit pages intact during migration.
- Add a renderer feature flag:
  - `legacy`: always use current Streamlit page
  - `react`: use React screen for supported routes
  - `mixed`: page-by-page rollout
- For each target page, route-level fallback should be:
  - try React bridge
  - if component package unavailable or payload build fails, render current legacy page
- Do not delete the legacy page files until full acceptance and regression sign-off are complete.

## Implementation Readiness

- Product and architecture decisions are now fixed.
- The only blocking runtime prerequisite is Python.
- Implementation can begin only after the local runtime is upgraded from `3.9.6` to `>=3.10`.
