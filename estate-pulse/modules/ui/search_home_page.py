from __future__ import annotations

from dataclasses import dataclass
import logging
import re
import unicodedata

import streamlit as st

from modules.ui.dashboard import render_dashboard_page
from modules.ui.page_ids import PAGE_COMPARISON, PAGE_DASHBOARD
from modules.ui.viewmodels.search_home import (
    SEARCH_STATUS_ERROR,
    SEARCH_STATUS_IDLE,
    SEARCH_STATUS_LOADING,
    SEARCH_STATUS_NO_RESULTS,
    SEARCH_STATUS_SUCCESS,
    build_search_home_view_model,
)


LOGGER = logging.getLogger(__name__)

SIDEBAR_USER_PAGE_KEY = "sidebar_user_page"
SEARCH_HOME_SELECTED_ANALYSIS_ID_KEY = "commercial_search_home_selected_analysis_id"
SEARCH_HOME_NAVIGATION_TARGET_KEY = "commercial_search_home_navigation_target"
SEARCH_HOME_QUERY_KEY = "commercial_search_home_query"
SEARCH_HOME_STATUS_KEY = "commercial_search_home_status"
SEARCH_HOME_RESULTS_KEY = "commercial_search_home_results"
SEARCH_HOME_DISPLAY_ERROR_KEY = "commercial_search_home_display_error"

NAVIGATION_TARGET_SEARCH = "search"
NAVIGATION_TARGET_COMPARISON = "comparison"
NAVIGATION_TARGET_SAVED_ANALYSES = "saved_analyses"


@dataclass(frozen=True)
class SearchHomePageState:
    search_query: str
    search_status: str
    search_results: list[dict]
    display_error: dict[str, str] | None


def build_search_home_page_state(session_state: dict[str, object]) -> SearchHomePageState:
    return SearchHomePageState(
        search_query=str(session_state.get(SEARCH_HOME_QUERY_KEY) or ""),
        search_status=str(session_state.get(SEARCH_HOME_STATUS_KEY) or SEARCH_STATUS_IDLE),
        search_results=list(session_state.get(SEARCH_HOME_RESULTS_KEY) or []),
        display_error=session_state.get(SEARCH_HOME_DISPLAY_ERROR_KEY),  # type: ignore[arg-type]
    )


