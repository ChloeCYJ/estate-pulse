from __future__ import annotations

import logging

import streamlit as st

from commercial_ui.component import render_commercial_ui
from modules.services.finance_profile_service import (
    FinanceProfileValidationError,
    build_finance_profile_payload,
)
from modules.ui.commercial_auth import (
    CommercialAuthContext,
    login_commercial_user,
    logout_commercial_user,
)
from modules.ui.commercial_page_state import (
    CommercialPageState,
    load_commercial_page_state,
    save_commercial_page_state,
)
from modules.ui.viewmodels.finance_profile import build_finance_profile_view_model


LOGGER = logging.getLogger(__name__)
FINANCE_FIELD_ERRORS_KEY = "commercial_finance_profile_field_errors"


def render_commercial_finance_profile_page(
    *,
    auth_context: CommercialAuthContext,
    auth_view_model: dict[str, object],
    finance_profile_service,
) -> None:
    profile = None
    if auth_context.user is not None:
        profile = finance_profile_service.get_current(auth_context.user.id)
    state = load_commercial_page_state(st.session_state)
    view_model = build_finance_profile_view_model(
        profile=profile,
        status="ready" if auth_context.user is not None else "auth_required",
        field_errors=dict(st.session_state.get(FINANCE_FIELD_ERRORS_KEY) or {}),
        notice=state.page_notice,
    )
    component_result = render_commercial_ui(
        page="finance-profile",
        view_model=view_model,
        auth_view_model=auth_view_model,
        key="commercial-finance-profile",
    )

    if isinstance(_result_value(component_result, "login_requested"), dict):
        login_commercial_user()
        return
    if isinstance(_result_value(component_result, "logout_requested"), dict):
        logout_commercial_user()
        return
    if isinstance(_result_value(component_result, "finance_profile_back_requested"), dict):
        _return_to_search(st.session_state)
        st.rerun()
        return
    form_payload = _result_value(component_result, "finance_profile_saved")
    if isinstance(form_payload, dict):
        handle_finance_profile_saved(
            session_state=st.session_state,
            auth_context=auth_context,
            finance_profile_service=finance_profile_service,
            form_payload=form_payload,
        )
        st.rerun()


def handle_finance_profile_saved(
    *,
    session_state: dict[str, object],
    auth_context: CommercialAuthContext,
    finance_profile_service,
    form_payload: dict[str, object],
) -> CommercialPageState:
    current = load_commercial_page_state(session_state)
    if auth_context.user is None:
        return _save_state(
            session_state,
            current,
            page="finance_profile",
            notice={
                "level": "warning",
                "code": "auth_required",
                "message": "개인 자산을 저장하려면 로그인해 주세요.",
            },
        )

    existing = finance_profile_service.get_current(auth_context.user.id)
    try:
        payload = build_finance_profile_payload(
            cash_amount_eok=form_payload.get("cash_amount_eok", 0),
            annual_income_eok=form_payload.get("annual_income_eok", 0),
            interest_rate_percent=form_payload.get("interest_rate_percent", 0),
            credit_loan_balance_eok=form_payload.get("credit_loan_balance_eok", 0),
            other_loan_balance_eok=form_payload.get("other_loan_balance_eok", 0),
            home_count=form_payload.get("home_count", 0),
            owned_real_estate_value_eok=form_payload.get(
                "owned_real_estate_value_eok", 0
            ),
            owned_real_estate_debt_eok=form_payload.get(
                "owned_real_estate_debt_eok", 0
            ),
            use_manual_ltv=bool(form_payload.get("use_manual_ltv", False)),
            manual_ltv_rate=form_payload.get("manual_ltv_rate"),
            existing_profile=existing,
        )
    except FinanceProfileValidationError as exc:
        session_state[FINANCE_FIELD_ERRORS_KEY] = exc.field_errors
        return _save_state(
            session_state,
            current,
            page="finance_profile",
            notice={
                "level": "error",
                "code": "finance_profile_validation",
                "message": "입력값을 확인해 주세요.",
            },
        )

    try:
        finance_profile_service.save_current(
            user_id=auth_context.user.id,
            payload=payload,
        )
    except Exception as exc:  # pragma: no cover - storage adapter boundary
        LOGGER.exception("Commercial finance profile save failed", exc_info=exc)
        return _save_state(
            session_state,
            current,
            page="finance_profile",
            notice={
                "level": "error",
                "code": "finance_profile_save_failed",
                "message": "개인 자산을 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.",
            },
        )

    session_state.pop(FINANCE_FIELD_ERRORS_KEY, None)
    return _save_state(
        session_state,
        current,
        page="search_home",
        notice={
            "level": "info",
            "code": "finance_profile_saved",
            "message": "개인 자산을 저장했습니다.",
        },
    )


def _return_to_search(session_state: dict[str, object]) -> CommercialPageState:
    return _save_state(
        session_state,
        load_commercial_page_state(session_state),
        page="search_home",
        notice=None,
    )


def _save_state(
    session_state: dict[str, object],
    current: CommercialPageState,
    *,
    page: str,
    notice: dict[str, str] | None,
) -> CommercialPageState:
    next_state = CommercialPageState(
        commercial_page=page,  # type: ignore[arg-type]
        analysis_source=current.analysis_source,
        active_analysis_id=current.active_analysis_id,
        active_analysis_result=current.active_analysis_result,
        pending_analysis_request=current.pending_analysis_request,
        page_notice=notice,  # type: ignore[arg-type]
        last_trigger="finance_profile_saved",
        resume_action=current.resume_action,
    )
    save_commercial_page_state(session_state, next_state)
    return next_state


def _result_value(component_result, field_name: str):
    if component_result is None:
        return None
    return getattr(component_result, field_name, None)
