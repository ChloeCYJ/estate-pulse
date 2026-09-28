from __future__ import annotations

from dataclasses import dataclass
import logging
import re
import unicodedata

import streamlit as st

from modules.services.analysis_service import BenchmarkInputs
from modules.ui.commercial_page_state import (
    CommercialPageState,
    load_commercial_page_state,
    save_commercial_page_state,
)
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
    analysis_service,
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
    commercial_state = load_commercial_page_state(st.session_state)
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
        pending_analysis=_build_pending_analysis_view_model(
            commercial_state=commercial_state,
            analysis_service=analysis_service,
            finance_repository=finance_repository,
        ),
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
        finance_repository=finance_repository,
        analysis_service=analysis_service,
        complex_repository=complex_repository,
        address_search_service=address_search_service,
    ):
        st.rerun()


def handle_recent_analysis_selected(*, session_state: dict[str, object], analysis_id: str) -> None:
    session_state[SEARCH_HOME_SELECTED_ANALYSIS_ID_KEY] = str(analysis_id)
    current_state = load_commercial_page_state(session_state)
    save_commercial_page_state(
        session_state,
        CommercialPageState(
            commercial_page="analysis_dashboard",
            analysis_source="saved",
            active_analysis_id=int(analysis_id) if str(analysis_id).strip().isdigit() else None,
            active_analysis_result=current_state.active_analysis_result,
            pending_analysis_request=None,
            page_notice=None,
            last_trigger="recent_analysis_selected",
        ),
    )


def handle_navigation_selected(*, session_state: dict[str, object], target: str) -> None:
    normalized_target = str(target or "").strip()
    session_state[SEARCH_HOME_NAVIGATION_TARGET_KEY] = normalized_target
    if normalized_target == NAVIGATION_TARGET_COMPARISON:
        session_state[SIDEBAR_USER_PAGE_KEY] = PAGE_COMPARISON
        return
    session_state[SIDEBAR_USER_PAGE_KEY] = PAGE_DASHBOARD


def handle_search_result_selected(
    *,
    session_state: dict[str, object],
    result_type: str,
    result_id: str,
    analysis_service,
) -> CommercialPageState:
    if str(result_type or "").strip() != "registered_complex":
        return load_commercial_page_state(session_state)

    complex_id = _parse_registered_complex_id(result_id)
    if complex_id is None:
        return load_commercial_page_state(session_state)

    area_options = analysis_service.list_complex_area_options(complex_id=complex_id)
    if not area_options:
        current_state = load_commercial_page_state(session_state)
        next_state = CommercialPageState(
            commercial_page="search_home",
            analysis_source=current_state.analysis_source,
            active_analysis_id=current_state.active_analysis_id,
            active_analysis_result=current_state.active_analysis_result,
            pending_analysis_request=None,
            page_notice={
                "level": "warning",
                "code": "analysis_target_unavailable",
                "message": "분석 가능한 면적 정보를 찾을 수 없습니다.",
            },
            last_trigger="search_result_selected",
        )
        save_commercial_page_state(session_state, next_state)
        return next_state

    first_area_bucket = float(area_options[0]["area_bucket"])
    current_state = load_commercial_page_state(session_state)
    next_state = CommercialPageState(
        commercial_page="search_home",
        analysis_source=current_state.analysis_source,
        active_analysis_id=current_state.active_analysis_id,
        active_analysis_result=current_state.active_analysis_result,
        pending_analysis_request={
            "request_kind": "complex_area_analysis",
            "complex_id": complex_id,
            "area_bucket": first_area_bucket,
            "listing_id": None,
        },
        page_notice=None,
        last_trigger="search_result_selected",
    )
    save_commercial_page_state(session_state, next_state)
    return next_state


