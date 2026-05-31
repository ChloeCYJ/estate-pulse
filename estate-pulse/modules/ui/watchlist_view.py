from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.utils.money_utils import format_compact_won


def render_watchlist_page(
    *,
    complex_repository,
    listing_repository,
    finance_repository,
    watchlist_repository,
    opportunity_service,
) -> None:
    st.title("Watchlist")
    st.caption("관심 단지와 관심 매물을 저장하고 현재 자금 기준으로 다시 확인합니다.")

    profiles = finance_repository.list_all()
    complexes = complex_repository.list_all()
    listings = listing_repository.list_all()

    if not profiles:
        st.info("먼저 자금 프로필을 등록해 주세요.")
        return

    profile_options = {_profile_label(item): item["id"] for item in profiles}
    selected_profile_id = profile_options[st.selectbox("자금 프로필", list(profile_options.keys()))]

    add_complex_col, add_listing_col = st.columns(2)
    with add_complex_col:
        st.subheader("단지 저장")
        if complexes:
            complex_options = {f"#{item['id']} | {item['name']}": int(item["id"]) for item in complexes}
            selected_complex = st.selectbox("관심 단지", list(complex_options.keys()), key="watchlist_complex")
            if st.button("단지 추가", use_container_width=True):
                watchlist_repository.add_complex(complex_options[selected_complex])
                st.success("관심 단지를 추가했습니다.")
        else:
            st.caption("등록된 단지가 없습니다.")

    with add_listing_col:
        st.subheader("매물 저장")
        if listings:
            listing_options = {
                f"#{item['id']} | {item['complex_name']} | {format_compact_won(item['sale_price'])}": int(item["id"])
                for item in listings
            }
            selected_listing = st.selectbox("관심 매물", list(listing_options.keys()), key="watchlist_listing")
            if st.button("매물 추가", use_container_width=True):
                watchlist_repository.add_listing(listing_options[selected_listing])
                st.success("관심 매물을 추가했습니다.")
        else:
            st.caption("등록된 매물이 없습니다.")

    st.divider()
    st.subheader("관심 목록")
    rows = opportunity_service.build_watchlist(finance_profile_id=selected_profile_id)
    if not rows:
        st.info("관심 목록이 비어 있습니다.")
        return

    st.caption("단지 저장은 단지 내 대표 매물 1건을 요약해서 보여주고, 매물 저장은 해당 매물 자체를 보여줍니다.")

    display_df = pd.DataFrame(rows)[
        [
            "watchlist_id",
            "watch_target",
            "summary_basis",
            "representative_listing_id",
            "complex_listing_count",
            "analysis_status",
            "complex_name",
            "sale_price",
            "required_cash",
            "shortage_cash",
            "bargain_score",
            "jeonse_ratio",
            "complex_grade_label",
            "liquidity_score",
            "investment_score",
            "latest_analysis_date",
        ]
    ].rename(
        columns={
            "watchlist_id": "ID",
            "watch_target": "저장 유형",
            "summary_basis": "요약 기준",
            "representative_listing_id": "대표 매물 ID",
            "complex_listing_count": "단지 내 매물 수",
            "analysis_status": "상태",
            "complex_name": "단지",
            "sale_price": "매매가",
            "required_cash": "필요 현금",
            "shortage_cash": "부족 현금",
            "bargain_score": "급매 점수",
            "jeonse_ratio": "전세가율",
            "complex_grade_label": "단지 등급",
            "liquidity_score": "유동성 점수",
            "investment_score": "투자 점수",
            "latest_analysis_date": "최근 분석일",
        }
    )
    for column in ["매매가", "필요 현금", "부족 현금"]:
        display_df[column] = display_df[column].map(_format_money_or_dash)
    display_df["전세가율"] = display_df["전세가율"].map(_format_percent_or_dash)
    display_df["대표 매물 ID"] = display_df["대표 매물 ID"].map(_format_int_or_dash)
    display_df["단지 내 매물 수"] = display_df["단지 내 매물 수"].map(_format_int_or_dash)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    removable_options = {
        f"#{item['watchlist_id']} | {item['complex_name']} | {item.get('watch_target', '-')}": int(item["watchlist_id"])
        for item in rows
    }
    selected_remove = st.selectbox("삭제할 항목", list(removable_options.keys()))
    if st.button("관심 목록에서 삭제", type="secondary"):
        watchlist_repository.delete(removable_options[selected_remove])
        st.success("관심 목록에서 삭제했습니다.")


def _profile_label(profile: dict) -> str:
    return f"#{profile['id']} | 보유 현금 {format_compact_won(profile['cash_amount'])}"


def _format_money_or_dash(value: int | float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return format_compact_won(value)


def _format_percent_or_dash(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.1f}%"


def _format_int_or_dash(value: int | float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return str(int(value))
