from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from modules.analyzers.owner_occupied_analyzer import calculate_monthly_repayment
from config.settings import AppSettings
from modules.services.analysis_service import (
    CASH_ONLY,
    SELL_OWNED_REAL_ESTATE,
    AnalysisService,
    BenchmarkInputs,
)
from modules.utils.money_utils import format_compact_won, format_won, from_eok, to_eok

PRIMARY_MODE_LABELS = {
    "OWNER_OCCUPIED": "실거주",
    "INVESTMENT": "투자",
}
FUNDING_MODE_LABELS = {
    CASH_ONLY: "보유 현금만 사용",
    SELL_OWNED_REAL_ESTATE: "보유 부동산 처분 후 매수",
}
LAST_ANALYSIS_RESULT_KEY = "analysis_last_result"
LAST_ANALYSIS_LISTING_ID_KEY = "analysis_last_listing_id"
LAST_ANALYSIS_PROFILE_ID_KEY = "analysis_last_profile_id"
LAST_ANALYSIS_BENCHMARKS_KEY = "analysis_last_benchmarks"
LAST_SCENARIO_RESULT_KEY = "analysis_last_scenario_result"
LAST_SCENARIO_LISTING_ID_KEY = "analysis_last_scenario_listing_id"
LAST_SCENARIO_PROFILE_ID_KEY = "analysis_last_scenario_profile_id"


def render_analysis_page(
    *,
    complex_repository,
    listing_repository,
    finance_repository,
    analysis_repository,
    analysis_service: AnalysisService,
    settings: AppSettings,
) -> None:
    st.title("Analysis")
    st.caption("단일 매물을 선택해 자금, 거래비용, 유동성, 단지 등급까지 함께 분석합니다.")

    listings = listing_repository.list_all()
    profiles = finance_repository.list_all()

    if not listings:
        st.info("먼저 매물을 등록해 주세요.")
        return
    if not profiles:
        st.info("먼저 자금 프로필을 등록해 주세요.")
        return

    listing_options = {
        f"#{item['id']} | {item['complex_name']} | {format_compact_won(item['sale_price'])}": item
        for item in listings
    }
    profile_options = {
        f"#{item['id']} | 보유 현금 {format_compact_won(item['cash_amount'])}": item
        for item in profiles
    }

    selected_listing = listing_options[st.selectbox("매물 선택", list(listing_options.keys()))]
    selected_profile = profile_options[st.selectbox("자금 프로필", list(profile_options.keys()))]

    default_mode = _to_primary_mode(selected_listing.get("effective_investment_type"))
    selected_mode = st.radio(
        "분석 관점",
        list(PRIMARY_MODE_LABELS.keys()),
        index=list(PRIMARY_MODE_LABELS.keys()).index(default_mode),
        format_func=lambda value: PRIMARY_MODE_LABELS[value],
        horizontal=True,
    )

    try:
        transaction_context = analysis_service.get_transaction_context(listing_id=selected_listing["id"])
        _render_transaction_summary(transaction_context)
        _render_transaction_history(transaction_context)
    except ValueError as exc:
        st.warning(str(exc))

    with st.form("analysis_form"):
        st.subheader("자금 사용 시나리오")
        funding_mode = st.radio(
            "매수 자금 기준",
            list(FUNDING_MODE_LABELS.keys()),
            index=0,
            format_func=lambda value: FUNDING_MODE_LABELS[value],
            help=(
                "보유 부동산을 팔아 갈아타는 경우에는 처분 후 매수를 선택하세요. "
                "이 경우 보유 현금 + 보유 부동산 시가 - 보유 부동산 대출 잔액을 기준으로 봅니다."
            ),
            horizontal=True,
        )
        _render_profile_purchase_power_preview(selected_profile, funding_mode)

        with st.expander("고급 설정: 시장 입력값 수동 보정", expanded=False):
            st.caption(
                "기본값은 시스템이 자동 계산합니다. 실제 매매 조건이 다른 경우에만 수동 보정을 입력하세요."
            )
            market_col1, market_col2 = st.columns(2)
            with market_col1:
                recent_avg_price_override_eok = st.number_input(
                    "최근 평균가 수동 보정 (억 원)",
                    min_value=0.0,
                    step=0.1,
                    value=0.0,
                    format="%.2f",
                )
                one_year_high_price_override_eok = st.number_input(
                    "최근 1년 최고가 수동 보정 (억 원)",
                    min_value=0.0,
                    step=0.1,
                    value=0.0,
                    format="%.2f",
                )
                repair_cost_eok = st.number_input(
                    "수리비 (억 원)",
                    min_value=0.0,
                    step=0.1,
                    value=0.0,
                    format="%.2f",
                )
            with market_col2:
                expected_loan_amount_eok = st.number_input(
                    "예상 대출 수동 보정 (억 원)",
                    min_value=0.0,
                    step=0.1,
                    value=0.0,
                    format="%.2f",
                )
                ltv_rate_override = st.number_input(
                    "LTV 수동 보정",
                    min_value=0.0,
                    max_value=1.0,
                    step=0.05,
                    value=0.0,
                    format="%.2f",
                    help="비워두면 자금 프로필의 수동 LTV 설정 또는 대출 규칙 엔진의 자동 계산값을 사용합니다.",
                )
                expected_jeonse_price_override_eok = 0.0
                if selected_mode == "INVESTMENT":
                    expected_jeonse_price_override_eok = st.number_input(
                        "예상 전세가 수동 보정 (억 원)",
                        min_value=0.0,
                        step=0.1,
                        value=0.0,
                        format="%.2f",
                    )

        with st.expander("고급 설정: 거래비용 수동 보정", expanded=False):
            st.caption(
                "기본값은 시스템이 자동 계산합니다. 실제 계약 비용이 다른 경우에만 수동 보정을 입력하세요."
            )
            cost_col1, cost_col2, cost_col3 = st.columns(3)
            with cost_col1:
                acquisition_tax_override_eok = st.number_input(
                    "취득세 수동 보정 (억 원)",
                    min_value=0.0,
                    step=0.01,
                    value=0.0,
                    format="%.2f",
                )
                local_education_tax_override_eok = st.number_input(
                    "지방교육세 수동 보정 (억 원)",
                    min_value=0.0,
                    step=0.01,
                    value=0.0,
                    format="%.2f",
                )
            with cost_col2:
                brokerage_fee_override_eok = st.number_input(
                    "중개보수 수동 보정 (억 원)",
                    min_value=0.0,
                    step=0.01,
                    value=0.0,
                    format="%.2f",
                )
                legal_fee_override_eok = st.number_input(
                    "법무비 수동 보정 (억 원)",
                    min_value=0.0,
                    step=0.01,
                    value=0.0,
                    format="%.2f",
                )
            with cost_col3:
                reserve_cost_override_eok = st.number_input(
                    "예비비 수동 보정 (억 원)",
                    min_value=0.0,
                    step=0.01,
                    value=0.0,
                    format="%.2f",
                )

        save_result = st.checkbox("분석 결과 저장", value=True)

        submitted = st.form_submit_button("분석 실행")

    if submitted:
        try:
            current_benchmarks = BenchmarkInputs(
                repair_cost=int(from_eok(repair_cost_eok)),
                expected_loan_amount=_to_optional_won(expected_loan_amount_eok),
                ltv_rate_override=_to_optional_float(ltv_rate_override),
                funding_mode=funding_mode,
                recent_avg_price_override=_to_optional_won(recent_avg_price_override_eok),
                one_year_high_price_override=_to_optional_won(one_year_high_price_override_eok),
                expected_jeonse_price_override=_to_optional_won(expected_jeonse_price_override_eok),
                analysis_mode=selected_mode,
                acquisition_tax_override=_to_optional_won(acquisition_tax_override_eok),
                local_education_tax_override=_to_optional_won(local_education_tax_override_eok),
                brokerage_fee_override=_to_optional_won(brokerage_fee_override_eok),
                legal_fee_override=_to_optional_won(legal_fee_override_eok),
                reserve_cost_override=_to_optional_won(reserve_cost_override_eok),
            )
            result = analysis_service.run_analysis(
                listing_id=selected_listing["id"],
                finance_profile_id=selected_profile["id"],
                benchmarks=current_benchmarks,
                save_result=save_result,
            )
            st.session_state[LAST_ANALYSIS_RESULT_KEY] = result
            st.session_state[LAST_ANALYSIS_LISTING_ID_KEY] = selected_listing["id"]
            st.session_state[LAST_ANALYSIS_PROFILE_ID_KEY] = selected_profile["id"]
            st.session_state[LAST_ANALYSIS_BENCHMARKS_KEY] = current_benchmarks
            st.session_state.pop(LAST_SCENARIO_RESULT_KEY, None)
            st.session_state.pop(LAST_SCENARIO_LISTING_ID_KEY, None)
            st.session_state.pop(LAST_SCENARIO_PROFILE_ID_KEY, None)
        except ValueError as exc:
            st.error(str(exc))

    current_result = _current_analysis_result(
        selected_listing_id=selected_listing["id"],
        selected_profile_id=selected_profile["id"],
    )
    current_benchmarks = st.session_state.get(LAST_ANALYSIS_BENCHMARKS_KEY)
    if current_result and current_benchmarks is not None:
        _render_analysis_metrics(current_result)
        _render_scenario_analyzer(
            analysis_service=analysis_service,
            listing_id=selected_listing["id"],
            finance_profile_id=selected_profile["id"],
            baseline_result=current_result,
            baseline_benchmarks=current_benchmarks,
        )

    _render_recent_analysis_history(analysis_repository.list_recent())


