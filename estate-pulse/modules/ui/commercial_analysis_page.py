from __future__ import annotations

import logging

import streamlit as st

from commercial_ui.component import render_commercial_ui
from modules.ui.commercial_page_state import (
    CommercialPageState,
    load_commercial_page_state,
    save_commercial_page_state,
)
from modules.ui.viewmodels.analysis_dashboard import (
    build_analysis_dashboard_view_model_from_live_result,
    build_analysis_dashboard_view_model_from_saved_row,
)


LOGGER = logging.getLogger(__name__)


def render_commercial_analysis_page(*, analysis_repository, analysis_service) -> None:
    state = load_commercial_page_state(st.session_state)
    view_model = _build_view_model(
        state=state,
        analysis_repository=analysis_repository,
    )

    try:
        component_result = render_commercial_ui(
            page="analysis-dashboard",
            view_model=view_model,
            key="commercial-analysis-dashboard",
            frontend_state={
                "analysis_source": state.analysis_source,
                "active_analysis_id": state.active_analysis_id,
            },
        )
    except Exception as exc:  # pragma: no cover - covered with a mocked component
        LOGGER.exception(
            "Commercial AnalysisDashboard render failed "
            "[last_trigger=%s analysis_id=%s analysis_source=%s]",
            state.last_trigger,
            state.active_analysis_id,
            state.analysis_source,
            exc_info=exc,
        )
        st.error("분석 화면을 불러오지 못했습니다.")
        if st.button("다시 시도", key="commercial-analysis-retry"):
            st.rerun()
        if st.button("단지 검색으로 돌아가기", key="commercial-analysis-back"):
            handle_back_to_search_requested(session_state=st.session_state)
            st.rerun()
        return

    if _handle_component_events(
        component_result=component_result,
        analysis_repository=analysis_repository,
        analysis_service=analysis_service,
    ):
        st.rerun()


def handle_save_requested(
    *,
    session_state: dict[str, object],
    analysis_service,
    analysis_repository,
) -> CommercialPageState:
    current_state = load_commercial_page_state(session_state)

    if current_state.analysis_source == "saved" and current_state.active_analysis_id is not None:
        next_state = CommercialPageState(
            commercial_page="analysis_dashboard",
            analysis_source="saved",
            active_analysis_id=current_state.active_analysis_id,
            active_analysis_result=current_state.active_analysis_result,
            pending_analysis_request=None,
            page_notice={
                "level": "info",
                "code": "analysis_already_saved",
                "message": "이미 저장된 분석입니다.",
            },
            last_trigger="save_requested",
        )
        save_commercial_page_state(session_state, next_state)
        return next_state

    active_result = current_state.active_analysis_result
    if active_result is None:
        next_state = CommercialPageState(
            commercial_page="analysis_dashboard",
            analysis_source=current_state.analysis_source,
            active_analysis_id=current_state.active_analysis_id,
            active_analysis_result=None,
            pending_analysis_request=None,
            page_notice={
                "level": "error",
                "code": "analysis_result_missing",
                "message": "저장할 분석 결과가 없습니다.",
            },
            last_trigger="save_requested",
        )
        save_commercial_page_state(session_state, next_state)
        return next_state

    analysis_id = int(analysis_service.save_completed_analysis_result(active_result))
    saved_row = analysis_repository.get_by_id(analysis_id)
    if saved_row is None:
        next_state = CommercialPageState(
            commercial_page="analysis_dashboard",
            analysis_source="live",
            active_analysis_id=None,
            active_analysis_result=active_result,
            pending_analysis_request=None,
            page_notice={
                "level": "error",
                "code": "saved_analysis_unavailable",
                "message": "저장된 분석을 다시 불러오지 못했습니다.",
            },
            last_trigger="save_requested",
        )
        save_commercial_page_state(session_state, next_state)
        return next_state

    next_state = CommercialPageState(
        commercial_page="analysis_dashboard",
        analysis_source="saved",
        active_analysis_id=analysis_id,
        active_analysis_result=active_result,
        pending_analysis_request=None,
        page_notice={
            "level": "info",
            "code": "analysis_saved",
            "message": "분석을 저장했습니다.",
        },
        last_trigger="save_requested",
    )
    save_commercial_page_state(session_state, next_state)
    return next_state


def handle_comparison_requested(*, session_state: dict[str, object]) -> CommercialPageState:
    current_state = load_commercial_page_state(session_state)
    next_state = CommercialPageState(
        commercial_page="legacy_comparison",
        analysis_source=current_state.analysis_source,
        active_analysis_id=current_state.active_analysis_id,
        active_analysis_result=current_state.active_analysis_result,
        pending_analysis_request=None,
        page_notice=None,
        last_trigger="comparison_requested",
    )
    save_commercial_page_state(session_state, next_state)
    return next_state


def handle_back_to_search_requested(*, session_state: dict[str, object]) -> CommercialPageState:
    current_state = load_commercial_page_state(session_state)
    next_state = CommercialPageState(
        commercial_page="search_home",
        analysis_source=current_state.analysis_source,
        active_analysis_id=current_state.active_analysis_id,
        active_analysis_result=current_state.active_analysis_result,
        pending_analysis_request=None,
        page_notice=None,
        last_trigger="back_to_search_requested",
    )
    save_commercial_page_state(session_state, next_state)
    return next_state


def _build_view_model(*, state: CommercialPageState, analysis_repository) -> dict[str, object]:
    if state.analysis_source == "saved" and state.active_analysis_id is not None:
        saved_row = analysis_repository.get_by_id(state.active_analysis_id)
        if saved_row is None:
            return _build_error_view_model(
                state=state,
                code="saved_analysis_not_found",
                message="저장된 분석을 찾을 수 없습니다.",
            )
        view_model = build_analysis_dashboard_view_model_from_saved_row(saved_row)
    elif state.active_analysis_result is not None:
        view_model = build_analysis_dashboard_view_model_from_live_result(
            state.active_analysis_result
        )
    else:
        return _build_error_view_model(
            state=state,
            code="analysis_result_missing",
            message="표시할 분석 결과가 없습니다.",
        )

    view_model["analysis_source"] = state.analysis_source or "live"
    view_model["page_notice"] = state.page_notice
    return view_model


def _build_error_view_model(
    *,
    state: CommercialPageState,
    code: str,
    message: str,
) -> dict[str, object]:
    view_model = build_analysis_dashboard_view_model_from_live_result({})
    view_model["page_status"] = "error"
    view_model["display_error"] = {"code": code, "message": message}
    view_model["analysis_source"] = state.analysis_source or "live"
    view_model["page_notice"] = state.page_notice
    decision = dict(view_model["decision"])  # type: ignore[arg-type]
    decision["decision_status"] = "error"
    view_model["decision"] = decision
    return view_model


def _handle_component_events(
    *,
    component_result,
    analysis_repository,
    analysis_service,
) -> bool:
    if isinstance(_result_value(component_result, "save_requested"), dict):
        handle_save_requested(
            session_state=st.session_state,
            analysis_service=analysis_service,
            analysis_repository=analysis_repository,
        )
        return True

    if isinstance(_result_value(component_result, "comparison_requested"), dict):
        handle_comparison_requested(session_state=st.session_state)
        return True

    if isinstance(_result_value(component_result, "back_to_search_requested"), dict):
        handle_back_to_search_requested(session_state=st.session_state)
        return True

    if isinstance(_result_value(component_result, "retry_requested"), dict):
        return True

    return False


def _result_value(component_result, field_name: str):
    if component_result is None:
        return None
    return getattr(component_result, field_name, None)
