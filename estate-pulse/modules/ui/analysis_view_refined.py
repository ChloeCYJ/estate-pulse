from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import AppSettings
from modules.services.analysis_service import (
    CASH_ONLY,
    SELL_OWNED_REAL_ESTATE,
    AnalysisService,
    BenchmarkInputs,
)
from modules.ui.analysis_view import (
    _cash_judgment,
    _display_value,
    _format_optional_money,
    _format_unlimited_money,
    _high_interest_rate_warning,
    _missing_metric_reason,
    _render_active_region_policy_table,
    _render_applied_rules_panel,
    _render_complex_profile_table,
    _render_cost_table,
    _render_formula_explainer,
    _render_policy_event_table,
    _render_profile_purchase_power_preview,
    _render_purchase_power_table,
    _render_recent_analysis_history,
    _render_source_table,
    _render_transaction_history,
    _render_transaction_summary,
    _to_optional_float,
    _to_optional_won,
)
from modules.utils.money_utils import format_compact_won, from_eok

FUNDING_MODE_LABELS = {
    CASH_ONLY: "보유 현금만 사용",
    SELL_OWNED_REAL_ESTATE: "보유 부동산 처분 후 매수",
}
LAST_ANALYSIS_RESULT_KEY = "analysis_v2_last_result"
LAST_ANALYSIS_TARGET_KEY = "analysis_v2_last_target"
LAST_ANALYSIS_BENCHMARKS_KEY = "analysis_v2_last_benchmarks"