def _render_analysis_metrics(result: dict) -> None:
    st.subheader(f"{result['complex_name']} 분석 결과")
    st.info(result["scenario_explanation"])
    interest_rate_warning = _high_interest_rate_warning(result)
    if interest_rate_warning:
        st.warning(interest_rate_warning)

    _render_decision_highlight(result)

    st.write("핵심 자금 판단")
    _render_core_cash_metrics(result)
    st.write("투자 판단 근거")
    _render_explainability_summary(result)

    if result["primary_user_mode"] == "INVESTMENT":
        extra_cols = st.columns(3)
        st.write("추가 참고 지표")
        extra_cols[0].metric("갭 금액", format_compact_won(result["gap_amount"]))
        extra_cols[1].metric(
            "자금 효율 점수",
            f"{result['required_cash_efficiency_score']:.1f}",
        )
        extra_cols[2].metric(
            "투자 효율",
            _format_efficiency(result["estimated_investment_efficiency"]),
        )
    else:
        st.write("추가 참고 지표")
        cash_balance_after_purchase = _cash_judgment(result)["cash_balance_after_purchase"]
        extra_cols = st.columns(3 if cash_balance_after_purchase >= 0 else 2)
        extra_cols[0].metric("월 상환액", _format_optional_money(result["monthly_repayment"]))
        applied_rules = result.get("applied_rules") or {}
        repayment_reason = _missing_metric_reason(
            "monthly_repayment",
            result["monthly_repayment"],
            explicit_reason=(applied_rules.get("monthly_repayment") or {}).get("missing_reason"),
        )
        if repayment_reason:
            extra_cols[0].caption(repayment_reason)
        extra_cols[1].metric("DSR", _format_optional_percent(result["dsr"]))
        dsr_reason = _missing_metric_reason(
            "dsr",
            result["dsr"],
            explicit_reason=(applied_rules.get("dsr") or {}).get("missing_reason"),
        )
        if dsr_reason:
            extra_cols[1].caption(dsr_reason)
        if cash_balance_after_purchase >= 0:
            extra_cols[2].metric(
                "매수 후 현금 잔액",
                format_compact_won(cash_balance_after_purchase),
            )

    st.caption(f"판정: {result['decision']}")

    with st.expander("상세: 자금 사용 기준", expanded=False):
        _render_purchase_power_table(result)
    with st.expander("상세: 계산 기준", expanded=False):
        _render_source_table(result)
    with st.expander("적용 계산 룰 보기", expanded=False):
        _render_applied_rules_panel(result)
    with st.expander("상세: 지역 규제 및 정책 참고", expanded=False):
        _render_active_region_policy_table(result)
        _render_policy_event_table(result)
    with st.expander("상세: 거래비용", expanded=False):
        _render_cost_table(result)
    with st.expander("상세: 단지 품질 분석", expanded=False):
        _render_complex_profile_table(result)
    with st.expander("상세: 계산식", expanded=False):
        _render_formula_explainer(result)
    with st.expander("상세: 요약 원문", expanded=False):
        st.text_area("요약", value=result["summary"], height=180, disabled=True)

    if result["reasons"]:
        st.write("점수 반영 사유")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

    if result["risks"]:
        st.write("리스크 체크")
        for risk in result["risks"]:
            st.write(f"- {risk}")


def _current_analysis_result(*, selected_listing_id: int, selected_profile_id: int) -> dict | None:
    if st.session_state.get(LAST_ANALYSIS_LISTING_ID_KEY) != selected_listing_id:
        return None
    if st.session_state.get(LAST_ANALYSIS_PROFILE_ID_KEY) != selected_profile_id:
        return None
    return st.session_state.get(LAST_ANALYSIS_RESULT_KEY)


def _render_scenario_analyzer(
    *,
    analysis_service: AnalysisService,
    listing_id: int,
    finance_profile_id: int,
    baseline_result: dict,
    baseline_benchmarks: BenchmarkInputs,
) -> None:
    st.subheader("시나리오 분석")
    st.caption(
        "현재 분석 결과를 기준으로 가격, 전세가, 금리, LTV 변화 시 자금 부담과 투자점수 변화를 비교합니다."
    )

    with st.form("scenario_analyzer_form"):
        cols = st.columns(4)
        sale_price_change_pct = cols[0].slider("매매가 변화율 (%)", min_value=-10, max_value=10, value=0)
        jeonse_price_change_pct = cols[1].slider("전세가 변화율 (%)", min_value=-10, max_value=10, value=0)
        interest_rate_change_pct = cols[2].slider(
            "금리 변화율 (%p)",
            min_value=-2.0,
            max_value=2.0,
            value=0.0,
            step=0.1,
        )
        ltv_change_pct = cols[3].slider("LTV 변화율 (%p)", min_value=-20, max_value=20, value=0)
        scenario_submitted = st.form_submit_button("시나리오 계산")

    if scenario_submitted:
        scenario_benchmarks = _build_scenario_benchmarks(
            baseline_benchmarks=baseline_benchmarks,
            baseline_result=baseline_result,
            sale_price_change_pct=sale_price_change_pct,
            jeonse_price_change_pct=jeonse_price_change_pct,
            interest_rate_change_pct=interest_rate_change_pct,
            ltv_change_pct=ltv_change_pct,
        )
        try:
            scenario_result = analysis_service.run_analysis(
                listing_id=listing_id,
                finance_profile_id=finance_profile_id,
                benchmarks=scenario_benchmarks,
                save_result=False,
            )
            st.session_state[LAST_SCENARIO_RESULT_KEY] = scenario_result
            st.session_state[LAST_SCENARIO_LISTING_ID_KEY] = listing_id
            st.session_state[LAST_SCENARIO_PROFILE_ID_KEY] = finance_profile_id
        except ValueError as exc:
            st.error(str(exc))
            st.session_state.pop(LAST_SCENARIO_RESULT_KEY, None)

    scenario_result = _current_scenario_result(
        listing_id=listing_id,
        finance_profile_id=finance_profile_id,
    )
    if not scenario_result:
        return

    _render_scenario_summary_cards(
        baseline_result=baseline_result,
        scenario_result=scenario_result,
    )
    comparison_rows = _scenario_comparison_rows(
        baseline_result=baseline_result,
        scenario_result=scenario_result,
    )
    st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True, hide_index=True)
    _render_interest_rate_scenario_note(
        baseline_result=baseline_result,
        scenario_result=scenario_result,
        interest_rate_change_pct=interest_rate_change_pct,
    )

    interpretation_lines = _scenario_interpretation_lines(
        baseline_result=baseline_result,
        scenario_result=scenario_result,
        sale_price_change_pct=sale_price_change_pct,
        jeonse_price_change_pct=jeonse_price_change_pct,
        interest_rate_change_pct=interest_rate_change_pct,
        ltv_change_pct=ltv_change_pct,
    )
    if interpretation_lines:
        st.write("해석")
        for line in interpretation_lines:
            st.write(f"- {line}")
    limited_impact_lines = _scenario_limited_impact_lines(
        baseline_result=baseline_result,
        scenario_result=scenario_result,
        jeonse_price_change_pct=jeonse_price_change_pct,
        ltv_change_pct=ltv_change_pct,
    )
    if limited_impact_lines:
        st.write("영향이 제한된 이유")
        for line in limited_impact_lines:
            st.write(f"- {line}")
    score_line = _scenario_score_line(
        baseline_result=baseline_result,
        scenario_result=scenario_result,
        has_input_changes=_scenario_has_input_changes(
            sale_price_change_pct=sale_price_change_pct,
            jeonse_price_change_pct=jeonse_price_change_pct,
            interest_rate_change_pct=interest_rate_change_pct,
            ltv_change_pct=ltv_change_pct,
        ),
    )
    if score_line:
        st.write("투자점수 변화")
        st.write(f"- {score_line}")


