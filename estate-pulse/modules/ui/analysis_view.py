from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import AppSettings
from modules.services.analysis_service import AnalysisService, BenchmarkInputs
from modules.utils.money_utils import format_compact_won, format_won, from_eok, to_eok


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
    st.caption("저장된 매매/전세 거래 데이터를 기준으로 자동 분석하고, 필요하면 수동 보정할 수 있습니다.")

    listings = listing_repository.list_all()
    profiles = finance_repository.list_all()

    if not listings:
        st.info("먼저 매물을 1개 이상 등록해 주세요.")
        return
    if not profiles:
        st.info("먼저 자금 프로필을 1개 이상 등록해 주세요.")
        return

    listing_options = {
        f"#{item['id']} | {item['complex_name']} | {format_compact_won(item['sale_price'])}": item["id"]
        for item in listings
    }
    profile_options = {
        f"#{item['id']} | 보유 현금 {format_compact_won(item['cash_amount'])} | LTV {item['ltv_limit'] or settings.default_ltv_limit:.0%}": item["id"]
        for item in profiles
    }

    selected_listing_label = st.selectbox("매물 선택", list(listing_options.keys()))
    selected_profile_label = st.selectbox("자금 프로필 선택", list(profile_options.keys()))

    transaction_context: dict | None = None
    try:
        transaction_context = analysis_service.get_transaction_context(
            listing_id=listing_options[selected_listing_label]
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
            expected_jeonse_price_override_eok = st.number_input(
                "예상 전세가 수동 보정 (억원, 0이면 자동)",
                min_value=0.0,
                step=0.1,
                value=0.0,
                format="%.2f",
            )
            expected_loan_amount_eok = st.number_input(
                "예상 대출금 (억원, 0이면 LTV로 자동 계산)",
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

        save_result = st.checkbox("분석 결과 저장", value=True)
        submitted = st.form_submit_button("분석 실행")

    if submitted:
        try:
            repair_cost = from_eok(repair_cost_eok)
            expected_loan_amount = from_eok(expected_loan_amount_eok)
            recent_avg_price_override = from_eok(recent_avg_price_override_eok)
            one_year_high_price_override = from_eok(one_year_high_price_override_eok)
            expected_jeonse_price_override = from_eok(expected_jeonse_price_override_eok)
            result = analysis_service.run_analysis(
                listing_id=listing_options[selected_listing_label],
                finance_profile_id=profile_options[selected_profile_label],
                benchmarks=BenchmarkInputs(
                    repair_cost=int(repair_cost),
                    expected_loan_amount=int(expected_loan_amount) or None,
                    recent_avg_price_override=int(recent_avg_price_override) or None,
                    one_year_high_price_override=int(one_year_high_price_override) or None,
                    expected_jeonse_price_override=int(expected_jeonse_price_override) or None,
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
            "sale_price": "매물가",
            "required_cash": "총 필요 자기자본",
            "shortage_cash": "추가 필요 현금",
            "jeonse_ratio": "전세가율",
            "bargain_score": "급매 점수",
            "decision": "판정",
            "created_at": "분석일시",
        }
    )
    for column in ["매물가", "총 필요 자기자본", "추가 필요 현금"]:
        history_view_df[column] = history_view_df[column].map(format_compact_won)
    st.dataframe(
        history_view_df,
        use_container_width=True,
    )

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
    cost_total = sum(result["costs"].values())
    own_cash = result["required_cash"] - result["shortage_cash"]

    top_cols = st.columns(4)
    top_cols[0].metric(
        "총 필요 자기자본",
        format_compact_won(result["required_cash"]),
        help="매물가에서 대출금과 전세금을 빼고, 취득세/중개보수/법무비/수리비/예비비를 더한 값입니다.",
    )
    top_cols[1].metric(
        "추가 필요 현금",
        format_compact_won(result["shortage_cash"]),
        help="총 필요 자기자본에서 현재 보유 현금을 뺀 값입니다. 0 이하이면 현재 자금으로 가능하다는 뜻입니다.",
    )
    top_cols[2].metric(
        "전세가율",
        f"{result['jeonse_ratio']:.1f}%",
        help="예상 전세가를 매물가로 나눈 비율입니다.",
    )
    top_cols[3].metric(
        "급매 점수",
        f"{result['bargain_score']} ({result['bargain_grade']})",
        help="최근 평균가 대비 할인율, 1년 최고가 대비 하락률, 전세가율, 자금 가능성을 합산한 점수입니다.",
    )

    detail_cols = st.columns(3)
    detail_cols[0].metric(
        "예상 대출금",
        format_compact_won(result["expected_loan_amount"]),
        help="사용자 입력값이 있으면 그 값을 쓰고, 없으면 자금 프로필의 LTV 한도로 자동 계산합니다.",
    )
    detail_cols[1].metric(
        "평균 대비 할인율",
        f"{result['discount_vs_recent_avg']:.1f}%",
        help="최근 평균 매매가 대비 현재 매물가가 얼마나 낮은지 보여줍니다.",
    )
    detail_cols[2].metric(
        "고점 대비 하락률",
        f"{result['drop_from_high']:.1f}%",
        help="최근 1년 최고가 대비 현재 매물가가 얼마나 내려왔는지 보여줍니다.",
    )

    st.success(result["decision"])
    _render_result_interpretation(result)
    st.write("자동 계산 / 수동 보정 기준")
    source_df = pd.DataFrame(
        [
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
        ]
    )
    st.dataframe(source_df, use_container_width=True, hide_index=True)
    _render_formula_explainer(result, cost_total, own_cash)
    st.text_area("요약", value=result["summary"], height=160, disabled=True)

    st.write("부대비용 구성")
    st.metric("부대비용 합계", format_compact_won(cost_total))
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "항목": "취득세",
                    "계산 기준": f"매물가 x {settings.acquisition_tax_rate:.2%}",
                    "금액": format_compact_won(result["costs"]["acquisition_tax"]),
                },
                {
                    "항목": "중개보수",
                    "계산 기준": f"매물가 x {settings.brokerage_fee_rate:.2%}",
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
                    "계산 기준": f"매물가 x {settings.contingency_rate:.2%}",
                    "금액": format_compact_won(result["costs"]["contingency_fee"]),
                },
                {"항목": "합계", "계산 기준": "-", "금액": format_compact_won(cost_total)},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    if result["reasons"]:
        st.write("점수 반영 사유")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

    if result["risks"]:
        st.write("체크할 리스크")
        for risk in result["risks"]:
            st.write(f"- {risk}")

    _render_interpretation_guide()


def _render_formula_explainer(result: dict, cost_total: int, own_cash: int) -> None:
    with st.expander("계산식 자세히 보기"):
        st.markdown(
            "\n".join(
                [
                    "총 필요 자기자본",
                    f"- 계산식: 매물가 - 예상 대출금 - 예상 전세가 + 부대비용 합계",
                    f"- 실제 계산: {format_won(result['sale_price'])} - {format_won(result['expected_loan_amount'])} - {format_won(result['expected_jeonse_price'])} + {format_won(cost_total)} = {format_won(result['required_cash'])}",
                    "",
                    "추가 필요 현금",
                    f"- 계산식: 총 필요 자기자본 - 보유 현금",
                    f"- 실제 계산: {format_won(result['required_cash'])} - {format_won(own_cash)} = {format_won(result['shortage_cash'])}",
                    "",
                    "전세가율",
                    f"- 계산식: 예상 전세가 / 매물가 x 100",
                    f"- 실제 계산: {format_won(result['expected_jeonse_price'])} / {format_won(result['sale_price'])} x 100 = {result['jeonse_ratio']:.1f}%",
                    "",
                    "평균 대비 할인율",
                    f"- 계산식: (최근 평균가 - 매물가) / 최근 평균가 x 100",
                    f"- 실제 계산: ({format_won(result['derived_inputs']['recent_avg_price'])} - {format_won(result['sale_price'])}) / {format_won(result['derived_inputs']['recent_avg_price'])} x 100 = {result['discount_vs_recent_avg']:.1f}%",
                    "",
                    "고점 대비 하락률",
                    f"- 계산식: (최근 1년 최고가 - 매물가) / 최근 1년 최고가 x 100",
                    f"- 실제 계산: ({format_won(result['derived_inputs']['one_year_high_price'])} - {format_won(result['sale_price'])}) / {format_won(result['derived_inputs']['one_year_high_price'])} x 100 = {result['drop_from_high']:.1f}%",
                    "",
                    "급매 점수",
                    "- 최근 평균가 대비 할인 폭, 최근 1년 최고가 대비 하락 폭, 전세가율, 현재 자금으로 가능한지 여부를 반영해 계산합니다.",
                ]
            )
        )


def _render_interpretation_guide() -> None:
    st.subheader("지표 해석 가이드")

    jeonse_guide_df = pd.DataFrame(
        [
            {"전세가율 구간": "70% 이상", "해석": "투자금 부담은 낮을 수 있지만, 역전세 리스크를 함께 점검하는 것이 좋습니다."},
            {"전세가율 구간": "60% ~ 70%", "해석": "보통 수준으로 볼 수 있습니다."},
            {"전세가율 구간": "50% ~ 60%", "해석": "내가 직접 넣어야 하는 자금 부담이 커질 수 있습니다."},
            {"전세가율 구간": "50% 미만", "해석": "갭 투자 관점에서는 매력이 낮을 수 있습니다."},
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

    guide_col1, guide_col2 = st.columns(2)
    with guide_col1:
        st.write("전세가율 해석")
        st.dataframe(jeonse_guide_df, use_container_width=True, hide_index=True)
    with guide_col2:
        st.write("급매 점수 해석")
        st.dataframe(bargain_guide_df, use_container_width=True, hide_index=True)


def _render_result_interpretation(result: dict) -> None:
    jeonse_ratio = result["jeonse_ratio"]
    bargain_score = result["bargain_score"]

    if jeonse_ratio >= 70:
        st.info("전세가율 해석: 전세가율이 높아 투자금 부담은 낮을 수 있지만, 역전세 리스크를 함께 점검하는 편이 좋습니다.")
    elif jeonse_ratio >= 60:
        st.success("전세가율 해석: 전세가율은 보통 수준입니다.")
    elif jeonse_ratio >= 50:
        st.warning("전세가율 해석: 전세가율이 다소 낮아 직접 투입해야 하는 자금 부담이 커질 수 있습니다.")
    else:
        st.warning("전세가율 해석: 전세가율이 낮아 갭 투자 관점의 매력은 크지 않을 수 있습니다.")

    if bargain_score >= 80:
        st.success("급매 점수 해석: 강한 급매 후보로 볼 수 있습니다.")
    elif bargain_score >= 65:
        st.info("급매 점수 해석: 검토 가치가 있는 매물입니다.")
    elif bargain_score >= 50:
        st.info("급매 점수 해석: 보통 수준의 매물입니다.")
    else:
        st.warning("급매 점수 해석: 현재 기준으로는 급매 가능성이 낮습니다.")


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
