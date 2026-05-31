from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.utils.money_utils import format_compact_won


def render_dashboard_page(
    *,
    complex_repository,
    listing_repository,
    finance_repository,
    analysis_repository,
) -> None:
    st.title("Estate Pulse Dashboard")
    st.caption("Phase 2 기준으로 최근 분석, 단지 품질, 투자 비교 결과를 빠르게 확인합니다.")

    complexes = complex_repository.list_all()
    listings = listing_repository.list_all()
    profiles = finance_repository.list_all()
    analyses = analysis_repository.list_recent(limit=10)

    cols = st.columns(4)
    cols[0].metric("단지 수", len(complexes))
    cols[1].metric("매물 수", len(listings))
    cols[2].metric("자금 프로필 수", len(profiles))
    cols[3].metric("최근 분석 수", len(analyses))

    if not analyses:
        st.info("아직 분석 결과가 없습니다. 분석 화면에서 매물을 먼저 계산해 주세요.")
        return

    st.subheader("최근 분석 결과")
    analysis_df = pd.DataFrame(analyses)[
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
        analysis_df[column] = analysis_df[column].map(format_compact_won)
    analysis_df["단지 등급"] = analysis_df["단지 등급"].map(_complex_grade_label)
    st.dataframe(analysis_df, use_container_width=True, hide_index=True)

    top_investment_df = pd.DataFrame(analyses).sort_values(
        by="investment_score",
        ascending=False,
    ).head(5)
    st.subheader("최근 투자 점수 상위")
    top_view_df = top_investment_df[
        [
            "complex_name",
            "investment_score",
            "liquidity_score",
            "bargain_score",
            "required_cash",
            "complex_grade",
        ]
    ].rename(
        columns={
            "complex_name": "단지",
            "investment_score": "투자 점수",
            "liquidity_score": "유동성 점수",
            "bargain_score": "급매 점수",
            "required_cash": "필요 현금",
            "complex_grade": "단지 등급",
        }
    )
    top_view_df["필요 현금"] = top_view_df["필요 현금"].map(format_compact_won)
    top_view_df["단지 등급"] = top_view_df["단지 등급"].map(_complex_grade_label)
    st.dataframe(top_view_df, use_container_width=True, hide_index=True)


def _complex_grade_label(value: str | None) -> str:
    labels = {
        "LEADER": "대장",
        "SUB_LEADER": "준대장",
        "NORMAL": "일반",
        "SMALL": "나홀로",
        "RISKY": "유동성주의",
    }
    return labels.get(value or "", value or "-")