def _current_scenario_result(*, listing_id: int, finance_profile_id: int) -> dict | None:
    if st.session_state.get(LAST_SCENARIO_LISTING_ID_KEY) != listing_id:
        return None
    if st.session_state.get(LAST_SCENARIO_PROFILE_ID_KEY) != finance_profile_id:
        return None
    return st.session_state.get(LAST_SCENARIO_RESULT_KEY)


def _build_scenario_benchmarks(
    *,
    baseline_benchmarks: BenchmarkInputs,
    baseline_result: dict,
    sale_price_change_pct: int,
    jeonse_price_change_pct: int,
    interest_rate_change_pct: float,
    ltv_change_pct: int,
) -> BenchmarkInputs:
    base_sale_price = int(baseline_result["sale_price"])
    base_jeonse_price = int(baseline_result.get("expected_jeonse_price") or 0)
    base_interest_rate = (baseline_result.get("applied_rules") or {}).get("monthly_repayment", {}).get(
        "annual_interest_rate"
    )
    base_ltv_rate = (baseline_result.get("applied_rules") or {}).get("loan_ltv", {}).get(
        "applied_ltv_rate"
    )

    scenario_sale_price = int(round(base_sale_price * (1 + sale_price_change_pct / 100)))
    scenario_jeonse_price = int(round(base_jeonse_price * (1 + jeonse_price_change_pct / 100)))
    scenario_interest_rate = (
        None
        if base_interest_rate is None
        else max(0.0, float(base_interest_rate) + float(interest_rate_change_pct) / 100)
    )
    scenario_ltv_rate = (
        None
        if base_ltv_rate is None
        else min(1.0, max(0.0, float(base_ltv_rate) + float(ltv_change_pct) / 100))
    )

    return BenchmarkInputs(
        repair_cost=baseline_benchmarks.repair_cost,
        sale_price_override=scenario_sale_price,
        expected_loan_amount=baseline_benchmarks.expected_loan_amount,
        ltv_rate_override=scenario_ltv_rate,
        interest_rate_override=scenario_interest_rate,
        recent_avg_price_override=baseline_benchmarks.recent_avg_price_override,
        one_year_high_price_override=baseline_benchmarks.one_year_high_price_override,
        expected_jeonse_price_override=scenario_jeonse_price,
        analysis_mode=baseline_benchmarks.analysis_mode,
        reference_date=baseline_benchmarks.reference_date,
        region_type=baseline_benchmarks.region_type,
        buyer_type=baseline_benchmarks.buyer_type,
        purpose=baseline_benchmarks.purpose,
        tax_rule_version=baseline_benchmarks.tax_rule_version,
        brokerage_rule_version=baseline_benchmarks.brokerage_rule_version,
        acquisition_tax_override=baseline_benchmarks.acquisition_tax_override,
        local_education_tax_override=baseline_benchmarks.local_education_tax_override,
        brokerage_fee_override=baseline_benchmarks.brokerage_fee_override,
        legal_fee_override=baseline_benchmarks.legal_fee_override,
        reserve_cost_override=baseline_benchmarks.reserve_cost_override,
        funding_mode=baseline_benchmarks.funding_mode,
    )


def _scenario_comparison_rows(*, baseline_result: dict, scenario_result: dict) -> list[dict[str, str]]:
    rows = [
        ("예상 대출", baseline_result.get("expected_loan_amount"), scenario_result.get("expected_loan_amount"), "money"),
        ("총 필요 현금", baseline_result.get("required_cash"), scenario_result.get("required_cash"), "money"),
        ("추가 필요 현금", baseline_result.get("shortage_cash"), scenario_result.get("shortage_cash"), "money"),
        (
            "은행 승인액 기준 월 부담",
            baseline_result.get("monthly_repayment"),
            scenario_result.get("monthly_repayment"),
            "money",
        ),
        ("투자점수", baseline_result.get("investment_score"), scenario_result.get("investment_score"), "score"),
    ]
    rows[2] = (*rows[2][:3], "shortage_money")
    return [
        {
            "항목": label,
            "현재": _scenario_value_label(current, kind),
            "변경 후": _scenario_value_label(changed, kind),
            "차이": _scenario_delta_label(current, changed, kind),
        }
        for label, current, changed, kind in rows
    ]

def _scenario_value_label(value: int | float | None, kind: str) -> str:
    if value is None:
        return "-"
    if kind == "shortage_money":
        return _format_scenario_money(max(int(value), 0))
    if kind in {"money", "shortage_money"}:
        return _format_scenario_money(value)
    if kind == "score":
        return f"{int(value)}점"
    return str(value)


def _format_scenario_money(value: int | float | None) -> str:
    if value is None:
        return "-"
    amount = int(value)
    if abs(amount) >= 100_000_000:
        return f"{amount / 100_000_000:.2f}억"
    return format_compact_won(amount)


def _scenario_delta_label(current: int | float | None, changed: int | float | None, kind: str) -> str:
    if current is None or changed is None:
        return "-"
    delta = changed - current
    if kind in {"money", "shortage_money"}:
        if delta == 0:
            return "0원"
        sign = "+" if delta > 0 else ""
        return f"{sign}{format_compact_won(int(delta))}"
    if kind == "score":
        if delta == 0:
            return "0점"
        sign = "+" if delta > 0 else ""
        return f"{sign}{int(delta)}점"
    return "-"


def _render_scenario_summary_cards(*, baseline_result: dict, scenario_result: dict) -> None:
    same_loan_pair = _same_loan_monthly_repayment_pair(
        baseline_result=baseline_result,
        scenario_result=scenario_result,
    )
    same_loan_current = same_loan_pair[0] if same_loan_pair is not None else None
    same_loan_changed = same_loan_pair[1] if same_loan_pair is not None else None

    rows = [
        (
            "추가 준비 현금",
            baseline_result.get("shortage_cash"),
            scenario_result.get("shortage_cash"),
            "money",
            "금리/가격 변화로 인해 실제로 더 준비해야 하는 현금",
        ),
        (
            "기존 대출금 유지 시 월 부담",
            same_loan_current,
            same_loan_changed,
            "money",
            "현재 대출액을 유지한다고 가정한 경우의 월 상환 부담",
        ),
        (
            "은행 승인액 기준 월 부담",
            baseline_result.get("monthly_repayment"),
            scenario_result.get("monthly_repayment"),
            "money",
            "시나리오 적용 후 실제 승인 가능한 대출액 기준 월 상환액",
        ),
        (
            "투자점수",
            baseline_result.get("investment_score"),
            scenario_result.get("investment_score"),
            "score",
            None,
        ),
        (
            "은행 대출 가능액",
            baseline_result.get("expected_loan_amount"),
            scenario_result.get("expected_loan_amount"),
            "money",
            "DSR 기준으로 은행이 승인 가능한 예상 대출액",
        ),
    ]
    rows[0] = (*rows[0][:3], "shortage_money", rows[0][4])
    cols = st.columns(len(rows))
    for col, (label, current, changed, kind, help_text) in zip(cols, rows):
        col.metric(
            label,
            f"{_scenario_value_label(current, kind)} → {_scenario_value_label(changed, kind)}",
            _scenario_delta_summary_label(current, changed, kind),
        )
        if help_text:
            col.caption(help_text)


def _scenario_delta_summary_label(current: int | float | None, changed: int | float | None, kind: str) -> str:
    if current is None or changed is None:
        return "변화 없음"
    if changed == current:
        return "변화 없음"
    return _scenario_delta_label(current, changed, kind)


def _render_interest_rate_scenario_note(
    *,
    baseline_result: dict,
    scenario_result: dict,
    interest_rate_change_pct: float,
) -> None:
    if interest_rate_change_pct == 0:
        return

    if interest_rate_change_pct > 0:
        st.info(
            "금리 상승 시에는 은행 대출 가능액, 동일 대출 유지 시 월상환액, "
            "승인 대출 기준 월상환액을 구분해서 확인해 주세요."
        )
    else:
        st.info(
            "금리 변화 시에는 은행 대출 가능액과 월상환액이 함께 재계산됩니다. "
            "동일 대출 유지 기준과 승인 대출 기준 결과를 함께 확인해 주세요."
        )


def _same_loan_monthly_repayment_pair(
    *,
    baseline_result: dict,
    scenario_result: dict,
) -> tuple[int | None, int | None] | None:
    loan_amount = baseline_result.get("expected_loan_amount")
    if loan_amount is None:
        return None

    baseline_rate = (
        (baseline_result.get("applied_rules") or {})
        .get("monthly_repayment", {})
        .get("annual_interest_rate")
    )
    scenario_rate = (
        (scenario_result.get("applied_rules") or {})
        .get("monthly_repayment", {})
        .get("annual_interest_rate")
    )
    if baseline_rate is None or scenario_rate is None:
        return None

    current = calculate_monthly_repayment(
        loan_amount=int(loan_amount),
        annual_interest_rate=float(baseline_rate),
        loan_term_years=30,
    )
    changed = calculate_monthly_repayment(
        loan_amount=int(loan_amount),
        annual_interest_rate=float(scenario_rate),
        loan_term_years=30,
    )
    return current, changed