def handle_analysis_requested(
    *,
    session_state: dict[str, object],
    complex_id: int,
    area_bucket: float,
    listing_id: int | None,
    analysis_service,
    finance_repository,
) -> CommercialPageState:
    requested_payload = {
        "request_kind": "complex_area_analysis",
        "complex_id": int(complex_id),
        "area_bucket": float(area_bucket),
        "listing_id": int(listing_id) if listing_id is not None else None,
    }
    current_state = load_commercial_page_state(session_state)
    current_page_state = build_search_home_page_state(session_state)

    if (
        current_page_state.search_status == SEARCH_STATUS_LOADING
        and current_state.pending_analysis_request == requested_payload
    ):
        return _execute_pending_analysis_request(
            session_state=session_state,
            requested_payload=requested_payload,
            analysis_service=analysis_service,
            finance_repository=finance_repository,
        )

    next_state = CommercialPageState(
        commercial_page="search_home",
        analysis_source=current_state.analysis_source,
        active_analysis_id=current_state.active_analysis_id,
        active_analysis_result=current_state.active_analysis_result,
        pending_analysis_request=requested_payload,
        page_notice=None,
        last_trigger="analysis_requested",
    )
    save_commercial_page_state(session_state, next_state)
    _persist_search_home_page_state(
        session_state,
        SearchHomePageState(
            search_query=current_page_state.search_query,
            search_status=SEARCH_STATUS_LOADING,
            search_results=current_page_state.search_results,
            display_error=None,
        ),
    )
    return next_state


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


