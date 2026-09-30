# Commercial AnalysisDashboard Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the commercial `AnalysisDashboard` flow for SearchHome and saved analyses without changing analysis calculations, while routing comparison back to the existing comparison page.

**Architecture:** Streamlit owns one canonical commercial page-state object and routes between commercial SearchHome, commercial AnalysisDashboard, and the existing legacy comparison page. Python loads, saves, and adapts resolved analysis results into a typed `AnalysisViewModel`; React renders the analysis UI and emits typed triggers only.

**Tech Stack:** Python 3.14.6, Streamlit 1.59.0, unittest, React 19.1.1, TypeScript 5.8.3, Vitest 3.2.4, Playwright 1.54.2.

## Current Checkpoint

- Implemented: canonical commercial page state, SearchHome-to-analysis flow, saved snapshot lookup, save-without-recompute, AnalysisDashboard ViewModel/renderer, typed triggers, and legacy comparison handoff.
- Verified: non-PostgreSQL Python suite, frontend typecheck/lint/tests/build, and commercial Streamlit startup health.
- Remaining: additional renderer loading/partial/error coverage, AnalysisDashboard visual capture and responsive review, and PostgreSQL smoke verification when `TEST_DATABASE_URL` is available.
- MVP decision: the verified legacy comparison handoff is accepted for the first release; a native Commercial comparison screen is post-MVP.
- Status source: `docs/COMMERCIAL_UI.md`; this plan remains active only for the verification items above.

## Global Constraints

- Keep `AnalysisService`, repositories, and analyzers as the source of business logic.
- Do not move DB access, external access, or calculation logic into React.
- `AnalysisRepository.list_recent(limit=4)` is for SearchHome recent cards only.
- Saved AnalysisDashboard detail must come from `analysis_id` snapshot data only.
- `save_requested` must persist the current `active_analysis_result` without rerunning analysis or refreshing transaction/external data.
- Use `area_bucket: float` as the only area contract for commercial analysis requests.
- Legacy comparison has no preselection session contract; do not invent one.
- Do not implement `ComparisonDashboard` or `SavedAnalysisDashboard`.
- Commit or push only when the user explicitly requests it.

---

### Task 1: Add canonical commercial page state

**Files:**
- Create: `modules/ui/commercial_page_state.py`
- Modify: `modules/ui/search_home_page.py`
- Test: `tests/test_commercial_page_state.py`
- Test: `tests/test_search_home_page.py`

**Interfaces:**
- `COMMERCIAL_PAGE_STATE_KEY = "commercial_page_state"`
- `CommercialPageState`
- `ResolvedAnalysisResultDict`
- `PendingAnalysisRequestDict`
- `PageNoticeDict`
- `load_commercial_page_state(session_state: dict[str, object]) -> CommercialPageState`
- `save_commercial_page_state(session_state: dict[str, object], state: CommercialPageState) -> None`

- [ ] Write failing tests for default state and state round-trip.
- [ ] Run `.\.venv314\Scripts\python -B -m unittest tests.test_commercial_page_state tests.test_search_home_page -v` and confirm red.
- [ ] Implement the typed state module and migrate SearchHome to use it.
- [ ] Re-run the same tests until green.

### Task 2: Add snapshot lookup and save-completed-result flow

**Files:**
- Modify: `modules/repositories/analysis_repository.py`
- Modify: `modules/services/analysis_service.py`
- Test: `tests/test_analysis_service_phase2.py`
- Create: `tests/test_analysis_repository_detail.py`

**Interfaces:**
- `AnalysisRepository.get_by_id(analysis_id: int) -> AnalysisSnapshotRow | None`
- `AnalysisService.save_completed_analysis_result(active_result: ResolvedAnalysisResultDict) -> int`

- [ ] Write failing tests that:
  - save one analysis with `save_result=True` and assert `get_by_id()` returns that row
  - call `save_completed_analysis_result()` on a `save_result=False` live result while `AnalysisService._resolve_analysis_subject` is patched to raise, proving no recomputation path is used
- [ ] Run `.\.venv314\Scripts\python -B -m unittest tests.test_analysis_service_phase2 tests.test_analysis_repository_detail -v` and confirm red.
- [ ] Implement `get_by_id()` and `save_completed_analysis_result()` using the existing snapshot schema and `analysis_repository.create(...)`.
- [ ] Re-run the same tests until green.

### Task 3: Build the analysis ViewModel

**Files:**
- Create: `modules/ui/viewmodels/analysis_dashboard.py`
- Create: `tests/test_analysis_dashboard_viewmodel.py`

**Interfaces:**
- `build_analysis_dashboard_view_model_from_live_result(result: ResolvedAnalysisResultDict) -> dict[str, object]`
- `build_analysis_dashboard_view_model_from_saved_row(row: AnalysisSnapshotRow) -> dict[str, object]`

- [ ] Write failing tests for `None` versus `0` and partial data.
- [ ] Run `.\.venv314\Scripts\python -B -m unittest tests.test_analysis_dashboard_viewmodel -v` and confirm red.
- [ ] Implement the ViewModel builders.
- [ ] Re-run the same tests until green.