def _scenario_interpretation_lines(
    *,
    baseline_result: dict,
    scenario_result: dict,
    sale_price_change_pct: int,
    jeonse_price_change_pct: int,
    interest_rate_change_pct: float,
    ltv_change_pct: int,
) -> list[str]:
    lines: list[str] = []

    shortage_delta = _numeric_delta(scenario_result.get("shortage_cash"), baseline_result.get("shortage_cash"))
    loan_delta = _numeric_delta(
        scenario_result.get("expected_loan_amount"),
        baseline_result.get("expected_loan_amount"),
    )
    score_delta = _numeric_delta(
        scenario_result.get("investment_score"),
        baseline_result.get("investment_score"),
    )
    repayment_delta = _numeric_delta(
        scenario_result.get("monthly_repayment"),
        baseline_result.get("monthly_repayment"),
    )
    same_loan_pair = _same_loan_monthly_repayment_pair(
        baseline_result=baseline_result,
        scenario_result=scenario_result,
    )
    same_loan_delta = None
    if same_loan_pair is not None:
        same_loan_delta = _numeric_delta(same_loan_pair[1], same_loan_pair[0])
    if shortage_delta is not None:
        if _is_effectively_zero_money_delta(shortage_delta):
            lines.append("추가 준비 현금은 그대로입니다.")
        else:
            lines.append(f"추가 준비 현금이 약 {_delta_money_phrase(shortage_delta)}했습니다.")

    if same_loan_delta is not None:
        if _is_effectively_zero_money_delta(same_loan_delta):
            lines.append("기존 대출금 유지 시 월 부담은 그대로입니다.")
        else:
            lines.append(f"기존 대출금 유지 시 월 부담은 약 {_delta_money_phrase(same_loan_delta)}했습니다.")

    if repayment_delta is not None:
        if _is_effectively_zero_money_delta(repayment_delta):
            lines.append("은행 승인액 기준 월 부담은 그대로입니다.")
        else:
            lines.append(f"은행 승인액 기준 월 부담은 약 {_delta_money_phrase(repayment_delta)}했습니다.")

    if loan_delta is not None:
        if _is_effectively_zero_money_delta(loan_delta):
            lines.append("은행 대출 가능액은 그대로입니다.")
        else:
            lines.append(f"은행 대출 가능액은 약 {_delta_money_phrase(loan_delta)}했습니다.")

    if not lines and not _scenario_has_input_changes(
        sale_price_change_pct=sale_price_change_pct,
        jeonse_price_change_pct=jeonse_price_change_pct,
        interest_rate_change_pct=interest_rate_change_pct,
        ltv_change_pct=ltv_change_pct,
    ):
        lines.append("현재 결과와 동일합니다.")
    return lines


def _scenario_limited_impact_lines(
    *,
    baseline_result: dict,
    scenario_result: dict,
    jeonse_price_change_pct: int,
    ltv_change_pct: int,
) -> list[str]:
    lines: list[str] = []
    loan_delta = _numeric_delta(
        scenario_result.get("expected_loan_amount"),
        baseline_result.get("expected_loan_amount"),
    )
    shortage_delta = _numeric_delta(
        scenario_result.get("shortage_cash"),
        baseline_result.get("shortage_cash"),
    )

    if ltv_change_pct != 0 and loan_delta is not None and _is_effectively_zero_money_delta(loan_delta):
        limiting_factor = _scenario_limiting_factor_text(scenario_result)
        if limiting_factor:
            lines.append(
                f"LTV를 변경했지만 현재 대출은 {limiting_factor}에 의해 제한되어 대출 가능액이 변하지 않았습니다."
            )
        else:
            lines.append("LTV를 변경했지만 현재 대출은 다른 상한 규칙에 의해 제한되어 대출 가능액이 변하지 않았습니다.")

    if jeonse_price_change_pct != 0 and shortage_delta is not None and _is_effectively_zero_money_delta(shortage_delta):
        if scenario_result.get("primary_user_mode") == "OWNER_OCCUPIED":
            lines.append(
                "전세가를 변경했지만 실거주 기준 분석에서는 전세보증금을 매수 자금에서 차감하지 않아 추가 준비 현금에 영향이 없습니다."
            )
        else:
            lines.append("전세가를 변경했지만 이번 변화는 추가 준비 현금 계산에 직접 반영되지 않아 영향이 제한적입니다.")

    return lines[:2]


def _scenario_score_line(
    *,
    baseline_result: dict,
    scenario_result: dict,
    has_input_changes: bool,
) -> str | None:
    score_delta = _numeric_delta(
        scenario_result.get("investment_score"),
        baseline_result.get("investment_score"),
    )
    if score_delta is None:
        return None
    if score_delta == 0:
        if has_input_changes:
            return "투자점수는 주요 점수 구간이 바뀌지 않아 동일하게 유지되었습니다."
        return f"투자점수는 {int(scenario_result.get('investment_score') or 0)}점으로 변화가 없습니다."
    if score_delta > 0:
        return f"투자점수가 {int(score_delta)}점 개선되었습니다."
    return f"투자점수가 {abs(int(score_delta))}점 하락했습니다."


def _scenario_has_input_changes(
    *,
    sale_price_change_pct: int,
    jeonse_price_change_pct: int,
    interest_rate_change_pct: float,
    ltv_change_pct: int,
) -> bool:
    return any(
        (
            sale_price_change_pct != 0,
            jeonse_price_change_pct != 0,
            interest_rate_change_pct != 0,
            ltv_change_pct != 0,
        )
    )


def _scenario_limiting_factor_text(result: dict) -> str | None:
    factor = (
        (((result.get("applied_rules") or {}).get("loan_ltv") or {}).get("final_limiting_factor"))
        or ""
    )
    factor_text = str(factor).strip()
    if not factor_text or factor_text == "-":
        return None
    return factor_text


def _is_effectively_zero_money_delta(value: int | float | None) -> bool:
    if value is None:
        return False
    return abs(float(value)) < 10_000


def _compare_numeric(changed: int | float | None, current: int | float | None) -> int:
    if changed is None or current is None:
        return 0
    if changed > current:
        return 1
    if changed < current:
        return -1
    return 0


def _numeric_delta(changed: int | float | None, current: int | float | None) -> int | float | None:
    if changed is None or current is None:
        return None
    return changed - current


def _delta_money_phrase(delta: int | float) -> str:
    direction = "증가" if delta > 0 else "감소"
    return f"{format_compact_won(abs(int(delta)))} {direction}"


def _signed_percent_label(value: int | float) -> str:
    return f"{value:+.1f}%"


def _signed_point_label(value: int | float) -> str:
    return f"{value:+.1f}%p"


def _render_decision_highlight(result: dict) -> None:
    judgment = _cash_judgment(result)
    if not judgment["can_purchase"]:
        st.error(
            f"매수 불가: 추가 필요 현금 {format_compact_won(judgment['additional_cash_required'])}. "
            f"현재 가용 현금 {format_compact_won(judgment['available_cash'])}으로는 부족합니다."
        )
    else:
        st.success(
            f"매수 가능: 매수 후 현금 잔액 "
            f"{format_compact_won(judgment['cash_balance_after_purchase'])}."
        )
    st.caption(
        "총 필요 현금은 매수가, 취득세, 중개보수, 예비비 등을 반영한 자기자본 기준입니다. "
        "추가 필요 현금은 현재 가용 현금으로 부족한 금액입니다."
    )


def _render_core_cash_metrics(result: dict) -> None:
    judgment = _cash_judgment(result)

    top_cols = st.columns([1.35, 1, 1, 1])
    top_cols[0].metric("가용 현금", format_compact_won(judgment["available_cash"]))
    top_cols[1].metric("총 필요 현금", format_compact_won(judgment["required_cash"]))
    top_cols[2].metric(
        "추가 필요 현금",
        format_compact_won(judgment["additional_cash_required"]),
    )
    top_cols[3].metric("예상 대출", format_compact_won(result["expected_loan_amount"]))


