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
    st.title("분석 결과")
    st.caption("저장된 실거래 데이터를 기준으로 실거주 관점과 투자 관점을 각각 비교할 수 있습니다.")

    listings = listing_repository.list_all()
    profiles = finance_repository.list_all()

    if not listings:
        st.info("먼저 매물을 1개 이상 등록해 주세요.")
        return
    if not profiles:
        st.info("먼저 자금 프로필을 1개 이상 등록해 주세요.")
        return

    listing_options = {
        f"#{item['id']} | {item['complex_name']} | {format_compact_won(item['sale_price'])}": item
        for item in listings
    }
    profile_options = {
        f"#{item['id']} | 보유 현금 {format_compact_won(item['cash_amount'])} | LTV {item['ltv_limit'] or settings.default_ltv_limit:.0%}": item
        for item in profiles
    }

    selected_listing_label = st.selectbox("매물 선택", list(listing_options.keys()))
    selected_profile_label = st.selectbox("자금 프로필 선택", list(profile_options.keys()))
    selected_listing = listing_options[selected_listing_label]
    selected_profile = profile_options[selected_profile_label]

    default_analysis_mode = _to_primary_mode(selected_listing.get("effective_investment_type"))
    selected_analysis_mode = st.radio(
        "분석 관점",
        list(PRIMARY_MODE_LABELS.keys()),
        index=list(PRIMARY_MODE_LABELS.keys()).index(default_analysis_mode),
        format_func=lambda value: PRIMARY_MODE_LABELS[value],
        horizontal=True,
        help="같은 매물을 실거주 기준과 투자 기준으로 번갈아 비교할 수 있습니다.",
    )
    st.info(f"현재 분석 관점: {PRIMARY_MODE_LABELS[selected_analysis_mode]}")

    try:
        transaction_context = analysis_service.get_transaction_context(
            listing_id=selected_listing["id"]
        )
        _render_transaction_summary(transaction_context)
        _render_transaction_history(transaction_context)
    except ValueError as exc:
        st.warning(str(exc))

    with st.form("analysis_form"):
        col1, col2 = st.columns(2)
        with col1:
            recent_avg_price_override_eok = st.number_input(
                "최근 평균가 수동 보정 (억원, 0이면 자동)",
                min_value=0.0,
                step=0.1,
                value=0.0,
                format="%.2f",
            )
            one_year_high_price_override_eok = st.number_input(
                "최근 1년 최고가 수동 보정 (억원, 0이면 자동)",
                min_value=0.0,
                step=0.1,
                value=0.0,
                format="%.2f",
            )
        with col2:
            ltv_rate_override = st.number_input(
                "LTV 수동 보정 (0이면 규칙 적용)",
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                value=0.0,
                format="%.2f",
            )
            expected_loan_amount_eok = st.number_input(
                "예상 대출금 (억원, 0이면 자동 계산)",
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
            if selected_analysis_mode == "INVESTMENT":
                expected_jeonse_price_override_eok = st.number_input(
                    "예상 전세가 수동 보정 (억원, 0이면 자동)",
                    min_value=0.0,
                    step=0.1,
                    value=0.0,
                    format="%.2f",
                )
            else:
                expected_jeonse_price_override_eok = 0.0

        save_result = st.checkbox("분석 결과 저장", value=True)
        submitted = st.form_submit_button("분석 실행")

    if submitted:
        try:
            result = analysis_service.run_analysis(
                listing_id=selected_listing["id"],
                finance_profile_id=selected_profile["id"],
                benchmarks=BenchmarkInputs(
                    repair_cost=int(from_eok(repair_cost_eok)),
                    expected_loan_amount=int(from_eok(expected_loan_amount_eok)) or None,
                    ltv_rate_override=float(ltv_rate_override) or None,
                    recent_avg_price_override=int(from_eok(recent_avg_price_override_eok)) or None,
                    one_year_high_price_override=int(from_eok(one_year_high_price_override_eok)) or None,
                    expected_jeonse_price_override=int(from_eok(expected_jeonse_price_override_eok)) or None,
                    analysis_mode=selected_analysis_mode,
                ),
                save_result=save_result,
            )
            _render_analysis_metrics(result, settings)
        except ValueError as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("최근 분석 이력")
    recent_results = analysis_repository.list_recent()
    if not recent_results:
        st.caption("저장된 분석 결과가 없습니다.")
        return

    history_df = pd.DataFrame(recent_results)
    history_view_df = history_df[
        [
            "id",
            "complex_name",
            "sale_price",
            "required_cash",
            "shortage_cash",
            "jeonse_ratio",
            "bargain_score",
            "decision",
            "created_at",
        ]
    ].rename(
        columns={
            "id": "ID",
            "complex_name": "단지명",
            "sale_price": "매매가",
            "required_cash": "총 필요 자기자본",
            "shortage_cash": "추가 필요 현금",
            "jeonse_ratio": "전세가율",
            "bargain_score": "급매 점수",
            "decision": "판단",
            "created_at": "분석일시",
        }
    )
    for column in ["매매가", "총 필요 자기자본", "추가 필요 현금"]:
        history_view_df[column] = history_view_df[column].map(format_compact_won)
    st.dataframe(history_view_df, use_container_width=True)

    chart = px.bar(
        history_df.head(10),
        x="complex_name",
        y="bargain_score",
        color="decision",
        title="최근 급매 점수",
    )
    st.plotly_chart(chart, use_container_width=True)


def _render_analysis_metrics(result: dict, settings: AppSettings) -> None:
    st.subheader(f"{result['complex_name']} 분석 결과")
    st.info(result["scenario_explanation"])

    if result["primary_user_mode"] == "OWNER_OCCUPIED":
        _render_owner_metrics(result)
    else:
        _render_investment_metrics(result)

    st.success(result["decision"])
    _render_result_interpretation(result)
    _render_source_table(result)
    _render_formula_explainer(result)
    st.text_area("요약", value=result["summary"], height=180, disabled=True)
    _render_cost_table(result, settings)

    if result["reasons"]:
        st.write("점수 반영 사유")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

    if result["risks"]:
        st.write("체크할 리스크")
        for risk in result["risks"]:
            st.write(f"- {risk}")

    _render_interpretation_guide(result["primary_user_mode"])


def _render_owner_metrics(result: dict) -> None:
    top_cols = st.columns(4)
    top_cols[0].metric(
        "총 필요 자기자본",
        format_compact_won(result["required_cash"]),
        help="매매가에서 대출금을 빼고 취득세, 중개보수 등 부대비용을 더한 금액입니다.",
    )
    top_cols[1].metric(
        "추가 필요 현금",
        format_compact_won(result["shortage_cash"]),
        help="총 필요 자기자본에서 현재 보유 현금을 뺀 값입니다.",
    )
    top_cols[2].metric(
        "예상 월 상환액",
        _format_optional_money(result["monthly_repayment"]),
        help="등록된 금리 정보가 있으면 30년 원리금균등 상환 기준으로 추정합니다.",
    )
    top_cols[3].metric(
        "예상 DSR",
        _format_optional_percent(result["dsr"]),
        help="연 소득 정보가 있을 때 연간 원리금 상환액을 기준으로 계산합니다.",
    )

    detail_cols = st.columns(4)
    detail_cols[0].metric(
        "매수 후 남는 현금",
        format_compact_won(result["remaining_cash_after_purchase"]),
        help="보유 현금에서 총 필요 자기자본을 뺀 값입니다.",
    )
    detail_cols[1].metric(
        "예상 대출금",
        format_compact_won(result["expected_loan_amount"]),
        help="규칙 기반 계산값 또는 수동 보정값입니다.",
    )
    _render_signed_rate_metric(
        detail_cols[2],
        label="평균 대비 변동률",
        value=result["recent_avg_change_rate"],
        help_text="최근 평균 실거래가 대비 현재 매물가가 얼마나 높은지 또는 낮은지 보여줍니다.",
    )
    detail_cols[3].metric(
        "급매 점수",
        f"{result['bargain_score']}점 ({result['bargain_grade']})",
        help="실거주에서도 시세 대비 가격 매력을 참고할 수 있도록 보조 지표로 보여줍니다.",
    )

    support_cols = st.columns(2)
    _render_signed_rate_metric(
        support_cols[0],
        label="고점 대비 변동률",
        value=result["high_price_change_rate"],
        help_text="최근 1년 최고 실거래가 대비 현재 매물가가 얼마나 높은지 또는 낮은지 보여줍니다.",
    )
    support_cols[1].metric(
        "전세가율",
        f"{result['jeonse_ratio']:.1f}%",
        help="실거주 판단의 핵심 지표는 아니지만, 시장 가격대를 가늠하는 참고값으로 볼 수 있습니다.",
    )


def _render_investment_metrics(result: dict) -> None:
    top_cols = st.columns(4)
    top_cols[0].metric(
        "갭 금액",
        format_compact_won(result["gap_amount"]),
        help="매매가에서 전세 보증금을 뺀 기본 갭 규모입니다.",
    )
    top_cols[1].metric(
        "전세가율",
        f"{result['jeonse_ratio']:.1f}%",
        help="예상 전세가를 매매가로 나눈 비율입니다.",
    )
    top_cols[2].metric(
        "총 필요 자기자본",
        format_compact_won(result["required_cash"]),
        help="대출, 전세금, 부대비용까지 반영한 실제 투입 자기자본입니다.",
    )
    top_cols[3].metric(
        "급매 점수",
        f"{result['bargain_score']}점 ({result['bargain_grade']})",
        help="평균 대비 변동률, 고점 기준 변동률, 전세가율, 자금 가능 여부를 반영합니다.",
    )

    detail_cols = st.columns(4)
    detail_cols[0].metric(
        "투자 효율",
        _format_efficiency(result["estimated_investment_efficiency"]),
        help="투입 자기자본 대비 확보 자산 배수입니다.",
    )
    detail_cols[1].metric(
        "예상 대출금",
        format_compact_won(result["expected_loan_amount"]),
        help="규칙 기반 계산값 또는 수동 보정값입니다.",
    )
    _render_signed_rate_metric(
        detail_cols[2],
        label="평균 대비 변동률",
        value=result["recent_avg_change_rate"],
        help_text="최근 평균 실거래가 대비 현재 매물가가 얼마나 높은지 또는 낮은지 보여줍니다.",
    )
    _render_signed_rate_metric(
        detail_cols[3],
        label="고점 대비 변동률",
        value=result["high_price_change_rate"],
        help_text="최근 1년 최고 실거래가 대비 현재 매물가가 얼마나 높은지 또는 낮은지 보여줍니다.",
    )

    if result["monthly_cash_flow"] is not None:
        st.metric("월세 현금흐름", format_compact_won(result["monthly_cash_flow"]))


def _render_source_table(result: dict) -> None:
    st.write("자동 계산 / 수동 보정 기준")
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
            "항목": "대출 규칙 버전",
            "적용값": result["loan_rule_version"],
            "출처": result["loan_terms"]["ltv_source"],
        },
    ]
    if result["primary_user_mode"] == "INVESTMENT":
        rows.insert(
            2,
            {
                "항목": "예상 전세가",
                "적용값": format_compact_won(result["expected_jeonse_price"]),
                "출처": result["sources"]["expected_jeonse_price"],
            },
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_formula_explainer(result: dict) -> None:
    cost_total = sum(result["costs"].values())
    own_cash = result["required_cash"] - result["shortage_cash"]

    with st.expander("계산식 자세히 보기"):
        lines = _build_mode_formula_lines(result, cost_total=cost_total, own_cash=own_cash)
        st.markdown("\n".join(lines))


def _build_mode_formula_lines(result: dict, *, cost_total: int, own_cash: int) -> list[str]:
    lines = [
        "기본 계산",
        f"- 매매가: {format_won(result['sale_price'])}",
        f"- 예상 대출금: {format_won(result['expected_loan_amount'])}",
        f"- 부대비용 합계: {format_won(cost_total)}",
        "",
    ]

    if result["primary_user_mode"] == "OWNER_OCCUPIED":
        lines.extend(
            [
                "실거주 계산식",
                "- 총 필요 자기자본 = 매매가 - 예상 대출금 + 부대비용 합계",
                f"- 실제 계산: {format_won(result['sale_price'])} - {format_won(result['expected_loan_amount'])} + {format_won(cost_total)} = {format_won(result['required_cash'])}",
                "",
                "추가 필요 현금",
                "- 추가 필요 현금 = 총 필요 자기자본 - 보유 현금",
                f"- 실제 계산: {format_won(result['required_cash'])} - {format_won(own_cash)} = {format_won(result['shortage_cash'])}",
                "",
                "매수 후 남는 현금",
                "- 매수 후 남는 현금 = 보유 현금 - 총 필요 자기자본",
                f"- 실제 계산: {format_won(own_cash)} - {format_won(result['required_cash'])} = {format_won(result['remaining_cash_after_purchase'])}",
                "",
                "고점 대비 변동률",
                "- 변동률 = (매매가 - 최근 1년 최고가) / 최근 1년 최고가 x 100",
                f"- 실제 계산: ({format_won(result['sale_price'])} - {format_won(result['derived_inputs']['one_year_high_price'])}) / {format_won(result['derived_inputs']['one_year_high_price'])} x 100 = {result['high_price_change_rate']:+.1f}%",
            ]
        )
        if result["monthly_repayment"] is not None:
            lines.extend(
                [
                    "",
                    "월 상환액",
                    "- 등록된 금리 정보 기준 30년 원리금균등 상환으로 추정",
                    f"- 추정 결과: {format_won(result['monthly_repayment'])}",
                ]
            )
        if result["dsr"] is not None:
            lines.extend(
                [
                    "",
                    "DSR",
                    "- DSR = 연간 원리금 상환액 / 연소득 x 100",
                    f"- 추정 결과: {result['dsr']:.1f}%",
                ]
            )
        return lines

    lines.extend(
        [
            "투자 계산식",
            "- 총 필요 자기자본 = 매매가 - 예상 대출금 - 예상 전세가 + 부대비용 합계",
            f"- 실제 계산: {format_won(result['sale_price'])} - {format_won(result['expected_loan_amount'])} - {format_won(result['expected_jeonse_price'])} + {format_won(cost_total)} = {format_won(result['required_cash'])}",
            "",
            "갭 금액",
            "- 갭 금액 = 매매가 - 예상 전세가",
            f"- 실제 계산: {format_won(result['sale_price'])} - {format_won(result['expected_jeonse_price'])} = {format_won(result['gap_amount'])}",
            "",
            "전세가율",
            "- 전세가율 = 예상 전세가 / 매매가 x 100",
            f"- 실제 계산: {format_won(result['expected_jeonse_price'])} / {format_won(result['sale_price'])} x 100 = {result['jeonse_ratio']:.1f}%",
            "",
            "투자 효율",
            "- 투자 효율 = 매매가 / 총 필요 자기자본",
            f"- 실제 계산: {format_won(result['sale_price'])} / {format_won(result['required_cash'])} = {_format_efficiency(result['estimated_investment_efficiency'])}",
            "",
            "평균 대비 변동률",
            "- 변동률 = (매매가 - 최근 평균가) / 최근 평균가 x 100",
            f"- 실제 계산: ({format_won(result['sale_price'])} - {format_won(result['derived_inputs']['recent_avg_price'])}) / {format_won(result['derived_inputs']['recent_avg_price'])} x 100 = {result['recent_avg_change_rate']:+.1f}%",
            "",
            "고점 대비 변동률",
            "- 변동률 = (매매가 - 최근 1년 최고가) / 최근 1년 최고가 x 100",
            f"- 실제 계산: ({format_won(result['sale_price'])} - {format_won(result['derived_inputs']['one_year_high_price'])}) / {format_won(result['derived_inputs']['one_year_high_price'])} x 100 = {result['high_price_change_rate']:+.1f}%",
        ]
    )
    if result["monthly_cash_flow"] is not None:
        lines.extend(
            [
                "",
                "월세 현금흐름",
                f"- 추정 결과: {format_won(result['monthly_cash_flow'])}",
            ]
        )
    lines.extend(
        [
            "",
            "대출 규칙",
            f"- 규칙 버전: {result['loan_rule_version']}",
            f"- 규칙 설명: {result['loan_terms']['rule_description']}",
            f"- 적용 LTV: {result['loan_terms']['applied_ltv_rate']:.0%}",
            f"- 적용 DSR: {result['loan_terms']['applied_dsr_rate']:.0%}",
        ]
    )
    return lines


def _render_cost_table(result: dict, settings: AppSettings) -> None:
    cost_total = sum(result["costs"].values())
    st.write("부대비용 구성")
    st.metric("부대비용 합계", format_compact_won(cost_total))
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "항목": "취득세",
                    "계산 기준": f"매매가 x {settings.acquisition_tax_rate:.2%}",
                    "금액": format_compact_won(result["costs"]["acquisition_tax"]),
                },
                {
                    "항목": "중개보수",
                    "계산 기준": f"매매가 x {settings.brokerage_fee_rate:.2%}",
                    "금액": format_compact_won(result["costs"]["brokerage_fee"]),
                },
                {
                    "항목": "법무비",
                    "계산 기준": "고정값",
                    "금액": format_compact_won(result["costs"]["legal_fee"]),
                },
                {
                    "항목": "수리비",
                    "계산 기준": "사용자 입력값",
                    "금액": format_compact_won(result["costs"]["repair_cost"]),
                },
                {
                    "항목": "예비비",
                    "계산 기준": f"매매가 x {settings.contingency_rate:.2%}",
                    "금액": format_compact_won(result["costs"]["contingency_fee"]),
                },
                {"항목": "합계", "계산 기준": "-", "금액": format_compact_won(cost_total)},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_result_interpretation(result: dict) -> None:
    if result["primary_user_mode"] == "OWNER_OCCUPIED":
        if result["shortage_cash"] <= 0:
            st.success("자금 여력 해석: 현재 보유 현금 기준으로 실거주 매수 진행이 가능한 수준입니다.")
        else:
            st.warning("자금 여력 해석: 실거주 매수 전 추가 현금 확보가 필요합니다.")

        if result["dsr"] is None:
            st.info("상환 부담 해석: 금리 또는 연소득 정보가 없어 월 상환 부담과 DSR은 계산하지 못했습니다.")
        elif result["dsr"] > result["loan_terms"]["applied_dsr_rate"] * 100:
            st.warning("상환 부담 해석: 현재 추정 DSR이 적용 규칙 수준보다 높아 상환 부담이 큰 편입니다.")
        else:
            st.success("상환 부담 해석: 현재 추정 DSR은 무난한 편입니다.")

        if result["bargain_score"] >= 65:
            st.info("가격 참고 지표: 자금 여력이 맞는다면 가격 매력도도 함께 검토할 만한 수준입니다.")
        else:
            st.info("가격 참고 지표: 실거주 판단이 우선이지만, 가격 매력은 보통 이하로 볼 수 있습니다.")
        return

    if result["jeonse_ratio"] >= 70:
        st.info("갭 효율 해석: 전세가율이 높아 초기 자기자본 부담은 낮지만 전세 리스크 점검이 필요합니다.")
    elif result["jeonse_ratio"] >= 60:
        st.success("갭 효율 해석: 전세가율이 보통 이상으로 투자 구조가 비교적 안정적입니다.")
    else:
        st.warning("갭 효율 해석: 전세가율이 낮아 직접 투입해야 하는 자금 부담이 큽니다.")

    if result["bargain_score"] >= 80:
        st.success("급매 해석: 강한 급매 후보로 볼 수 있습니다.")
    elif result["bargain_score"] >= 65:
        st.info("급매 해석: 검토 가치가 있는 매물입니다.")
    else:
        st.warning("급매 해석: 현재 기준으로는 급매 매력도가 높지 않습니다.")


