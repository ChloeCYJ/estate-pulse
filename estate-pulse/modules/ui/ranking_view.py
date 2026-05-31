from __future__ import annotations

import pandas as pd
import streamlit as st

from config.scoring_rules import RANKING_TYPES
from modules.utils.money_utils import format_compact_won


def render_ranking_page(
    *,
    finance_repository,
    opportunity_service,
) -> None:
    st.title("Ranking")
    st.caption("전체 매물을 여러 기준으로 순위화합니다. 분석 불가 매물은 하단으로 내려갑니다.")

    profiles = finance_repository.list_all()
    if not profiles:
        st.info("먼저 자금 프로필을 등록해 주세요.")
        return

    profile_options = {
        f"#{item['id']} | 보유 현금 {format_compact_won(item['cash_amount'])}": item["id"]
        for item in profiles
    }
    selected_profile_label = st.selectbox("자금 프로필", list(profile_options.keys()))
    ranking_type = st.selectbox(
        "랭킹 기준",
        list(RANKING_TYPES.keys()),
        format_func=lambda key: RANKING_TYPES[key]["label"],
    )
    top_n = st.slider("표시 개수", min_value=3, max_value=30, value=10)

    rows = opportunity_service.rank_listings(
        finance_profile_id=profile_options[selected_profile_label],
        ranking_type=ranking_type,
    )
    if not rows:
        st.info("랭킹을 계산할 매물이 없습니다.")
        return

    unavailable_count = sum(1 for row in rows if not row.get("analysis_available"))
    if unavailable_count:
        st.warning(f"{unavailable_count}개 매물은 실거래 데이터 부족으로 분석 불가입니다.")

    ranking_df = pd.DataFrame(rows[:top_n])[
        [
            "complex_name",
            "analysis_status",
            "analysis_error",
            "sale_price",
            "required_cash",
            "shortage_cash",
            "bargain_score",
            "jeonse_ratio",
            "complex_grade_label",
            "liquidity_score",
            "investment_score",
        ]
    ].rename(
        columns={
            "complex_name": "단지",
            "analysis_status": "상태",
            "analysis_error": "메모",
            "sale_price": "매물가",
            "required_cash": "필요 현금",
            "shortage_cash": "부족 현금",
            "bargain_score": "급매 점수",
            "jeonse_ratio": "전세가율",
            "complex_grade_label": "단지 등급",
            "liquidity_score": "유동성 점수",
            "investment_score": "투자 점수",
        }
    )
    for column in ["매물가", "필요 현금", "부족 현금"]:
        ranking_df[column] = ranking_df[column].map(_format_money_or_dash)
    ranking_df["전세가율"] = ranking_df["전세가율"].map(_format_percent_or_dash)
    ranking_df.index = range(1, len(ranking_df) + 1)
    st.dataframe(ranking_df, use_container_width=True)


def _format_money_or_dash(value: int | float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return format_compact_won(value)


def _format_percent_or_dash(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.1f}%"