def _render_explainability_summary(result: dict) -> None:
    reason_cols = st.columns(4)
    reason_cols[0].metric("투자점수", str(result["investment_score"]))
    reason_cols[0].caption(_investment_score_reason(result))
    reason_cols[1].metric("급매점수", f"{result['bargain_score']}점")
    reason_cols[1].caption(_bargain_score_reason(result))
    reason_cols[2].metric("전세가율", f"{result['jeonse_ratio']:.1f}%")
    reason_cols[2].caption(_jeonse_ratio_reason(result.get("jeonse_ratio")))
    reason_cols[3].metric("단지등급", _complex_grade_label(result.get("complex_grade")))
    reason_cols[3].caption(_complex_grade_reason(result))

    bargain_rows = [
        {
            "항목": "최근 평균가",
            "값": format_compact_won(result["derived_inputs"]["recent_avg_price"]),
        },
        {
            "항목": "1년 최고가",
            "값": format_compact_won(result["derived_inputs"]["one_year_high_price"]),
        },
        {
            "항목": "최근 평균가 대비 할인율",
            "값": _discount_vs_average_label(result.get("discount_vs_recent_avg")),
        },
        {
            "항목": "1년 최고가 대비 하락률",
            "값": _drop_from_high_label(result.get("drop_from_high")),
        },
    ]
    st.caption("급매 점수 근거")
    st.dataframe(pd.DataFrame(bargain_rows), use_container_width=True, hide_index=True)
    _render_investment_score_drivers(result)


def _cash_judgment(result: dict) -> dict[str, int | bool]:
    required_cash = int(result["required_cash"])
    purchase_power = result.get("purchase_power") or {}
    available_cash = int(purchase_power.get("available_cash_for_purchase") or 0)
    cash_balance_after_purchase = available_cash - required_cash
    additional_cash_required = max(required_cash - available_cash, 0)
    return {
        "available_cash": available_cash,
        "required_cash": required_cash,
        "additional_cash_required": additional_cash_required,
        "cash_balance_after_purchase": cash_balance_after_purchase,
        "can_purchase": available_cash >= required_cash,
    }


def _render_profile_purchase_power_preview(profile: dict, funding_mode: str) -> None:
    cash_amount = int(profile.get("cash_amount") or 0)
    owned_real_estate_value = int(profile.get("owned_real_estate_value") or 0)
    owned_real_estate_debt = int(profile.get("owned_real_estate_debt") or 0)
    sale_net_cash = (
        max(owned_real_estate_value - owned_real_estate_debt, 0)
        if funding_mode == SELL_OWNED_REAL_ESTATE
        else 0
    )
    available_cash = cash_amount + sale_net_cash
    if funding_mode == SELL_OWNED_REAL_ESTATE and owned_real_estate_value <= 0:
        st.warning("보유 부동산 시가가 0원입니다. 자금 프로필에서 처분 대상 부동산 금액을 먼저 입력해 주세요.")
    st.caption(
        "가용 현금 기준: "
        f"{format_compact_won(available_cash)} "
        f"(보유 현금 {format_compact_won(cash_amount)}"
        + (
            f" + 처분 순현금 {format_compact_won(sale_net_cash)})"
            if funding_mode == SELL_OWNED_REAL_ESTATE
            else ")"
        )
    )


