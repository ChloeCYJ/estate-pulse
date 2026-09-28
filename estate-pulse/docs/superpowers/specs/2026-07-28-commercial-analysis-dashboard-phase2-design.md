# Commercial AnalysisDashboard Phase 2 Design

## Implementation status

- The core design is implemented: canonical commercial state, live/saved AnalysisDashboard routing, snapshot-based reopen, save without recomputation, typed React events, and legacy comparison handoff.
- Phase 2 remains active until loading/partial/error coverage and AnalysisDashboard visual evidence are complete.
- SNS authentication and user-scoped personal finance management are a separate subsequent phase; the current finance-profile repository is not user-scoped.

## Adopted approach
- Adopt Python adapter + dedicated Commercial AnalysisDashboard + SearchHome connection.
- Keep `AnalysisService`, existing repository boundaries, legacy analysis pages, and the legacy comparison page intact.
- Do not build a hybrid Streamlit/React analysis screen.
- Do not add a new presenter layer or a new repository layer.
- Keep `SearchHome` and `AnalysisDashboard` as the only commercial pages in this phase.

## Canonical data source
- `AnalysisRepository.list_recent(limit=4)` remains SearchHome recent-analysis-card data only.
- Commercial AnalysisDashboard never reconstructs saved detail from `list_recent()` plus live metadata.
- New analysis detail uses the exact full result dict returned by `AnalysisService.run_analysis(...)` or `AnalysisService.run_complex_area_analysis(...)`.
- Saved analysis detail uses the saved row loaded by `analysis_id` and adapted from snapshot columns only.
- Check `AnalysisRepository` first for single-row lookup support; if missing, add only `AnalysisRepository.get_by_id(analysis_id: int) -> AnalysisSnapshotRow | None`.
- `save_requested` must not rerun analysis, recalculate metrics, or perform fresh transaction/external lookups.
- If current code cannot persist an already-computed result, add the smallest reuse-oriented service path: `AnalysisService.save_completed_analysis_result(active_result: ResolvedAnalysisResult) -> int`.

## Page/session state
- Use one canonical session object under `COMMERCIAL_PAGE_STATE_KEY = "commercial_page_state"`.
- Define it in `modules/ui/commercial_page_state.py` as a dataclass plus load/save helpers.
- Define exact support types in the same module:
  - `ResolvedAnalysisResult`
    - the normalized Python result shape used by Commercial AnalysisDashboard
  - `PendingAnalysisRequest`
    - `request_kind: "complex_area_analysis"`
    - `complex_id: int`
    - `area_bucket: float`
    - `listing_id: int | None`
  - `PageNotice`
    - `level: "info" | "warning" | "error"`
    - `code: str`
    - `message: str`
- State fields:
  - `commercial_page: "search_home" | "analysis_dashboard" | "legacy_comparison"`
  - `analysis_source: "live" | "saved" | None`
  - `active_analysis_id: int | None`
  - `active_analysis_result: ResolvedAnalysisResult | None`
  - `pending_analysis_request: PendingAnalysisRequest | None`
  - `page_notice: PageNotice | None`
  - `last_trigger: str | None`
- Triggers are events only. After each trigger, this session object is the single source of truth for the visible page.
- Do not let multiple keys independently choose SearchHome, AnalysisDashboard, or legacy comparison.

## Python/React responsibility
- Python owns session state, `AnalysisService` calls, saved-analysis loading, `AnalysisViewModel` building, save idempotency, navigation, and logging with trigger type plus `analysis_id`.
- React owns rendering, section-navigation UI state, trigger emission, responsive layout, focus handling, overflow safety, badges, and state presentation.
- React must not query repositories, recompute cash/price/score/policy logic, or synthesize saved analysis data from partial fields.

## Trigger and navigation
- SearchHome trigger payloads:
  - `recent_analysis_selected`: `{ analysis_id: string }`
  - `search_result_selected`: `{ result_type: "registered_complex" | "address_candidate", result_id: string }`
  - `analysis_requested`: `{ complex_id: number, area_bucket: number, listing_id: number | null }`
- SearchHome triggers:
  - `recent_analysis_selected { analysis_id }`: load saved row by `analysis_id`, build snapshot-only dashboard detail, set `analysis_dashboard / saved`.
  - `search_result_selected { result_type, result_id }`: resolve one `PendingAnalysisRequest` in Python using `area_bucket: float` as the area contract.
  - `analysis_requested { complex_id, area_bucket, listing_id }`: run the matching service method, persist the returned full result in `active_analysis_result`, set `analysis_dashboard / live`.
