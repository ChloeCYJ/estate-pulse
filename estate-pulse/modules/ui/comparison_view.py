from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.utils.money_utils import format_compact_won


COMPARISON_SORT_OPTIONS = {
    "investment_score": "투자 점수",
    "required_cash": "총 필요 현금",
    "shortage_cash": "추가 필요 현금",
    "expected_loan_amount": "예상 대출",
    "total_transaction_cost": "거래 비용",
    "bargain_score": "급매 점수",
    "jeonse_ratio": "전세가율",
    "liquidity_score": "유동성 점수",
}


def render_comparison_page(
    *,
    listing_repository,
    finance_repository,
    opportunity_service,
) -> None:
    st.title("매물 비교")
    st.caption(
        "동일한 자금 조건으로 여러 매물을 동시에 비교합니다. "
        "어떤 매물이 가장 투자 가치가 높은지 확인할 수 있습니다."
    )

    listings = listing_repository.list_all()
    profiles = finance_repository.list_all()
    if not listings:
        st.info("비교할 매물이 없습니다.")
        return
    if not profiles:
        st.info("먼저 자금 프로필을 등록해 주세요.")
        return

    profile_options = {
        f"#{item['id']} | 보유 현금 {format_compact_won(item['cash_amount'])}": item["id"]
        for item in profiles
    }
    selected_profile_label = st.selectbox("자금 프로필", list(profile_options.keys()))
    listing_options = {
        f"#{item['id']} | {item['complex_name']} | {format_compact_won(item['sale_price'])}": int(item["id"])
        for item in listings
    }
    selected_listing_labels = st.multiselect(
        "비교할 매물",
        list(listing_options.keys()),
        default=list(listing_options.keys())[: min(5, len(listing_options))],
    )
    if not selected_listing_labels:
        st.info("비교할 매물을 선택해 주세요.")
        return

    sort_col, direction_col = st.columns(2)
    selected_sort_field = sort_col.selectbox(
        "정렬 기준",
        list(COMPARISON_SORT_OPTIONS.keys()),
        format_func=lambda key: COMPARISON_SORT_OPTIONS[key],
    )
    ascending = direction_col.checkbox(
        "오름차순",
        value=selected_sort_field in {"required_cash", "shortage_cash"},
    )

    rows = opportunity_service.compare_listings(
        listing_ids=[listing_options[label] for label in selected_listing_labels],
        finance_profile_id=profile_options[selected_profile_label],
        sort_field=selected_sort_field,
        ascending=ascending,
    )
    if not rows:
        st.info("비교 가능한 매물이 없습니다.")
        return

    unavailable_count = sum(1 for row in rows if not row.get("analysis_available"))
    if unavailable_count:
        st.warning(f"{unavailable_count}개 매물은 실거래 데이터 부족으로 분석 불가입니다.")

    display_df = pd.DataFrame(rows)[
        [
            "complex_name",
            "sale_price",
            "required_cash",
            "shortage_cash",
            "total_transaction_cost",
            "bargain_score",
            "jeonse_ratio",
            "complex_grade_label",
            "liquidity_score",
            "investment_score",
        ]
    ].rename(
        columns={
            "complex_name": "단지",
            "sale_price": "매물가",
            "required_cash": "총 필요 현금",
            "shortage_cash": "추가 필요 현금",
            "total_transaction_cost": "거래 비용",
            "bargain_score": "급매 점수",
            "jeonse_ratio": "전세가율",
            "complex_grade_label": "단지 등급",
            "liquidity_score": "유동성 점수",
            "investment_score": "투자 점수",
        }
    )
    for column in ["매물가", "총 필요 현금", "추가 필요 현금", "거래 비용"]:
        display_df[column] = display_df[column].map(_format_money_or_dash)
    display_df["전세가율"] = display_df["전세가율"].map(_format_percent_or_dash)
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def _format_money_or_dash(value: int | float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return format_compact_won(value)


def _format_percent_or_dash(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.1f}%"