def _render_purchase_power_table(result: dict) -> None:
    purchase_power = result.get("purchase_power") or {}
    if not purchase_power:
        return
    rows = [
        {
            "항목": "자금 사용 시나리오",
            "값": FUNDING_MODE_LABELS.get(result.get("funding_mode"), result.get("funding_mode")),
        },
        {
            "항목": "보유 현금",
            "값": format_compact_won(purchase_power.get("cash_amount") or 0),
        },
        {
            "항목": "보유 부동산 시가",
            "값": format_compact_won(purchase_power.get("owned_real_estate_value") or 0),
        },
        {
            "항목": "보유 부동산 대출 잔액",
            "값": format_compact_won(purchase_power.get("owned_real_estate_debt") or 0),
        },
        {
            "항목": "처분 후 순현금",
            "값": format_compact_won(purchase_power.get("sale_net_cash") or 0),
        },
        {
            "항목": "가용 현금 기준",
            "값": format_compact_won(purchase_power.get("available_cash_for_purchase") or 0),
        },
        {
            "항목": "대출 심사 반영 기존 부채",
            "값": format_compact_won(purchase_power.get("existing_debt_for_loan_screening") or 0),
        },
    ]
    st.write("자금 사용 기준")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_source_table(result: dict) -> None:
    rows = [
        {
            "항목": "최근 평균가",
            "적용값": format_compact_won(result["derived_inputs"]["recent_avg_price"]),
            "출처": _source_label(result["sources"]["recent_avg_price"]),
        },
        {
            "항목": "최근 1년 최고가",
            "적용값": format_compact_won(result["derived_inputs"]["one_year_high_price"]),
            "출처": _source_label(result["sources"]["one_year_high_price"]),
        },
        {
            "항목": "예상 전세가",
            "적용값": format_compact_won(result["expected_jeonse_price"]),
            "출처": _source_label(result["sources"]["expected_jeonse_price"]),
        },
        {
            "항목": "세금 규칙",
            "적용값": _display_value(result["applied_tax_rule_version"]),
            "출처": _display_value("config/tax_rules.py"),
        },
        {
            "항목": "중개/비용 규칙",
            "적용값": _display_value(result["applied_brokerage_rule_version"]),
            "출처": _display_value("config/brokerage_rules.py"),
        },
        {
            "항목": "대출 규칙",
            "적용값": _display_value(result["loan_rule_version"]),
            "출처": _source_label(result["loan_terms"]["ltv_source"]),
        },
        {
            "항목": "대출 지역 판정",
            "적용값": _loan_region_type_label(result["resolved_region_type"]),
            "출처": _source_label(result["region_policy_source"]),
        },
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_applied_rules_panel(result: dict) -> None:
    applied_rules = result.get("applied_rules") or {}
    if not applied_rules:
        st.caption("이번 분석에 사용된 계산 룰 설명 정보가 없습니다.")
        return

    loan_ltv = applied_rules.get("loan_ltv") or {}
    base_price = loan_ltv.get("base_price")
    applied_ltv_rate = loan_ltv.get("applied_ltv_rate")
    loan_amount_by_ltv = loan_ltv.get("loan_amount_by_ltv")
    expected_loan_amount = loan_ltv.get("expected_loan_amount")
    loan_rows = [
        {"항목": "기준 가격", "값": _format_optional_money(base_price)},
        {"항목": "적용 LTV", "값": _format_ratio_percent(applied_ltv_rate)},
        {"항목": "LTV 기준 대출 한도", "값": _format_optional_money(loan_amount_by_ltv)},
        {
            "항목": "DSR 기준 대출 한도",
            "값": _format_optional_money(loan_ltv.get("dsr_based_loan_limit")),
        },
        {
            "항목": "가격구간 최대한도",
            "값": _format_unlimited_money(loan_ltv.get("max_loan_amount")),
        },
        {
            "항목": "정책 제한 후 대출",
            "값": _format_optional_money(loan_ltv.get("policy_capped_loan_amount")),
        },
        {
            "항목": "수동 예상대출 상한",
            "값": _format_optional_money(loan_ltv.get("manual_loan_amount_override")),
        },
        {"항목": "최종 예상 대출", "값": _format_optional_money(expected_loan_amount)},
        {"항목": "최종 제한 요인", "값": _display_value(loan_ltv.get("final_limiting_factor"))},
        {
            "항목": "LTV 적용 방식",
            "값": _applied_method_label(loan_ltv.get("ltv_method")),
        },
        {
            "항목": "수동 LTV 사용 여부",
            "값": "예" if loan_ltv.get("manual_ltv_used") else "아니오",
        },
        {
            "항목": "수동 LTV 출처",
            "값": _manual_ltv_source_label(loan_ltv.get("manual_ltv_source")),
        },
        {
            "항목": "적용 규제",
            "값": _loan_region_type_label(loan_ltv.get("applied_region_type")),
        },
        {
            "항목": "매칭된 규칙 지역 유형",
            "값": _loan_region_type_label(loan_ltv.get("matched_rule_region_type")),
        },
        {
            "항목": "규칙 fallback 사용",
            "값": "예" if loan_ltv.get("used_regulated_fallback") else "아니오",
        },
        {
            "항목": "규칙 매칭 안내",
            "값": _display_value(loan_ltv.get("fallback_notice")),
        },
        {
            "항목": "지역 판정 출처",
            "값": _source_label(loan_ltv.get("region_policy_source")),
        },
        {
            "항목": "적용 대출 규칙",
            "값": _rule_name(
                loan_ltv.get("matched_rule_description"),
                loan_ltv.get("matched_rule_version"),
            ),
        },
        {
            "항목": "예상 대출 적용 방식",
            "값": _applied_method_label(loan_ltv.get("loan_amount_method")),
        },
        {"항목": "계산식", "값": _ltv_formula_label(loan_ltv)},
    ]
    st.write("대출/LTV")
    st.dataframe(pd.DataFrame(loan_rows), use_container_width=True, hide_index=True)

    dsr = applied_rules.get("dsr") or {}
    dsr_rows = [
        {"항목": "연소득", "값": _format_optional_money(dsr.get("annual_income"))},
        {"항목": "DSR", "값": _format_optional_percent(dsr.get("dsr"))},
        {"항목": "DSR 한도", "값": _format_ratio_percent(dsr.get("applied_dsr_rate"))},
        {
            "항목": "DSR 기준 대출 한도",
            "값": _format_optional_money(dsr.get("dsr_based_loan_limit")),
        },
        {"항목": "계산 불가 사유", "값": _display_value(dsr.get("missing_reason"))},
    ]
    st.write("DSR")
    st.dataframe(pd.DataFrame(dsr_rows), use_container_width=True, hide_index=True)

    monthly_repayment = applied_rules.get("monthly_repayment") or {}
    repayment_rows = [
        {
            "항목": "금리",
            "값": _format_ratio_percent(monthly_repayment.get("annual_interest_rate")),
        },
        {
            "항목": "대출기간",
            "값": _loan_term_label(monthly_repayment.get("loan_term_years"), fixed=True),
        },
        {
            "항목": "월상환액",
            "값": _format_optional_money(monthly_repayment.get("monthly_repayment")),
        },
        {
            "항목": "계산 불가 사유",
            "값": _display_value(monthly_repayment.get("missing_reason")),
        },
    ]
    st.write("월상환액")
    st.dataframe(pd.DataFrame(repayment_rows), use_container_width=True, hide_index=True)

    transaction_costs = applied_rules.get("transaction_costs") or {}
    cost_rows = [
        {
            "항목": "취득세 적용 방식",
            "값": _cost_rule_method_label(transaction_costs.get("tax_manual_override")),
        },
        {
            "항목": "취득세 규칙",
            "값": _rule_name(
                transaction_costs.get("tax_rule_description"),
                transaction_costs.get("tax_rule_version"),
            ),
        },
        {
            "항목": "중개보수 적용 방식",
            "값": _cost_rule_method_label(
                transaction_costs.get("brokerage_manual_override")
            ),
        },
        {
            "항목": "중개/비용 규칙",
            "값": _rule_name(
                transaction_costs.get("brokerage_rule_description"),
                transaction_costs.get("brokerage_rule_version"),
            ),
        },
        {
            "항목": "수동 보정 사용 여부",
            "값": "예" if transaction_costs.get("manual_override_used") else "아니오",
        },
        {
            "항목": "수동 보정 항목",
            "값": _joined_labels(transaction_costs.get("manual_override_items")),
        },
    ]
    st.write("거래비용")
    st.dataframe(pd.DataFrame(cost_rows), use_container_width=True, hide_index=True)


def _render_cost_table(result: dict) -> None:
    rows = [
        {
            "항목": "취득세",
            "금액": format_compact_won(result["costs"]["acquisition_tax"]),
        },
        {
            "항목": "지방교육세",
            "금액": format_compact_won(result["costs"]["local_education_tax"]),
        },
        {
            "항목": "중개보수",
            "금액": format_compact_won(result["costs"]["brokerage_fee"]),
        },
        {
            "항목": "법무비",
            "금액": format_compact_won(result["costs"]["legal_fee"]),
        },
        {
            "항목": "예비비",
            "금액": format_compact_won(result["costs"]["reserve_cost"]),
        },
        {
            "항목": "수리비",
            "금액": format_compact_won(result["costs"]["repair_cost"]),
        },
        {
            "항목": "총 거래비용",
            "금액": format_compact_won(result["costs"]["total_transaction_cost"]),
        },
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_active_region_policy_table(result: dict) -> None:
    st.write("현재 적용 지역 규제")
    policies = result.get("active_region_policies", [])
    if not policies:
        st.caption("현재 분석 대상 지역에 적용 중인 지역 규제가 없습니다.")
        return

    rows = [
        {
            "규제 유형": _region_policy_type_label(_display_value(policy.get("policy_type"))),
            "적용 지역": policy.get("region_scope") or _region_scope_label(policy),
            "지역 레벨": _region_level_label(_display_value(policy.get("region_level"))),
            "시작일": _display_value(policy.get("effective_from")),
            "종료일": policy.get("effective_to") or "-",
            "대출 지역 판정": _loan_region_type_label(policy.get("loan_region_type")),
            "메모": policy.get("notes") or "-",
        }
        for policy in policies
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_complex_profile_table(result: dict) -> None:
    profile = result["complex_profile"]
    rows = [
        {"항목": "단지 등급", "값": _complex_grade_label(profile.get("complex_grade"))},
        {"항목": "유동성 점수", "값": _display_value(profile.get("liquidity_score"))},
        {"항목": "유동성 해석", "값": _liquidity_label(profile.get("liquidity_label"))},
        {"항목": "최근 매매 거래 수", "값": _display_value(profile.get("recent_sale_transaction_count"))},
        {"항목": "최근 전세 거래 수", "값": _display_value(profile.get("recent_rent_transaction_count"))},
        {"항목": "거래 빈도", "값": _display_value(profile.get("transaction_frequency"))},
        {"항목": "지역 평균가 순위", "값": _display_value(profile.get("average_sale_price_rank"))},
        {"항목": "평당가 순위", "값": _display_value(profile.get("price_per_area_rank"))},
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_policy_event_table(result: dict) -> None:
    st.write("관련 정책 참고")
    events = result.get("relevant_policy_events", [])
    if not events:
        st.caption("현재 분석 조건에 맞는 정책 이벤트가 없습니다.")
        return

    rows = [
        {
            "제목": event["title"],
            "요약": event["summary"],
            "영향도": _impact_level_label(event["impact_level"]),
            "시작일": event["effective_from"],
            "종료일": event.get("effective_to") or "-",
            "반영 방식": (
                "계산 지원 참고"
                if event["reference_mode"] == "CALCULATION_SUPPORTED_REFERENCE"
                else "참고 전용"
            ),
            "출처": event.get("source_name") or "-",
        }
        for event in events
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_formula_explainer(result: dict) -> None:
    lines = [
        f"- 매물가: {format_won(result['sale_price'])}",
        f"- 예상 대출: {format_won(result['expected_loan_amount'])}",
        f"- 총 거래비용: {format_won(result['costs']['total_transaction_cost'])}",
    ]
    if result["primary_user_mode"] == "INVESTMENT":
        lines.extend(
            [
                f"- 예상 전세가: {format_won(result['expected_jeonse_price'])}",
                "- 총 필요 현금 = 매물가 - 예상 대출 - 예상 전세가 + 총 거래비용 + 수리비",
                (
                    f"- 계산 결과: 총 필요 현금 {format_won(result['required_cash'])} / "
                    f"추가 필요 현금 {format_won(_cash_judgment(result)['additional_cash_required'])}"
                ),
            ]
        )
    else:
        lines.extend(
            [
                "- 총 필요 현금 = 매물가 - 예상 대출 + 총 거래비용 + 수리비",
                (
                    f"- 계산 결과: 총 필요 현금 {format_won(result['required_cash'])} / "
                    f"추가 필요 현금 {format_won(_cash_judgment(result)['additional_cash_required'])}"
                ),
            ]
        )
    lines.extend(
        [
            f"- 급매 점수: {result['bargain_score']}",
            f"- 유동성 점수: {result['liquidity_score']}",
            f"- 단지 등급: {_complex_grade_label(result.get('complex_grade'))}",
            f"- 투자점수: {result['investment_score']}",
        ]
    )
    st.markdown("\n".join(lines))


def _render_transaction_summary(transaction_context: dict) -> None:
    st.subheader("거래 요약")
    metrics = transaction_context["market_metrics"]
    st.caption(
        f"최근 매매 {metrics['sale_transaction_count']}건, "
        f"최근 전세 {metrics['rent_transaction_count']}건 기준으로 계산했습니다."
    )

    cols = st.columns(4)
    cols[0].metric("최근 3개월 평균", format_compact_won(metrics["sale_avg_3m"]))
    cols[1].metric("최근 6개월 평균", format_compact_won(metrics["sale_avg_6m"]))
    cols[2].metric("최근 12개월 평균", format_compact_won(metrics["sale_avg_12m"]))
    cols[3].metric("최근 전세 평균", format_compact_won(metrics["latest_rent_deposit_avg"]))

    detail_cols = st.columns(4)
    detail_cols[0].metric("1년 최고가", format_compact_won(metrics["one_year_high"]))
    detail_cols[1].metric("1년 최저가", format_compact_won(metrics["one_year_low"]))
    detail_cols[2].metric("매매 거래 수", str(metrics["sale_transaction_count"]))
    detail_cols[3].metric("전세 거래 수", str(metrics["rent_transaction_count"]))


def _render_transaction_history(transaction_context: dict) -> None:
    sale_history = pd.DataFrame(transaction_context["sale_history"])
    rent_history = pd.DataFrame(transaction_context["rent_history"])

    st.subheader("거래 추이")
    chart_frames: list[pd.DataFrame] = []
    if not sale_history.empty:
        chart_frames.append(
            sale_history[["deal_date", "price"]]
            .rename(columns={"price": "amount"})
            .assign(kind="매매")
        )
    if not rent_history.empty:
        chart_frames.append(
            rent_history[["deal_date", "deposit"]]
            .rename(columns={"deposit": "amount"})
            .assign(kind="전세")
        )

    if chart_frames:
        chart_df = pd.concat(chart_frames, ignore_index=True)
        chart_df["amount_eok"] = chart_df["amount"].map(to_eok)
        chart = px.line(
            chart_df,
            x="deal_date",
            y="amount_eok",
            color="kind",
            markers=True,
            title="최근 12개월 가격 추이",
            hover_data={"amount": True, "amount_eok": False},
        )
        st.plotly_chart(chart, use_container_width=True)

    with st.expander("상세: 원본 거래 이력", expanded=False):
        sale_tab, rent_tab = st.tabs(["매매 이력", "전세 이력"])
        with sale_tab:
            if sale_history.empty:
                st.caption("매매 거래 데이터가 없습니다.")
            else:
                sale_df = sale_history[["deal_date", "area_m2", "price", "floor"]].copy()
                sale_df["price"] = sale_df["price"].map(to_eok)
                sale_df = sale_df.rename(
                    columns={
                        "deal_date": "거래일",
                        "area_m2": "면적(m2)",
                        "price": "거래가(억 원)",
                        "floor": "층",
                    }
                )
                st.dataframe(
                    sale_df.sort_values("거래일", ascending=False),
                    use_container_width=True,
                    hide_index=True,
                )
        with rent_tab:
            if rent_history.empty:
                st.caption("전세 거래 데이터가 없습니다.")
            else:
                rent_df = rent_history[["deal_date", "area_m2", "deposit", "floor"]].copy()
                rent_df["deposit"] = rent_df["deposit"].map(to_eok)
                rent_df = rent_df.rename(
                    columns={
                        "deal_date": "거래일",
                        "area_m2": "면적(m2)",
                        "deposit": "보증금(억 원)",
                        "floor": "층",
                    }
                )
                st.dataframe(
                    rent_df.sort_values("거래일", ascending=False),
                    use_container_width=True,
                    hide_index=True,
                )


def _render_recent_analysis_history(recent_results: list[dict]) -> None:
    st.divider()
    with st.expander("상세: 최근 분석 이력", expanded=False):
        if not recent_results:
            st.caption("저장된 분석 결과가 없습니다.")
            return

        history_df = pd.DataFrame(recent_results)[
            [
                "complex_name",
                "sale_price",
                "required_cash",
                "shortage_cash",
                "bargain_score",
                "liquidity_score",
                "investment_score",
                "complex_grade",
                "created_at",
            ]
        ].rename(
            columns={
                "complex_name": "단지",
                "sale_price": "매물가",
                "required_cash": "총 필요 현금",
                "shortage_cash": "추가 필요 현금",
                "bargain_score": "급매 점수",
                "liquidity_score": "유동성 점수",
                "investment_score": "투자점수",
                "complex_grade": "단지 등급",
                "created_at": "분석일",
            }
        )
        history_df["추가 필요 현금"] = history_df["추가 필요 현금"].map(
            lambda value: max(int(value or 0), 0)
        )
        for column in ["매물가", "총 필요 현금", "추가 필요 현금"]:
            history_df[column] = history_df[column].map(format_compact_won)
        history_df["단지 등급"] = history_df["단지 등급"].map(_complex_grade_label)
        history_df = history_df.fillna("-")
        st.dataframe(history_df, use_container_width=True, hide_index=True)

        chart_df = pd.DataFrame(recent_results).head(10).copy()
        chart_df["complex_grade_label"] = chart_df["complex_grade"].map(_complex_grade_label)
        chart = px.bar(
            chart_df,
            x="complex_name",
            y="investment_score",
            color="complex_grade_label",
            title="최근 투자점수",
            labels={
                "complex_name": "단지",
                "investment_score": "투자점수",
                "complex_grade_label": "단지 등급",
            },
        )
        st.plotly_chart(chart, use_container_width=True)


def _to_primary_mode(investment_type: str | None) -> str:
    return "OWNER_OCCUPIED" if investment_type == "OWNER_OCCUPIED" else "INVESTMENT"


def _to_optional_won(value_eok: float) -> int | None:
    if value_eok <= 0:
        return None
    return int(from_eok(value_eok))


def _to_optional_float(value: float) -> float | None:
    if value <= 0:
        return None
    return float(value)


def _format_optional_money(value: int | None) -> str:
    if _is_missing_value(value):
        return "정보 없음"
    return format_compact_won(value)


def _format_unlimited_money(value: int | None) -> str:
    if _is_missing_value(value):
        return "제한 없음"
    return format_compact_won(value)


def _format_optional_percent(value: float | None) -> str:
    if _is_missing_value(value):
        return "정보 없음"
    return f"{value:.1f}%"


def _format_ratio_percent(value: float | None) -> str:
    if _is_missing_value(value):
        return "정보 없음"
    return f"{float(value) * 100:.1f}%"


def _high_interest_rate_warning(result: dict) -> str | None:
    interest_rate = (
        ((result.get("applied_rules") or {}).get("monthly_repayment") or {}).get(
            "annual_interest_rate"
        )
    )
    if interest_rate is None:
        return None
    normalized_rate = float(interest_rate)
    if normalized_rate < 0.2:
        return None
    return (
        f"현재 적용 금리 {_format_ratio_percent(normalized_rate)}. "
        "일반적인 주택담보대출 금리 범위를 크게 초과합니다. 금리 입력값을 확인하세요."
    )


def _applied_method_label(value: object) -> str:
    text = _display_value(value)
    return {
        "AUTO_RULE": "자동 계산",
        "MANUAL_OVERRIDE": "수동 보정",
    }.get(text, text)


def _manual_ltv_source_label(value: object) -> str:
    text = _display_value(value)
    return {
        "ANALYSIS_INPUT": "분석 화면 수동 보정",
        "FINANCE_PROFILE": "자금 프로필 수동 LTV",
        "UNKNOWN": "-",
    }.get(text, text)


def _cost_rule_method_label(manual_override: object) -> str:
    return "수동 보정" if bool(manual_override) else "자동 계산"


def _loan_term_label(value: object, *, fixed: bool = False) -> str:
    if _is_missing_value(value):
        return "정보 없음"
    label = f"{int(value)}년"
    if fixed:
        return f"{label} 고정"
    return label


def _joined_labels(values: object) -> str:
    if not values:
        return "-"
    return ", ".join(str(value) for value in values)


def _rule_name(description: object, version: object) -> str:
    description_text = _display_value(description)
    version_text = _display_value(version)
    if description_text != "-" and version_text != "-":
        return f"{description_text} ({version_text})"
    if description_text != "-":
        return description_text
    return version_text


def _ltv_formula_label(loan_ltv: dict) -> str:
    base_price = loan_ltv.get("base_price")
    applied_ltv_rate = loan_ltv.get("applied_ltv_rate")
    loan_amount_by_ltv = loan_ltv.get("loan_amount_by_ltv")
    if (
        _is_missing_value(base_price)
        or _is_missing_value(applied_ltv_rate)
        or _is_missing_value(loan_amount_by_ltv)
    ):
        return "정보 없음"
    return (
        f"{format_compact_won(base_price)} × {_format_ratio_percent(applied_ltv_rate)}"
        f" = {_format_optional_money(loan_amount_by_ltv)}"
    )


def _missing_metric_reason(
    metric_key: str,
    value: object,
    explicit_reason: str | None = None,
) -> str | None:
    if not _is_missing_value(value):
        return None
    if explicit_reason:
        return explicit_reason
    return {
        "monthly_repayment": "금리 정보가 없어 계산하지 않았습니다.",
        "dsr": "연소득 정보가 없어 계산하지 않았습니다.",
    }.get(metric_key)


def _is_missing_value(value: object) -> bool:
    return value is None or pd.isna(value)


def _format_efficiency(value: float | None) -> str:
    if _is_missing_value(value):
        return "계산 불가"
    return f"{value:.2f}배"


def _format_signed_percent(value: float | None) -> str:
    if _is_missing_value(value):
        return "정보 없음"
    return f"{float(value):.1f}%"


def _discount_vs_average_label(value: float | None) -> str:
    if _is_missing_value(value):
        return "정보 없음"
    discount_rate = float(value)
    if discount_rate < 0:
        return f"최근 평균 대비 {abs(discount_rate):.1f}% 비쌈"
    if discount_rate == 0:
        return "할인 없음"
    return f"{discount_rate:.1f}% 할인"


def _drop_from_high_label(value: float | None) -> str:
    if _is_missing_value(value):
        return "정보 없음"
    drop_rate = float(value)
    if drop_rate < 0:
        return f"1년 최고가 대비 {abs(drop_rate):.1f}% 비쌈"
    if drop_rate == 0:
        return "하락 없음"
    return f"{drop_rate:.1f}% 하락"


def _display_value(value: object, *, empty: str = "-") -> str:
    if _is_missing_value(value):
        return empty
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "null"}:
        return empty
    return text


def _source_label(value: object) -> str:
    text = _display_value(value)
    return {
        "default": "기본값",
        "manual override": "수동 보정",
        "profile manual ltv": "자금 프로필 수동 LTV",
        "rule application": "규칙 엔진 적용",
        "region_policy_status": "지역 규제 상태",
    }.get(text, text)


def _liquidity_label(value: object) -> str:
    text = _display_value(value, empty="정보 없음")
    return {
        "high liquidity": "유동성 높음",
        "medium liquidity": "유동성 보통",
        "normal liquidity": "유동성 보통",
        "low liquidity": "유동성 낮음",
    }.get(text, text)


def _investment_score_reason(result: dict) -> str:
    shortage_cash = int(result.get("shortage_cash") or 0)
    score = int(result.get("investment_score") or 0)
    if shortage_cash > 0:
        return "추가 필요 현금 부담이 큼"
    if score >= 70:
        return "급매·유동성·자금 효율이 전반적으로 양호"
    if score >= 50:
        return "급매도와 유동성은 보통 수준"
    return "급매도·유동성·자금 효율 점수가 낮음"


def _render_investment_score_drivers(result: dict) -> None:
    positive_factors = _investment_score_positive_factors(result)
    negative_factors = _investment_score_negative_factors(result)
    if not positive_factors and not negative_factors:
        return

    st.write("투자점수 주요 요인")
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**긍정 요인**")
        if positive_factors:
            for factor in positive_factors:
                st.write(f"- {factor}")
        else:
            st.caption("뚜렷한 긍정 요인 없음")
    with cols[1]:
        st.markdown("**감점 요인**")
        if negative_factors:
            for factor in negative_factors:
                st.write(f"- {factor}")
        else:
            st.caption("뚜렷한 감점 요인 없음")

    st.caption("전세가율은 투자점수에 직접 반영되기보다 급매/투자 매력 판단에 참고됩니다.")


def _investment_score_positive_factors(result: dict) -> list[str]:
    factors: list[str] = []
    liquidity_score = result.get("liquidity_score")
    if liquidity_score is not None and float(liquidity_score) >= 80:
        factors.append("유동성 점수가 높아 매도 가능성은 양호합니다.")

    complex_grade = str(result.get("complex_grade") or "")
    if complex_grade in {"LEADER", "SUB_LEADER"}:
        factors.append("단지등급이 높아 입지/수요 측면에서 긍정적입니다.")

    efficiency_score = result.get("required_cash_efficiency_score")
    if efficiency_score is not None and float(efficiency_score) >= 60:
        factors.append("자금효율이 양호해 필요한 자기자본 부담이 상대적으로 낮습니다.")

    bargain_score = result.get("bargain_score")
    if bargain_score is not None and float(bargain_score) >= 60:
        factors.append("급매점수가 높아 가격 매력도가 있습니다.")

    jeonse_ratio = result.get("jeonse_ratio")
    if jeonse_ratio is not None and float(jeonse_ratio) >= 70:
        factors.append("전세가율이 높아 자금 회수 측면에서 유리합니다.")
    return factors


def _investment_score_negative_factors(result: dict) -> list[str]:
    factors: list[str] = []
    shortage_cash = int(result.get("shortage_cash") or 0)
    if shortage_cash > 0:
        factors.append(f"추가 필요 현금이 커서 점수에 불리합니다. ({format_compact_won(shortage_cash)})")

    bargain_score = result.get("bargain_score")
    if bargain_score is not None and float(bargain_score) <= 20:
        factors.append("급매점수가 낮아 매수 매력은 제한적입니다.")

    jeonse_ratio = result.get("jeonse_ratio")
    if jeonse_ratio is not None and float(jeonse_ratio) < 60:
        factors.append("전세가율이 낮아 투자 매력 보완 요인이 약합니다.")

    liquidity_score = result.get("liquidity_score")
    if liquidity_score is not None and float(liquidity_score) < 35:
        factors.append("유동성 점수가 낮아 매도 가능성은 보수적으로 봐야 합니다.")

    efficiency_score = result.get("required_cash_efficiency_score")
    if efficiency_score is not None and float(efficiency_score) < 40:
        factors.append("자금효율이 낮아 필요한 자기자본 부담이 큽니다.")

    complex_grade = str(result.get("complex_grade") or "")
    if complex_grade in {"SMALL", "RISKY"}:
        factors.append("단지등급이 낮아 입지/수요 측면에서 보수적입니다.")
    return factors


def _bargain_score_reason(result: dict) -> str:
    discount_rate = float(result.get("discount_vs_recent_avg") or 0.0)
    drop_from_high = float(result.get("drop_from_high") or 0.0)
    if discount_rate >= 10:
        return "최근 평균가 대비 할인 폭이 큼"
    if discount_rate >= 5:
        return "최근 평균가 대비 의미 있는 할인"
    if drop_from_high >= 10:
        return "고점 대비 하락은 있으나 할인 폭은 제한적"
    return "최근 평균가 대비 할인 없음"


def _jeonse_ratio_reason(value: float | None) -> str:
    if _is_missing_value(value):
        return "설명 정보 없음"
    ratio = float(value)
    if ratio >= 70:
        return "높음"
    if ratio >= 60:
        return "보통"
    return "낮음"


def _complex_grade_reason(result: dict) -> str:
    profile = result.get("complex_profile") or {}
    liquidity_score = int(profile.get("liquidity_score") or 0)
    sale_count = int(profile.get("recent_sale_transaction_count") or 0)
    rent_count = int(profile.get("recent_rent_transaction_count") or 0)
    if liquidity_score >= 80 or sale_count + rent_count >= 12:
        return "유동성과 거래량 반영"
    if liquidity_score < 35 or sale_count + rent_count < 3:
        return "유동성 또는 거래량이 약함"
    return "유동성과 거래량을 함께 반영"


def _impact_level_label(value: object) -> str:
    text = _display_value(value)
    return {
        "HIGH": "높음",
        "MEDIUM": "보통",
        "LOW": "낮음",
    }.get(text, text)


def _region_policy_type_label(value: str) -> str:
    return {
        "REGULATED_AREA": "규제지역",
        "NON_REGULATED_AREA": "비규제지역",
        "LAND_TRANSACTION_PERMISSION": "토지거래허가구역",
        "LAND_TRANSACTION_PERMISSION_AREA": "토지거래허가구역",
        "SPECULATION_OVERHEATED_DISTRICT": "투기과열지구",
        "SPECULATION_OVERHEATED": "투기과열지구",
        "ADJUSTMENT_TARGET_AREA": "조정대상지역",
        "ADJUSTMENT_TARGET": "조정대상지역",
    }.get(value, value)


def _region_level_label(value: str) -> str:
    return {
        "SIDO": "시도",
        "SIGUNGU": "시군구",
        "DONG": "동",
    }.get(value, value)


def _loan_region_type_label(value: str | None) -> str:
    return {
        "REGULATED": "공통 규제 규칙",
        "NON_REGULATED": "비규제지역",
        "ADJUSTMENT_TARGET": "조정대상지역",
        "ADJUSTMENT_TARGET_AREA": "조정대상지역",
        "SPECULATION_OVERHEATED": "투기과열지구",
        "SPECULATION_OVERHEATED_DISTRICT": "투기과열지구",
        "LAND_TRANSACTION_PERMISSION": "토지거래허가구역",
        "LAND_TRANSACTION_PERMISSION_AREA": "토지거래허가구역",
        None: "-",
    }.get(value, str(value))


def _region_scope_label(policy: dict) -> str:
    parts = [
        str(policy.get("sido") or "").strip(),
        str(policy.get("sigungu") or "").strip(),
        str(policy.get("dong") or "").strip(),
    ]
    return " ".join(part for part in parts if part) or "-"


def _complex_grade_label(value: str | None) -> str:
    labels = {
        "LEADER": "대장",
        "SUB_LEADER": "준대장",
        "GENERAL": "일반",
        "NORMAL": "일반",
        "SMALL": "나홀로",
        "RISKY": "유동성주의",
    }
    return labels.get(value or "", value or "-")