def _handle_component_events(
    *,
    component_result,
    finance_repository,
    analysis_service,
    complex_repository,
    address_search_service,
) -> bool:
    search_payload = _result_value(component_result, "search_submitted")
    if isinstance(search_payload, dict):
        search_state = handle_search_submitted(
            query=str(search_payload.get("query") or ""),
            complex_repository=complex_repository,
            address_search_service=address_search_service,
        )
        _persist_search_home_page_state(st.session_state, search_state)
        current_state = load_commercial_page_state(st.session_state)
        save_commercial_page_state(
            st.session_state,
            CommercialPageState(
                commercial_page=current_state.commercial_page,
                analysis_source=current_state.analysis_source,
                active_analysis_id=current_state.active_analysis_id,
                active_analysis_result=current_state.active_analysis_result,
                pending_analysis_request=None,
                page_notice=None,
                last_trigger="search_submitted",
            ),
        )
        return True

    recent_analysis_payload = _result_value(component_result, "recent_analysis_selected")
    if isinstance(recent_analysis_payload, dict):
        handle_recent_analysis_selected(
            session_state=st.session_state,
            analysis_id=str(recent_analysis_payload.get("analysis_id") or ""),
        )
        return True

    search_result_payload = _result_value(component_result, "search_result_selected")
    if isinstance(search_result_payload, dict):
        handle_search_result_selected(
            session_state=st.session_state,
            result_type=str(search_result_payload.get("result_type") or ""),
            result_id=str(search_result_payload.get("result_id") or ""),
            analysis_service=analysis_service,
        )
        return True

    analysis_payload = _result_value(component_result, "analysis_requested")
    if isinstance(analysis_payload, dict):
        handle_analysis_requested(
            session_state=st.session_state,
            complex_id=int(analysis_payload.get("complex_id") or 0),
            area_bucket=float(analysis_payload.get("area_bucket") or 0.0),
            listing_id=_to_optional_int(analysis_payload.get("listing_id")),
            analysis_service=analysis_service,
            finance_repository=finance_repository,
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


def _build_pending_analysis_view_model(
    *,
    commercial_state: CommercialPageState,
    analysis_service,
    finance_repository,
) -> dict[str, object] | None:
    pending_request = commercial_state.pending_analysis_request
    if not pending_request:
        return None

    complex_id = int(pending_request["complex_id"])
    area_options = analysis_service.list_complex_area_options(complex_id=complex_id)
    if not area_options:
        return None

    latest_profile = finance_repository.get_latest()
    normalized_options: list[dict[str, object]] = []
    for option in area_options:
        area_bucket = float(option["area_bucket"])
        listing_options = [
            {"listing_id": None, "label": "최근 거래 기준"},
            *[
                {
                    "listing_id": int(item["id"]),
                    "label": f"#{int(item['id'])} | {_format_money_label(item.get('sale_price'))}",
                }
                for item in analysis_service.list_matching_listings(
                    complex_id=complex_id,
                    area_m2=area_bucket,
                )
            ],
        ]
        normalized_options.append(
            {
                "area_bucket": area_bucket,
                "label": _format_area_label(area_bucket),
                "listing_count": int(option.get("listing_count") or 0),
                "sale_transaction_count": int(option.get("sale_transaction_count") or 0),
                "listing_options": listing_options,
            }
        )

    return {
        "complex_id": complex_id,
        "complex_name": str(area_options[0].get("complex_name") or "-"),
        "finance_profile_label": _finance_profile_label(latest_profile),
        "auto_submit": build_search_home_page_state(st.session_state).search_status == SEARCH_STATUS_LOADING,
        "selected_area_bucket": float(pending_request["area_bucket"]),
        "area_options": normalized_options,
    }


def _execute_pending_analysis_request(
    *,
    session_state: dict[str, object],
    requested_payload: dict[str, object],
    analysis_service,
    finance_repository,
) -> CommercialPageState:
    current_state = load_commercial_page_state(session_state)
    finance_profile = finance_repository.get_latest()
    if not finance_profile:
        next_state = CommercialPageState(
            commercial_page="search_home",
            analysis_source=current_state.analysis_source,
            active_analysis_id=current_state.active_analysis_id,
            active_analysis_result=current_state.active_analysis_result,
            pending_analysis_request=current_state.pending_analysis_request,
            page_notice=None,
            last_trigger="analysis_requested",
        )
        save_commercial_page_state(session_state, next_state)
        _persist_search_home_page_state(
            session_state,
            SearchHomePageState(
                search_query=build_search_home_page_state(session_state).search_query,
                search_status=SEARCH_STATUS_ERROR,
                search_results=build_search_home_page_state(session_state).search_results,
                display_error={
                    "code": "finance_profile_required",
                    "message": "자금 프로필을 먼저 등록해 주세요.",
                },
            ),
        )
        return next_state

    try:
        result = analysis_service.run_complex_area_analysis(
            complex_id=int(requested_payload["complex_id"]),
            area_m2=float(requested_payload["area_bucket"]),
            listing_id=_to_optional_int(requested_payload.get("listing_id")),
            finance_profile_id=int(finance_profile["id"]),
            benchmarks=BenchmarkInputs(analysis_mode="OWNER_OCCUPIED"),
            save_result=False,
        )
    except Exception as exc:
        LOGGER.exception(
            "Commercial SearchHome analysis failed [complex_id=%s area_bucket=%s listing_id=%s]",
            requested_payload["complex_id"],
            requested_payload["area_bucket"],
            requested_payload.get("listing_id"),
            exc_info=exc,
        )
        next_state = CommercialPageState(
            commercial_page="search_home",
            analysis_source=current_state.analysis_source,
            active_analysis_id=current_state.active_analysis_id,
            active_analysis_result=current_state.active_analysis_result,
            pending_analysis_request=current_state.pending_analysis_request,
            page_notice=None,
            last_trigger="analysis_requested",
        )
        save_commercial_page_state(session_state, next_state)
        _persist_search_home_page_state(
            session_state,
            SearchHomePageState(
                search_query=build_search_home_page_state(session_state).search_query,
                search_status=SEARCH_STATUS_ERROR,
                search_results=build_search_home_page_state(session_state).search_results,
                display_error={
                    "code": "analysis_failed",
                    "message": str(exc) or "분석을 완료하지 못했습니다.",
                },
            ),
        )
        return next_state

    next_state = CommercialPageState(
        commercial_page="analysis_dashboard",
        analysis_source="live",
        active_analysis_id=None,
        active_analysis_result=result,
        pending_analysis_request=None,
        page_notice=None,
        last_trigger="analysis_requested",
    )
    save_commercial_page_state(session_state, next_state)
    _persist_search_home_page_state(
        session_state,
        SearchHomePageState(
            search_query=build_search_home_page_state(session_state).search_query,
            search_status=SEARCH_STATUS_SUCCESS,
            search_results=build_search_home_page_state(session_state).search_results,
            display_error=None,
        ),
    )
    return next_state


def _parse_registered_complex_id(result_id: str) -> int | None:
    prefix, _, suffix = str(result_id or "").partition(":")
    if prefix != "complex":
        return None
    return _to_optional_int(suffix)


def _format_area_label(value: object) -> str:
    if value in (None, ""):
        return "-"
    return f"{float(value):.1f}m²"


def _format_money_label(value: object) -> str:
    if value in (None, ""):
        return "-"
    try:
        from modules.utils.money_utils import format_compact_won

        return format_compact_won(int(value))
    except (TypeError, ValueError):
        return "-"


def _finance_profile_label(profile: dict | None) -> str:
    if not profile:
        return "자금 프로필 필요"
    return f"최근 자금 프로필 #{int(profile['id'])}"


def _to_optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _result_value(component_result, field_name: str):
    if component_result is None:
        return None
    return getattr(component_result, field_name, None)