def _render_interpretation_guide(primary_user_mode: str) -> None:
    st.subheader("지표 해석 가이드")

    if primary_user_mode == "OWNER_OCCUPIED":
        owner_guide_df = pd.DataFrame(
            [
                {"항목": "추가 필요 현금", "해석": "0 이하이면 현재 보유 현금만으로도 매수 가능성이 있습니다."},
                {"항목": "예상 DSR", "해석": "낮을수록 월 상환 부담이 적습니다."},
                {"항목": "매수 후 남는 현금", "해석": "매수 후에도 남는 현금이 있어야 생활 여유가 커집니다."},
                {"항목": "급매 점수", "해석": "실거주에서도 가격 매력을 참고하는 보조 지표로 볼 수 있습니다."},
                {"항목": "고점 대비 변동률", "해석": "+면 최근 최고 실거래가보다 비싸고, -면 더 낮다는 뜻입니다."},
            ]
        )
        st.dataframe(owner_guide_df, use_container_width=True, hide_index=True)
        return

    jeonse_guide_df = pd.DataFrame(
        [
            {"전세가율 구간": "70% 이상", "해석": "자기자본 부담은 낮지만 전세 리스크 확인이 필요합니다."},
            {"전세가율 구간": "60% ~ 70%", "해석": "보통 이상 수준으로 볼 수 있습니다."},
            {"전세가율 구간": "50% ~ 60%", "해석": "직접 투입 자금 부담이 커질 수 있습니다."},
            {"전세가율 구간": "50% 미만", "해석": "갭투자 관점에서는 매력이 낮을 수 있습니다."},
        ]
    )
    bargain_guide_df = pd.DataFrame(
        [
            {"급매 점수 구간": "80점 이상", "해석": "강한 급매 후보입니다."},
            {"급매 점수 구간": "65점 ~ 79점", "해석": "검토 가치가 있는 매물입니다."},
            {"급매 점수 구간": "50점 ~ 64점", "해석": "보통 수준입니다."},
            {"급매 점수 구간": "50점 미만", "해석": "급매 가능성이 낮습니다."},
        ]
    )
    col1, col2 = st.columns(2)
    with col1:
        st.write("전세가율 해석")
        st.dataframe(jeonse_guide_df, use_container_width=True, hide_index=True)
    with col2:
        st.write("급매 점수 해석")
        st.dataframe(bargain_guide_df, use_container_width=True, hide_index=True)


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
            .rename(columns={"price": "금액"})
            .assign(구분="매매")
        )
    if not rent_history.empty:
        chart_frames.append(
            rent_history[["deal_date", "deposit"]]
            .rename(columns={"deposit": "금액"})
            .assign(구분="전세")
        )

    if chart_frames:
        chart_df = pd.concat(chart_frames, ignore_index=True)
        chart_df["금액_억원"] = chart_df["금액"].map(to_eok)
        chart = px.line(
            chart_df,
            x="deal_date",
            y="금액_억원",
            color="구분",
            markers=True,
            title="최근 12개월 가격 추이",
            hover_data={"금액": True, "금액_억원": False},
        )
        chart.update_traces(
            hovertemplate="거래일=%{x}<br>구분=%{fullData.name}<br>금액=%{customdata[0]:,}원<extra></extra>"
        )
        chart.update_layout(yaxis_title="금액 (억원)", xaxis_title="거래일")
        st.plotly_chart(chart, use_container_width=True)

    sale_tab, rent_tab = st.tabs(["매매 이력", "전세 이력"])
    with sale_tab:
        if sale_history.empty:
            st.caption("매매 거래 데이터가 없습니다.")
        else:
            st.dataframe(
                sale_history[["deal_date", "area_m2", "price", "floor"]]
                .sort_values("deal_date", ascending=False)
                .assign(price=lambda df: df["price"].map(to_eok))
                .rename(
                    columns={
                        "deal_date": "거래일",
                        "area_m2": "면적(m²)",
                        "price": "거래가(억원)",
                        "floor": "층",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
    with rent_tab:
        if rent_history.empty:
            st.caption("전세 거래 데이터가 없습니다.")
        else:
            st.dataframe(
                rent_history[["deal_date", "area_m2", "deposit", "floor"]]
                .sort_values("deal_date", ascending=False)
                .assign(deposit=lambda df: df["deposit"].map(to_eok))
                .rename(
                    columns={
                        "deal_date": "거래일",
                        "area_m2": "면적(m²)",
                        "deposit": "보증금(억원)",
                        "floor": "층",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )


def _to_primary_mode(investment_type: str | None) -> str:
    return "OWNER_OCCUPIED" if investment_type == "OWNER_OCCUPIED" else "INVESTMENT"


def _format_optional_money(value: int | None) -> str:
    if value is None:
        return "입력 필요"
    return format_compact_won(value)


def _format_optional_percent(value: float | None) -> str:
    if value is None:
        return "입력 필요"
    return f"{value:.1f}%"


def _format_efficiency(value: float | None) -> str:
    if value is None:
        return "계산 불가"
    return f"{value:.2f}배"


def _render_signed_rate_metric(container, *, label: str, value: float, help_text: str) -> None:
    color = "#d92d20" if value > 0 else "#1570ef" if value < 0 else "#667085"
    status_text = "기준보다 높음" if value > 0 else "기준보다 낮음" if value < 0 else "기준과 동일"
    container.markdown(f"{label}  \n<small>{help_text}</small>", unsafe_allow_html=True)
    container.markdown(
        f"<div style='font-size:1.6rem;font-weight:700;color:{color};'>{value:+.1f}%</div>",
        unsafe_allow_html=True,
    )
    container.caption(status_text)