def handle_search_submitted(
    *,
    query: str,
    complex_repository,
    address_search_service,
) -> SearchHomePageState:
    normalized_query = str(query or "").strip()
    registered_results = _search_registered_complexes(
        query=normalized_query,
        complex_rows=complex_repository.list_all(),
    )

    try:
        address_results = _search_address_candidates(
            query=normalized_query,
            address_search_service=address_search_service,
        )
    except Exception as exc:  # pragma: no cover - exercised in tests
        LOGGER.exception("Commercial SearchHome search failed", exc_info=exc)
        return SearchHomePageState(
            search_query=normalized_query,
            search_status=SEARCH_STATUS_ERROR,
            search_results=[],
            display_error={
                "code": "search_failed",
                "message": "검색 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            },
        )

    search_results = [*registered_results, *address_results]
    if not search_results:
        return SearchHomePageState(
            search_query=normalized_query,
            search_status=SEARCH_STATUS_NO_RESULTS,
            search_results=[],
            display_error=None,
        )
    return SearchHomePageState(
        search_query=normalized_query,
        search_status=SEARCH_STATUS_SUCCESS,
        search_results=search_results,
        display_error=None,
    )


def render_search_home_page(
    *,
    settings,
    complex_repository,
    listing_repository,
    finance_repository,
    analysis_repository,
    policy_event_service,
    address_search_service,
) -> None:
    if getattr(settings, "ui_mode", "legacy") != "commercial":
        render_dashboard_page(
            complex_repository=complex_repository,
            listing_repository=listing_repository,
            finance_repository=finance_repository,
            analysis_repository=analysis_repository,
            policy_event_service=policy_event_service,
        )
        return

    page_state = build_search_home_page_state(st.session_state)
    recent_analyses = _recent_analysis_cards_source(
        analysis_rows=analysis_repository.list_recent(limit=4),
        complex_repository=complex_repository,
    )
    view_model = build_search_home_view_model(
        search_query=page_state.search_query,
        search_status=page_state.search_status,
        recent_analyses=recent_analyses,
        search_results=page_state.search_results,
        display_error=page_state.display_error,
    )

    _render_pending_navigation_notice()

    try:
        from commercial_ui.component import render_commercial_ui

        component_result = render_commercial_ui(
            page="search-home",
            view_model=view_model,
            key="commercial-search-home",
        )
    except Exception as exc:  # pragma: no cover - exercised during smoke/fallback only
        LOGGER.exception("Commercial SearchHome render failed", exc_info=exc)
        st.error("Commercial SearchHome 렌더링에 실패해 기존 Dashboard로 전환합니다.")
        render_dashboard_page(
            complex_repository=complex_repository,
            listing_repository=listing_repository,
            finance_repository=finance_repository,
            analysis_repository=analysis_repository,
            policy_event_service=policy_event_service,
        )
        return

    if _handle_component_events(
        component_result=component_result,
        complex_repository=complex_repository,
        address_search_service=address_search_service,
    ):
        st.rerun()


def handle_recent_analysis_selected(*, session_state: dict[str, object], analysis_id: str) -> None:
    session_state[SEARCH_HOME_SELECTED_ANALYSIS_ID_KEY] = str(analysis_id)


def handle_navigation_selected(*, session_state: dict[str, object], target: str) -> None:
    normalized_target = str(target or "").strip()
    session_state[SEARCH_HOME_NAVIGATION_TARGET_KEY] = normalized_target
    if normalized_target == NAVIGATION_TARGET_COMPARISON:
        session_state[SIDEBAR_USER_PAGE_KEY] = PAGE_COMPARISON
        return
    session_state[SIDEBAR_USER_PAGE_KEY] = PAGE_DASHBOARD


def _search_registered_complexes(*, query: str, complex_rows: list[dict]) -> list[dict]:
    normalized_query = _normalize_search_text(query)
    if not normalized_query:
        return []

    results: list[dict] = []
    for row in complex_rows:
        haystacks = [
            row.get("name"),
            row.get("address"),
            " ".join(
                str(part or "").strip()
                for part in (row.get("sido"), row.get("sigungu"), row.get("dong"))
                if str(part or "").strip()
            ),
        ]
        if not any(normalized_query in _normalize_search_text(value) for value in haystacks):
            continue
        results.append(
            {
                "result_id": f"complex:{row.get('id')}",
                "result_type": "registered_complex",
                "title": str(row.get("name") or "-"),
                "subtitle": str(row.get("address") or "-"),
                "meta": "등록된 단지",
            }
        )
    return results[:8]


def _search_address_candidates(*, query: str, address_search_service) -> list[dict]:
    if len(str(query or "").strip()) < 2:
        return []
    candidates = address_search_service.search_candidates(keyword=query)
    return [
        {
            "result_id": f"address:{index}",
            "result_type": "address_candidate",
            "title": str(candidate.complex_name or "-"),
            "subtitle": str(candidate.road_address or candidate.jibun_address or "-"),
            "meta": "주소 검색 결과",
        }
        for index, candidate in enumerate(candidates, start=1)
    ][:8]


def _normalize_search_text(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    normalized = re.sub(r"\s+", "", normalized)
    return "".join(char for char in normalized if _is_search_character(char))


def _is_search_character(char: str) -> bool:
    category = unicodedata.category(char)
    return bool(category) and category[0] in {"L", "N"}


def _handle_component_events(*, component_result, complex_repository, address_search_service) -> bool:
    search_payload = _result_value(component_result, "search_submitted")
    if isinstance(search_payload, dict):
        st.session_state[SEARCH_HOME_STATUS_KEY] = SEARCH_STATUS_LOADING
        search_state = handle_search_submitted(
            query=str(search_payload.get("query") or ""),
            complex_repository=complex_repository,
            address_search_service=address_search_service,
        )
        _persist_search_home_page_state(st.session_state, search_state)
        return True

    recent_analysis_payload = _result_value(component_result, "recent_analysis_selected")
    if isinstance(recent_analysis_payload, dict):
        handle_recent_analysis_selected(
            session_state=st.session_state,
            analysis_id=str(recent_analysis_payload.get("analysis_id") or ""),
        )
        return True

    navigation_payload = _result_value(component_result, "navigation_selected")
    if isinstance(navigation_payload, dict):
        handle_navigation_selected(
            session_state=st.session_state,
            target=str(navigation_payload.get("target") or ""),
        )
        return True

    return False


def _persist_search_home_page_state(
    session_state: dict[str, object],
    state: SearchHomePageState,
) -> None:
    session_state[SEARCH_HOME_QUERY_KEY] = state.search_query
    session_state[SEARCH_HOME_STATUS_KEY] = state.search_status
    session_state[SEARCH_HOME_RESULTS_KEY] = state.search_results
    session_state[SEARCH_HOME_DISPLAY_ERROR_KEY] = state.display_error


def _recent_analysis_cards_source(*, analysis_rows: list[dict], complex_repository) -> list[dict]:
    location_cache: dict[int, str] = {}
    prepared_rows: list[dict] = []
    for row in analysis_rows:
        prepared = dict(row)
        complex_id = row.get("complex_id")
        location_label = "-"
        if isinstance(complex_id, int):
            if complex_id not in location_cache:
                complex_row = complex_repository.get(complex_id)
                location_cache[complex_id] = _location_label(complex_row)
            location_label = location_cache[complex_id]
        prepared["location_label"] = location_label
        prepared_rows.append(prepared)
    return prepared_rows


def _location_label(complex_row: dict | None) -> str:
    if not complex_row:
        return "-"
    parts = [
        str(complex_row.get("sido") or "").strip(),
        str(complex_row.get("sigungu") or "").strip(),
        str(complex_row.get("dong") or "").strip(),
    ]
    label = " ".join(part for part in parts if part)
    return label or "-"


def _render_pending_navigation_notice() -> None:
    target = str(st.session_state.get(SEARCH_HOME_NAVIGATION_TARGET_KEY) or "")
    if target == NAVIGATION_TARGET_SAVED_ANALYSES:
        st.info(
            "저장한 분석 전용 화면은 Phase 2에서 전환됩니다. 현재는 기존 Dashboard의 최근 분석 영역을 사용해 주세요."
        )
        st.session_state.pop(SEARCH_HOME_NAVIGATION_TARGET_KEY, None)


def _result_value(component_result, field_name: str):
    if component_result is None:
        return None
    return getattr(component_result, field_name, None)
