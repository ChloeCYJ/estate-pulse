from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import AppSettings
from modules.services.analysis_service import AnalysisService, BenchmarkInputs
from modules.utils.money_utils import format_compact_won, format_won, from_eok, to_eok

PRIMARY_MODE_LABELS = {
    "OWNER_OCCUPIED": "실거주",
    "INVESTMENT": "투자",
}


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
        st.subheader("시장 입력 보정")
        market_col1, market_col2 = st.columns(2)
        with market_col1:
            recent_avg_price_override_eok = st.number_input(
                "최근 평균가 override (억 원)",
                min_value=0.0,
                step=0.1,
                value=0.0,
                format="%.2f",
            )
            one_year_high_price_override_eok = st.number_input(
                "최근 1년 최고가 override (억 원)",
                min_value=0.0,
                step=0.1,
                value=0.0,
                format="%.2f",
            )
        with market_col2:
            expected_loan_amount_eok = st.number_input(
                "예상 대출 override (억 원)",
                min_value=0.0,
                step=0.1,
                value=0.0,
                format="%.2f",
            )
            ltv_rate_override = st.number_input(
                "LTV override",
                min_value=0.0,
                max_value=1.0,
                step=0.05,
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
            expected_jeonse_price_override_eok = 0.0
            if selected_mode == "INVESTMENT":
                expected_jeonse_price_override_eok = st.number_input(
                    "예상 전세가 override (억 원)",
                    min_value=0.0,
                    step=0.1,
                    value=0.0,
                    format="%.2f",
                )

        st.subheader("거래비용 수동 override")
        cost_col1, cost_col2, cost_col3 = st.columns(3)
        with cost_col1:
            acquisition_tax_override_eok = st.number_input(
                "취득세 override (억 원)",
                min_value=0.0,
                step=0.01,
                value=0.0,
                format="%.2f",
            )
            local_education_tax_override_eok = st.number_input(
                "지방교육세 override (억 원)",
                min_value=0.0,
                step=0.01,
                value=0.0,
                format="%.2f",
            )
        with cost_col2:
            brokerage_fee_override_eok = st.number_input(
                "중개보수 override (억 원)",
                min_value=0.0,
                step=0.01,
                value=0.0,
                format="%.2f",
            )
            legal_fee_override_eok = st.number_input(
                "법무비 override (억 원)",
                min_value=0.0,
                step=0.01,
                value=0.0,
                format="%.2f",
            )
        with cost_col3:
            reserve_cost_override_eok = st.number_input(
                "예비비 override (억 원)",
                min_value=0.0,
                step=0.01,
                value=0.0,
                format="%.2f",
            )
            save_result = st.checkbox("분석 결과 저장", value=True)

        submitted = st.form_submit_button("분석 실행")

    if submitted:
        try:
            result = analysis_service.run_analysis(
                listing_id=selected_listing["id"],
                finance_profile_id=selected_profile["id"],
                benchmarks=BenchmarkInputs(
                    repair_cost=int(from_eok(repair_cost_eok)),
                    expected_loan_amount=_to_optional_won(expected_loan_amount_eok),
                    ltv_rate_override=_to_optional_float(ltv_rate_override),
                    recent_avg_price_override=_to_optional_won(recent_avg_price_override_eok),
                    one_year_high_price_override=_to_optional_won(one_year_high_price_override_eok),
                    expected_jeonse_price_override=_to_optional_won(expected_jeonse_price_override_eok),
                    analysis_mode=selected_mode,
                    acquisition_tax_override=_to_optional_won(acquisition_tax_override_eok),
                    local_education_tax_override=_to_optional_won(local_education_tax_override_eok),
                    brokerage_fee_override=_to_optional_won(brokerage_fee_override_eok),
                    legal_fee_override=_to_optional_won(legal_fee_override_eok),
                    reserve_cost_override=_to_optional_won(reserve_cost_override_eok),
                ),
                save_result=save_result,
            )
            _render_analysis_metrics(result)
        except ValueError as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("최근 분석 이력")
    recent_results = analysis_repository.list_recent()
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
            "required_cash": "필요 현금",
            "shortage_cash": "부족 현금",
            "bargain_score": "급매 점수",
            "liquidity_score": "유동성 점수",
            "investment_score": "투자 점수",
            "complex_grade": "단지 등급",
            "created_at": "분석일",
        }
    )
    for column in ["매물가", "필요 현금", "부족 현금"]:
        history_df[column] = history_df[column].map(format_compact_won)
    history_df["단지 등급"] = history_df["단지 등급"].map(_complex_grade_label)
    st.dataframe(history_df, use_container_width=True, hide_index=True)

    chart = px.bar(
        pd.DataFrame(recent_results).head(10),
        x="complex_name",
        y="investment_score",
        color="complex_grade",
        title="최근 투자 점수",
    )
    st.plotly_chart(chart, use_container_width=True)