### Task 4: Connect SearchHome and the commercial analysis page

**Files:**
- Create: `modules/ui/commercial_analysis_page.py`
- Modify: `modules/ui/search_home_page.py`
- Modify: `app.py`
- Modify: `commercial_ui/component.py`
- Create: `tests/test_commercial_analysis_page.py`
- Modify: `tests/test_commercial_component_contract.py`

**Interfaces:**
- `render_commercial_analysis_page(*, analysis_repository, analysis_service) -> None`
- `handle_search_result_selected(*, session_state: dict[str, object], result_type: str, result_id: str) -> CommercialPageState`
- `handle_analysis_requested(*, session_state: dict[str, object], complex_id: int, area_bucket: float, listing_id: int | None) -> CommercialPageState`
- `handle_save_requested(*, session_state: dict[str, object], analysis_service, analysis_repository) -> CommercialPageState`

- [ ] Write failing tests for:
  - `recent_analysis_selected` opening saved detail by `analysis_id`
  - `save_requested` promoting a live result to `analysis_source="saved"` with a real `active_analysis_id`
  - component-call failure keeping `active_analysis_result` and exposing retry/navigation actions
- [ ] Run `.\.venv314\Scripts\python -B -m unittest tests.test_search_home_page tests.test_commercial_analysis_page tests.test_commercial_component_contract -v` and confirm red.
- [ ] Route commercial mode by `CommercialPageState` in `app.py`, wire analysis triggers in `commercial_ui/component.py`, and implement the page bridge.
- [ ] Re-run the same tests until green.

### Task 5: Add frontend contracts, analysis renderer, and React tests

**Files:**
- Create: `commercial_ui/frontend/src/contracts/searchHome.ts`
- Create: `commercial_ui/frontend/src/contracts/analysisDashboard.ts`
- Modify: `commercial_ui/frontend/src/contracts/index.ts`
- Modify: `commercial_ui/frontend/src/index.tsx`
- Create: `commercial_ui/frontend/src/renderers/AnalysisDashboardRenderer.tsx`
- Create: `commercial_ui/frontend/src/renderers/AnalysisDashboardRenderer.test.tsx`
- Create: `commercial_ui/frontend/src/components/analysis/AnalysisSectionNav.tsx`
- Create: `commercial_ui/frontend/src/components/analysis/DecisionHero.tsx`
- Create: `commercial_ui/frontend/src/components/analysis/RiskList.tsx`
- Modify: `commercial_ui/frontend/src/design-system/global.css`

**Interfaces:**
- `SearchHomeEnvelope`
- `AnalysisDashboardEnvelope`
- `CommercialUIEnvelope = SearchHomeEnvelope | AnalysisDashboardEnvelope`
- `CommercialUIState` with `analysis_requested`, `save_requested`, `comparison_requested`, and `back_to_search_requested`

- [ ] Write failing renderer tests for hero render, loading/partial/error states, save/comparison/back triggers, and `ErrorBoundary` actions.
- [ ] Run `cmd /c npm.cmd run test` from `commercial_ui/frontend` and confirm red.
- [ ] Split the contracts, add the `analysis-dashboard` branch in `src/index.tsx`, implement the analysis components under `components/analysis/`, and wrap the renderer in an `ErrorBoundary`.
- [ ] Re-run `cmd /c npm.cmd run test` from `commercial_ui/frontend` until green.

### Task 6: Add visual capture and run full verification

**Files:**
- Create: `commercial_ui/frontend/scripts/capture-analysis-dashboard.mjs`
- Modify: `commercial_ui/frontend/package.json`
- Modify: `tests/test_commercial_frontend_assets.py`

**Interfaces:**
- Screenshot output under `artifacts/commercial-ui/analysis-dashboard/`
- JSON evidence for console errors, overflow, heading counts, and metric-grid layout

- [ ] Add `visual:analysis-dashboard` to `commercial_ui/frontend/package.json`.
- [ ] Implement the capture script using `capture-search-home.mjs` as the structural reference.
- [ ] Run `.\.venv314\Scripts\python -B -m unittest discover -s tests -v`.
- [ ] Run `cmd /c npm.cmd run typecheck`, `cmd /c npm.cmd run lint`, `cmd /c npm.cmd run test`, and `cmd /c npm.cmd run build` from `commercial_ui/frontend`.
- [ ] Run `.\.venv314\Scripts\python -m streamlit run app.py`, then `cmd /c npm.cmd run visual:analysis-dashboard` from `commercial_ui/frontend`, and confirm the screenshots plus evidence file were created.

## Self-Review Checklist

- [ ] The plan uses `area_bucket` only, not `area_id`.
- [ ] No step reruns analysis to satisfy `save_requested`.
- [ ] No task invents a legacy comparison preload session key.
- [ ] No new analysis-screen automatic legacy fallback is introduced in this phase.
- [ ] The plan keeps `ComparisonDashboard` and `SavedAnalysisDashboard` out of scope.
- [ ] Verification commands match `AGENTS.md`.
