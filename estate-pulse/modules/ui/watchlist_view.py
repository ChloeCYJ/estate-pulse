from __future__ import annotations

from datetime import datetime

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
    policy_event_service,
) -> None:
    st.title("투자 후보")
    st.caption("관심 단지와 관심 매물을 등록하고 투자 후보를 비교 관리합니다.")

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
        st.subheader("관심 단지 추가")
        if complexes:
            complex_options = {f"#{item['id']} | {item['name']}": int(item["id"]) for item in complexes}
            selected_complex = st.selectbox("단지", list(complex_options.keys()), key="watchlist_complex")
            if st.button("관심 단지 추가", use_container_width=True):
                watchlist_repository.add_complex(complex_options[selected_complex])
                st.success("관심 단지를 투자 후보에 추가했습니다.")
        else:
            st.caption("등록된 단지가 없습니다.")

    with add_listing_col:
        st.subheader("관심 매물 추가")
        if listings:
            listing_options = {
                f"#{item['id']} | {item['complex_name']} | {format_compact_won(item['sale_price'])}": int(item["id"])
                for item in listings
            }
            selected_listing = st.selectbox("매물", list(listing_options.keys()), key="watchlist_listing")
            if st.button("관심 매물 추가", use_container_width=True):
                watchlist_repository.add_listing(listing_options[selected_listing])
                st.success("관심 매물을 투자 후보에 추가했습니다.")
        else:
            st.caption("등록된 매물이 없습니다.")

    st.divider()
    st.subheader("투자 후보 목록")
    rows = opportunity_service.build_watchlist(finance_profile_id=selected_profile_id)
    if rows:
        display_df = pd.DataFrame(rows)[
            [
                "complex_name",
                "sale_price",
                "investment_score",
                "bargain_score",
                "liquidity_score",
                "shortage_cash",
                "complex_grade_label",
                "latest_analysis_date",
            ]
        ].rename(
            columns={
                "complex_name": "단지",
                "sale_price": "매물가",
                "investment_score": "투자점수",
                "bargain_score": "급매점수",
                "liquidity_score": "유동성",
                "shortage_cash": "추가 필요 현금",
                "complex_grade_label": "등급",
                "latest_analysis_date": "최근 분석일",
            }
        )
        for column in ["매물가", "추가 필요 현금"]:
            display_df[column] = display_df[column].map(_format_money_or_dash)
        display_df["최근 분석일"] = display_df["최근 분석일"].map(_format_datetime_or_dash)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        removable_options = {
            f"#{item['watchlist_id']} | {item['complex_name']} | {item.get('watch_target', '-')}": int(
                item["watchlist_id"]
            )
            for item in rows
        }
        selected_remove = st.selectbox("투자 후보 제거", list(removable_options.keys()))
        if st.button("투자 후보 제거", type="secondary"):
            watchlist_repository.delete(removable_options[selected_remove])
            st.success("투자 후보에서 제거했습니다.")
    else:
        st.info("등록된 투자 후보가 없습니다.")

    relevant_events = policy_event_service.list_high_impact_events()
    st.divider()
    st.subheader("관련 정책 이벤트")
    if not relevant_events:
        st.caption("현재 적용 중이거나 예정된 주요 정책 이벤트가 없습니다.")
        return

    event_df = pd.DataFrame(relevant_events)[
        [
            "effective_from",
            "effective_to",
            "policy_type",
            "title",
            "impact_level",
            "status",
        ]
    ].rename(
        columns={
            "effective_from": "시작일",
            "effective_to": "종료일",
            "policy_type": "유형",
            "title": "제목",
            "impact_level": "영향도",
            "status": "상태",
        }
    )
    event_df["시작일"] = event_df["시작일"].map(_format_datetime_or_dash)
    event_df["종료일"] = event_df["종료일"].map(_format_datetime_or_dash)
    event_df["유형"] = event_df["유형"].map(_policy_type_label)
    event_df["영향도"] = event_df["영향도"].map(_policy_impact_label)
    event_df["상태"] = event_df["상태"].map(_policy_status_label)
    st.dataframe(event_df, use_container_width=True, hide_index=True)


def _profile_label(profile: dict) -> str:
    return f"#{profile['id']} | 현금 {format_compact_won(profile['cash_amount'])}"


def _format_money_or_dash(value: int | float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return format_compact_won(value)


def _format_datetime_or_dash(value: str | None) -> str:
    if not value:
        return "-"
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        text = value.replace("T", " ")
        return text[:16] if len(text) >= 16 else text


def _policy_type_label(value: str | None) -> str:
    labels = {
        "LOAN": "대출",
        "TAX": "세금",
        "REGULATION": "규제",
    }
    return labels.get(value or "", value or "-")


def _policy_impact_label(value: str | None) -> str:
    labels = {
        "HIGH": "중요",
        "MEDIUM": "보통",
        "LOW": "낮음",
    }
    return labels.get(value or "", value or "-")


def _policy_status_label(value: str | None) -> str:
    labels = {
        "ACTIVE": "적용 중",
        "FUTURE": "예정",
        "UPCOMING": "예정",
        "EXPIRED": "종료",
    }
    return labels.get(value or "", value or "-")