def _render_analysis_metrics(result: dict) -> None:
    st.subheader(f"{result['complex_name']} 분석 결과")
    st.info(result["scenario_explanation"])

    top_cols = st.columns(4)
    top_cols[0].metric("필요 현금", format_compact_won(result["required_cash"]))
    top_cols[1].metric("부족 현금", format_compact_won(result["shortage_cash"]))
    top_cols[2].metric("유동성 점수", str(result["liquidity_score"]))
    top_cols[3].metric("투자 점수", str(result["investment_score"]))

    detail_cols = st.columns(4)
    detail_cols[0].metric("급매 점수", f"{result['bargain_score']} ({result['bargain_grade']})")
    detail_cols[1].metric("전세가율", f"{result['jeonse_ratio']:.1f}%")
    detail_cols[2].metric("단지 등급", result["complex_grade_label"])
    detail_cols[3].metric("예상 대출", format_compact_won(result["expected_loan_amount"]))

    if result["primary_user_mode"] == "INVESTMENT":
        extra_cols = st.columns(3)
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
        extra_cols = st.columns(3)
        extra_cols[0].metric("월 상환액", _format_optional_money(result["monthly_repayment"]))
        extra_cols[1].metric("DSR", _format_optional_percent(result["dsr"]))
        extra_cols[2].metric(
            "매수 후 잔여 현금",
            format_compact_won(result["remaining_cash_after_purchase"]),
        )

    st.success(result["decision"])
    _render_source_table(result)
    _render_cost_table(result)
    _render_complex_profile_table(result)
    _render_formula_explainer(result)
    st.text_area("요약", value=result["summary"], height=180, disabled=True)

    if result["reasons"]:
        st.write("점수 반영 사유")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

    if result["risks"]:
        st.write("리스크 체크")
        for risk in result["risks"]:
            st.write(f"- {risk}")


def _render_source_table(result: dict) -> None:
    rows = [
        {
            "항목": "최근 평균가",
            "적용값": format_compact_won(result["derived_inputs"]["recent_avg_price"]),
            "출처": result["sources"]["recent_avg_price"],
        },
        {
            "항목": "최근 1년 최고가",
            "적용값": format_compact_won(result["derived_inputs"]["one_year_high_price"]),
            "출처": result["sources"]["one_year_high_price"],
        },
        {
            "항목": "예상 전세가",
            "적용값": format_compact_won(result["expected_jeonse_price"]),
            "출처": result["sources"]["expected_jeonse_price"],
        },
        {
            "항목": "세금 규칙",
            "적용값": result["applied_tax_rule_version"],
            "출처": "config/tax_rules.py",
        },
        {
            "항목": "중개/비용 규칙",
            "적용값": result["applied_brokerage_rule_version"],
            "출처": "config/brokerage_rules.py",
        },
        {
            "항목": "대출 규칙",
            "적용값": result["loan_rule_version"],
            "출처": result["loan_terms"]["ltv_source"],
        },
        {
            "항목": "대출 지역 판정",
            "적용값": result["resolved_region_type"],
            "출처": result["region_policy_source"],
        },
    ]
    st.write("계산 기준")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


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
    st.write("거래비용")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_complex_profile_table(result: dict) -> None:
    profile = result["complex_profile"]
    rows = [
        {"항목": "단지 등급", "값": result["complex_grade_label"]},
        {"항목": "유동성 점수", "값": profile["liquidity_score"]},
        {"항목": "유동성 해석", "값": profile["liquidity_label"]},
        {"항목": "최근 매매 거래 수", "값": profile["recent_sale_transaction_count"]},
        {"항목": "최근 전세 거래 수", "값": profile["recent_rent_transaction_count"]},
        {"항목": "거래 빈도", "값": profile["transaction_frequency"]},
        {"항목": "지역 평균가 순위", "값": profile["average_sale_price_rank"]},
        {"항목": "평당가 순위", "값": profile["price_per_area_rank"]},
    ]
    st.write("단지 품질 분석")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_formula_explainer(result: dict) -> None:
    with st.expander("계산식 보기"):
        lines = [
            f"- 매물가: {format_won(result['sale_price'])}",
            f"- 예상 대출: {format_won(result['expected_loan_amount'])}",
            f"- 총 거래비용: {format_won(result['costs']['total_transaction_cost'])}",
        ]
        if result["primary_user_mode"] == "INVESTMENT":
            lines.extend(
                [
                    f"- 예상 전세가: {format_won(result['expected_jeonse_price'])}",
                    "- 필요 현금 = 매물가 - 예상 대출 - 예상 전세가 + 총 거래비용 + 수리비",
                    (
                        f"- 계산 결과: {format_won(result['required_cash'])} / "
                        f"부족 현금 {format_won(result['shortage_cash'])}"
                    ),
                ]
            )
        else:
            lines.extend(
                [
                    "- 필요 현금 = 매물가 - 예상 대출 + 총 거래비용 + 수리비",
                    (
                        f"- 계산 결과: {format_won(result['required_cash'])} / "
                        f"부족 현금 {format_won(result['shortage_cash'])}"
                    ),
                ]
            )
        lines.extend(
            [
                f"- 급매 점수: {result['bargain_score']}",
                f"- 유동성 점수: {result['liquidity_score']}",
                f"- 단지 등급: {result['complex_grade_label']}",
                f"- 투자 점수: {result['investment_score']}",
            ]
        )
        st.markdown("\n".join(lines))


def _render_transaction_summary(transaction_context: dict) -> None:
    st.subheader("거래 요약")
    metrics = transaction_context["market_metrics"]

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
            st.dataframe(sale_df.sort_values("거래일", ascending=False), use_container_width=True, hide_index=True)
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
            st.dataframe(rent_df.sort_values("거래일", ascending=False), use_container_width=True, hide_index=True)


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
    if value is None:
        return "정보 없음"
    return format_compact_won(value)


def _format_optional_percent(value: float | None) -> str:
    if value is None:
        return "정보 없음"
    return f"{value:.1f}%"


def _format_efficiency(value: float | None) -> str:
    if value is None:
        return "계산 불가"
    return f"{value:.2f}배"


def _complex_grade_label(value: str | None) -> str:
    labels = {
        "LEADER": "대장",
        "SUB_LEADER": "준대장",
        "NORMAL": "일반",
        "SMALL": "나홀로",
        "RISKY": "유동성주의",
    }
    return labels.get(value or "", value or "-")