def render_analysis_page(
    *,
    complex_repository,
    listing_repository,
    finance_repository,
    analysis_repository,
    analysis_service: AnalysisService,
    settings: AppSettings,
) -> None:
    del listing_repository, settings

    st.title("분석")
    st.caption(
        "단지와 평형을 선택하면 최근 실거래 기준으로 바로 기본 분석합니다. "
        "같은 단지·평형에 등록 매물이 있으면 호가 기준으로 다시 분석할 수 있습니다."
    )

    profiles = finance_repository.list_all()
    complexes = complex_repository.list_all()
    if not profiles:
        st.info("먼저 자금 프로필을 등록해 주세요.")
        return
    if not complexes:
        st.info("먼저 단지를 등록해 주세요.")
        return

    profile_options = {
        f"#{item['id']} | 보유 현금 {format_compact_won(item['cash_amount'])}": item
        for item in profiles
    }
    selected_profile = profile_options[
        st.selectbox("자금 프로필", list(profile_options.keys()))
    ]

    complex_options = {f"#{item['id']} | {item['name']}": item for item in complexes}
    selected_complex = complex_options[
        st.selectbox("단지", list(complex_options.keys()))
    ]

    area_options = analysis_service.list_complex_area_options(
        complex_id=int(selected_complex["id"])
    )
    if not area_options:
        st.info("이 단지에는 아직 분석 가능한 평형 구간이 없습니다.")
        return

    area_option_map = {_area_option_label(item): item for item in area_options}
    selected_area_option = area_option_map[
        st.selectbox("평형 구간", list(area_option_map.keys()))
    ]
    selected_area_bucket = float(selected_area_option["area_bucket"])

    matching_listings = analysis_service.list_matching_listings(
        complex_id=int(selected_complex["id"]),
        area_m2=selected_area_bucket,
    )
    price_basis = "TRANSACTION_REFERENCE"
    selected_listing_id: int | None = None
    if matching_listings:
        price_basis = st.radio(
            "적용 기준가격",
            ["TRANSACTION_REFERENCE", "LISTING"],
            index=0,
            format_func=lambda value: (
                "최근 실거래 기준"
                if value == "TRANSACTION_REFERENCE"
                else "등록 매물 호가 기준"
            ),
            horizontal=True,
        )
        if price_basis == "LISTING":
            listing_options = {
                f"#{item['id']} | 호가 {format_compact_won(int(item['sale_price']))}": int(item["id"])
                for item in matching_listings
            }
            selected_listing_label = st.selectbox("등록 매물 선택", list(listing_options.keys()))
            selected_listing_id = listing_options[selected_listing_label]
        else:
            st.caption("최근 실거래 기준가격으로 기본 분석합니다.")
    else:
        st.caption("같은 단지·평형에 등록 매물이 없어 최근 실거래 기준으로 분석합니다.")

    try:
        transaction_context = analysis_service.get_transaction_context(
            complex_id=int(selected_complex["id"]),
            area_m2=selected_area_bucket,
        )
        _render_transaction_summary(transaction_context)
        _render_transaction_history(transaction_context)
    except ValueError as exc:
        st.warning(str(exc))

    with st.form("analysis_form_v2"):
        st.subheader("자금 설정")
        funding_mode = st.radio(
            "매수 자금 기준",
            list(FUNDING_MODE_LABELS.keys()),
            index=0,
            format_func=lambda value: FUNDING_MODE_LABELS[value],
            horizontal=True,
        )
        _render_profile_purchase_power_preview(selected_profile, funding_mode)

        with st.expander("고급 설정: 시장 입력 수동 보정", expanded=False):
            market_col1, market_col2 = st.columns(2)
            with market_col1:
                recent_avg_price_override_eok = st.number_input(
                    "최근 평균가 수동 보정 (억원)",
                    min_value=0.0,
                    step=0.1,
                    value=0.0,
                    format="%.2f",
                )
                one_year_high_price_override_eok = st.number_input(
                    "최근 1년 최고가 수동 보정 (억원)",
                    min_value=0.0,
                    step=0.1,
                    value=0.0,
                    format="%.2f",
                )
                repair_cost_eok = st.number_input(
                    "수리비 (억원)",
                    min_value=0.0,
                    step=0.1,
                    value=0.0,
                    format="%.2f",
                )
            with market_col2:
                expected_loan_amount_eok = st.number_input(
                    "예상 대출 수동 보정 (억원)",
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
                )

        with st.expander("고급 설정: 거래비용 수동 보정", expanded=False):
            cost_col1, cost_col2, cost_col3 = st.columns(3)
            with cost_col1:
                acquisition_tax_override_eok = st.number_input(
                    "취득세 수동 보정 (억원)",
                    min_value=0.0,
                    step=0.01,
                    value=0.0,
                    format="%.2f",
                )
                local_education_tax_override_eok = st.number_input(
                    "지방교육세 수동 보정 (억원)",
                    min_value=0.0,
                    step=0.01,
                    value=0.0,
                    format="%.2f",
                )
            with cost_col2:
                brokerage_fee_override_eok = st.number_input(
                    "중개보수 수동 보정 (억원)",
                    min_value=0.0,
                    step=0.01,
                    value=0.0,
                    format="%.2f",
                )
                legal_fee_override_eok = st.number_input(
                    "법무비 수동 보정 (억원)",
                    min_value=0.0,
                    step=0.01,
                    value=0.0,
                    format="%.2f",
                )
            with cost_col3:
                reserve_cost_override_eok = st.number_input(
                    "예비비 수동 보정 (억원)",
                    min_value=0.0,
                    step=0.01,
                    value=0.0,
                    format="%.2f",
                )

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
                analysis_mode="OWNER_OCCUPIED",
                acquisition_tax_override=_to_optional_won(acquisition_tax_override_eok),
                local_education_tax_override=_to_optional_won(local_education_tax_override_eok),
                brokerage_fee_override=_to_optional_won(brokerage_fee_override_eok),
                legal_fee_override=_to_optional_won(legal_fee_override_eok),
                reserve_cost_override=_to_optional_won(reserve_cost_override_eok),
            )
            result = analysis_service.run_complex_area_analysis(
                complex_id=int(selected_complex["id"]),
                area_m2=selected_area_bucket,
                listing_id=selected_listing_id,
                finance_profile_id=int(selected_profile["id"]),
                benchmarks=current_benchmarks,
                save_result=True,
            )
            st.session_state[LAST_ANALYSIS_RESULT_KEY] = result
            st.session_state[LAST_ANALYSIS_TARGET_KEY] = {
                "complex_id": int(selected_complex["id"]),
                "area_bucket": selected_area_bucket,
                "listing_id": selected_listing_id,
                "profile_id": int(selected_profile["id"]),
            }
            st.session_state[LAST_ANALYSIS_BENCHMARKS_KEY] = current_benchmarks
        except ValueError as exc:
            st.error(str(exc))

    current_result = _current_analysis_result(
        selected_complex_id=int(selected_complex["id"]),
        selected_area_bucket=selected_area_bucket,
        selected_listing_id=selected_listing_id,
        selected_profile_id=int(selected_profile["id"]),
    )
    if current_result:
        _render_analysis_metrics(current_result)

    _render_recent_analysis_history(analysis_repository.list_recent())


def _render_analysis_metrics(result: dict) -> None:
    st.subheader(
        f"{result['complex_name']} | {_format_area_bucket(result.get('area_bucket'))} 분석 결과"
    )
    interest_rate_warning = _high_interest_rate_warning(result)
    if interest_rate_warning:
        st.warning(interest_rate_warning)

    cash_judgment = _cash_judgment(result)
    applied_rules = result.get("applied_rules") or {}
    metrics = st.columns(4)
    metrics[0].metric(
        "매수 가능 여부",
        "가능" if cash_judgment["can_purchase"] else "추가 현금 필요",
    )
    metrics[1].metric(
        "추가 필요 현금",
        format_compact_won(cash_judgment["additional_cash_required"]),
    )
    metrics[2].metric(
        "분석 기준가격",
        format_compact_won(int(result["sale_price"])),
    )
    metrics[2].caption(_analysis_price_source_label(result.get("price_source")))
    metrics[3].metric(
        "예상 월 상환액",
        _format_optional_money(result["monthly_repayment"]),
    )
    repayment_reason = _missing_metric_reason(
        "monthly_repayment",
        result["monthly_repayment"],
        explicit_reason=(applied_rules.get("monthly_repayment") or {}).get(
            "missing_reason"
        ),
    )
    if repayment_reason:
        metrics[3].caption(repayment_reason)

    _render_financing_summary(result)
    st.caption(f"판정: {result['decision']}")

    with st.expander("기준가격 산정 근거 보기", expanded=False):
        _render_reference_price_basis(result)
    with st.expander("상세: 자금 여력", expanded=False):
        _render_purchase_power_table(result)
    with st.expander("상세: 계산 기준", expanded=False):
        _render_source_table(result)
    with st.expander("적용 계산 룰 보기", expanded=False):
        _render_applied_rules_panel(result)
    with st.expander("상세: 지역 규제 및 정책", expanded=False):
        _render_active_region_policy_table(result)
        _render_policy_event_table(result)
    with st.expander("상세: 거래비용", expanded=False):
        _render_cost_table(result)
    with st.expander("상세: 단지 프로필", expanded=False):
        _render_complex_profile_table(result)
    with st.expander("상세: 계산식 설명", expanded=False):
        _render_formula_explainer(result)


