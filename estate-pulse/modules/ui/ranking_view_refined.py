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
    st.title("투자 랭킹")
    st.caption("등록 단지의 단지·평형 후보를 기준으로 우선순위를 확인합니다.")

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
        index=list(RANKING_TYPES.keys()).index("investment_score"),
        format_func=lambda key: RANKING_TYPES[key]["label"],
    )
    top_n = st.slider("표시 개수", min_value=3, max_value=30, value=10)

    rows = opportunity_service.rank_listings(
        finance_profile_id=profile_options[selected_profile_label],
        ranking_type=ranking_type,
    )
    if not rows:
        st.info("랭킹을 계산할 후보가 없습니다.")
        return

    display_rows = []
    for row in rows[:top_n]:
        display_rows.append(
            {
                "후보": _candidate_label(row),
                "분석 기준가격": _price_basis_label(row),
                "추가 필요 현금": _format_money_or_dash(row.get("shortage_cash")),
                "매수 가능 여부": _purchase_label(row),
                "투자점수": row.get("investment_score") if row.get("analysis_available") else "-",
            }
        )
    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)


def _candidate_label(row: dict) -> str:
    area = row.get("area_bucket")
    area_text = "-" if area is None else f"{float(area):.1f}m²"
    return f"{row.get('complex_name') or '-'} | {area_text}"


def _price_basis_label(row: dict) -> str:
    source_label = {
        "LISTING": "호가 기준",
        "TRANSACTION_REFERENCE": "실거래 기준",
    }.get(str(row.get("price_source") or ""), "-")
    return f"{_format_money_or_dash(row.get('sale_price'))} | {source_label}"


def _purchase_label(row: dict) -> str:
    if not row.get("analysis_available"):
        return "분석 불가"
    return "가능" if float(row.get("shortage_cash") or 0) <= 0 else "추가 자금 필요"


def _format_money_or_dash(value: int | float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return format_compact_won(max(int(value), 0))