- AnalysisDashboard triggers:
  - `back_to_search_requested`: set `commercial_page = "search_home"`.
  - `save_requested`: if `analysis_source == "saved"` and `active_analysis_id` exists, no-op with notice `"이미 저장된 분석입니다."`; if `analysis_source == "live"`, persist the current `active_analysis_result` as-is, obtain `analysis_id`, reload via `get_by_id(analysis_id)`, rebuild saved dashboard detail, set `active_analysis_id`, switch to `analysis_dashboard / saved`.
  - `comparison_requested`: investigation result is that `modules/ui/comparison_view.py` has no session-state preselection contract. It accepts listing IDs as `int`, defaults to the first `min(5, len(listings))` widget options, keeps selection only through Streamlit widget state, and deduplicates submitted IDs in `OpportunityService.compare_listings()` with `dict.fromkeys(...)`. This phase therefore routes to the legacy comparison page without inventing a preload key or overwriting native selection behavior.
- SearchHome `saved_analyses` navigation remains out of scope and returns an in-app notice instead of a new commercial page.

## Error handling
- Add `modules/ui/commercial_analysis_page.py` as the Streamlit bridge for the commercial analysis screen.
- When `render_commercial_ui(page="analysis-dashboard", ...)` raises, log trigger type, `active_analysis_id`, and `analysis_source`.
- Keep `active_analysis_result` in session state and show a retry/error action surface instead of recomputing analysis.
- Provide `다시 시도` and `단지 검색으로 돌아가기` actions without infinite rerun behavior.
- In React, wrap `AnalysisDashboardRenderer` in an `ErrorBoundary` that shows `분석 화면을 불러오지 못했습니다.`, `다시 시도`, and `단지 검색으로 돌아가기`.
- Whole-app operational rollback remains `ESTATE_PLUS_UI_MODE=legacy`.

## File responsibility
- `modules/ui/commercial_page_state.py`: canonical commercial session-state dataclass, `PendingAnalysisRequest`, `PageNotice`, and helpers.
- `modules/ui/search_home_page.py`: SearchHome trigger handling and page-state transitions only.
- `modules/ui/commercial_analysis_page.py`: commercial analysis bridge, ViewModel assembly, trigger dispatch, save flow, and retry/error handling.
- `modules/ui/viewmodels/analysis_dashboard.py`: `AnalysisViewModel` schema and builders from live result dict or saved analysis row.
- `modules/repositories/analysis_repository.py`: add `get_by_id()` only if no existing single-row lookup exists.
- `modules/services/analysis_service.py`: add `save_completed_analysis_result(active_result: ResolvedAnalysisResult) -> int` only if needed to persist the current computed result without recomputation.
- `commercial_ui/component.py`: extend the component event contract for analysis dashboard triggers.
- `commercial_ui/frontend/src/contracts/index.ts`: shared envelope exports only.
- `commercial_ui/frontend/src/contracts/searchHome.ts`: SearchHome view model and trigger payload types.
- `commercial_ui/frontend/src/contracts/analysisDashboard.ts`: AnalysisDashboard view model and trigger payload types.
- `commercial_ui/frontend/src/renderers/AnalysisDashboardRenderer.tsx`: page-level analysis renderer.
- `commercial_ui/frontend/src/components/analysis/AnalysisSectionNav.tsx`: section navigation buttons.
- `commercial_ui/frontend/src/components/analysis/DecisionHero.tsx`: decision headline and key metrics.
- `commercial_ui/frontend/src/components/analysis/RiskList.tsx`: risk badges and evidence list.

## Scope and out of scope
- In scope:
  - commercial AnalysisDashboard
  - saved-analysis reopen by `analysis_id`
  - SearchHome to AnalysisDashboard flow
  - save trigger no-op/idempotency for already-saved analysis
  - comparison handoff into the existing comparison page
  - loading, partial-data, insufficient-data, and error states
- Out of scope:
  - ComparisonDashboard implementation
  - SavedAnalysisDashboard implementation
  - new calculations or changed formulas
  - DB schema redesign
  - generic presenter layer
  - removing legacy analysis pages

## Test strategy
- Python unit tests:
  - `AnalysisRepository.get_by_id()` lookup if added
  - `save_completed_analysis_result()` persists the current result without recomputation
  - saved analysis adapts from snapshot-only data without live transaction recomposition
  - `recent_analysis_selected` opens saved detail by `analysis_id`
  - `analysis_requested` opens live detail from the exact service result
  - `save_requested` is no-op for already-saved analysis
  - `comparison_requested` routes to the existing comparison page without inventing preload state
  - component-call failure keeps `active_analysis_result` and exposes retry/navigation actions
- Frontend tests:
  - `AnalysisDashboardRenderer` header, hero, sections, risk severity, loading, partial, and error states
  - save/comparison/back triggers and `ErrorBoundary` actions
  - keyboard navigation and mobile layout
- Visual verification:
  - add a Playwright capture script for the required desktop/mobile AnalysisDashboard screenshots
  - verify no horizontal overflow, no console errors, and no asset 404s