def _current_analysis_result(
    *,
    selected_complex_id: int,
    selected_area_bucket: float,
    selected_listing_id: int | None,
    selected_profile_id: int,
) -> dict | None:
    target = st.session_state.get(LAST_ANALYSIS_TARGET_KEY) or {}
    if int(target.get("complex_id") or 0) != int(selected_complex_id):
        return None
    if round(float(target.get("area_bucket") or 0.0), 1) != round(
        float(selected_area_bucket), 1
    ):
        return None
    if target.get("listing_id") != selected_listing_id:
        return None
    if int(target.get("profile_id") or 0) != int(selected_profile_id):
        return None
    return st.session_state.get(LAST_ANALYSIS_RESULT_KEY)


def _area_option_label(option: dict) -> str:
    listing_count = int(option.get("listing_count") or 0)
    sale_count = int(option.get("sale_transaction_count") or 0)
    return (
        f"{_format_area_bucket(option.get('area_bucket'))} | "
        f"등록 매물 {listing_count}건 | 실거래 {sale_count}건"
    )


def _format_area_bucket(value: object) -> str:
    if value is None:
        return "-"
    return f"{float(value):.1f}m²"


def _analysis_price_source_label(value: object) -> str:
    return {
        "LISTING": "등록 매물 호가",
        "TRANSACTION_REFERENCE": "최근 실거래 기준",
    }.get(str(value or ""), "-")


def _reference_confidence_label(value: object) -> str:
    return {
        "HIGH": "높음",
        "MEDIUM": "보통",
        "LOW": "낮음",
    }.get(str(value or ""), "-")


def _reference_volatility_label(value: object) -> str:
    return {
        "RAPID_RISE": "급상승",
        "RAPID_FALL": "급하락",
        "STABLE": "안정",
        "INSUFFICIENT_DATA": "표본 부족",
    }.get(str(value or ""), "-")


def _render_reference_price_basis(result: dict) -> None:
    metadata = result.get("reference_price_metadata") or {}
    if not metadata:
        st.caption("최근 실거래 기준가격 메타데이터가 없습니다.")
        return

    rows = [
        {"항목": "적용 가격", "값": format_compact_won(int(result["sale_price"]))},
        {
            "항목": "가격 출처",
            "값": _analysis_price_source_label(result.get("price_source")),
        },
        {
            "항목": "기준가격",
            "값": format_compact_won(int(metadata.get("reference_price") or 0)),
        },
        {"항목": "표본 수", "값": str(int(metadata.get("sample_count") or 0))},
        {
            "항목": "선정 가격 범위",
            "값": (
                f"{format_compact_won(int(metadata.get('sample_min_price') or 0))} ~ "
                f"{format_compact_won(int(metadata.get('sample_max_price') or 0))}"
            ),
        },
        {
            "항목": "최신 실거래일",
            "값": _display_value(metadata.get("latest_transaction_date")),
        },
        {
            "항목": "신뢰도",
            "값": _reference_confidence_label(metadata.get("confidence")),
        },
        {
            "항목": "변동성",
            "값": _reference_volatility_label(metadata.get("volatility_status")),
        },
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_financing_summary(result: dict) -> None:
    purchase_power = result.get("purchase_power") or {}
    loan_ltv = ((result.get("applied_rules") or {}).get("loan_ltv")) or {}

    finance_cols = st.columns(4)
    finance_cols[0].metric(
        "가용 현금",
        format_compact_won(int(purchase_power.get("available_cash_for_purchase") or 0)),
    )
    finance_cols[1].metric(
        "부동산 처분 후 순현금",
        format_compact_won(int(purchase_power.get("sale_net_cash") or 0)),
    )
    finance_cols[2].metric(
        "최대 대출 한도",
        _format_unlimited_money(loan_ltv.get("max_loan_amount")),
    )
    finance_cols[3].metric(
        "최종 예상 대출",
        _format_optional_money(result.get("expected_loan_amount")),
    )
