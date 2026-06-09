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
        index=list(RANKING_TYPES.keys()).index("investment_score"),
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

    _render_top_rank_cards(rows)

    ranking_rows = []
    for row in rows[:top_n]:
        ranking_rows.append(
            {
                "단지": _ranking_complex_label(row),
                "매물가": row.get("sale_price"),
                "총 필요 현금": row.get("required_cash"),
                "추가 필요 현금": row.get("shortage_cash"),
                "급매 점수": row.get("bargain_score"),
                "전세가율": row.get("jeonse_ratio"),
                "단지 등급": row.get("complex_grade_label"),
                "유동성 점수": row.get("liquidity_score"),
                "투자 점수": row.get("investment_score"),
            }
        )

    ranking_df = pd.DataFrame(ranking_rows)
    for column in ["매물가", "총 필요 현금", "추가 필요 현금"]:
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


def _render_top_rank_cards(rows: list[dict]) -> None:
    top_candidates = [row for row in rows if row.get("analysis_available")][:3]
    if not top_candidates:
        return

    medals = ["🥇 1위", "🥈 2위", "🥉 3위"]
    cols = st.columns(len(top_candidates))
    for idx, row in enumerate(top_candidates):
        with cols[idx].container(border=True):
            st.markdown(f"**{medals[idx]}**")
            st.write(row.get("complex_name") or "-")
            st.write(f"매매가: {_format_money_or_dash(row.get('sale_price'))}")
            st.metric("투자 점수", _format_text_or_dash(row.get("investment_score")))
            st.write(
                f"추가 필요 현금: {_format_money_or_dash(row.get('shortage_cash'))}"
            )
            reason_lines = _top_rank_reason_lines(row)
            if reason_lines:
                st.caption("선정 이유")
                for line in reason_lines:
                    st.write(f"- {line}")


def _ranking_complex_label(row: dict) -> str:
    name = str(row.get("complex_name") or "-")
    if row.get("analysis_available"):
        return name
    return f"{name} (분석 불가: {_analysis_unavailable_reason(row.get('analysis_error'))})"


def _analysis_unavailable_reason(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "분석 데이터 없음"
    if "실거래" in text:
        return "실거래 데이터 부족"
    if "비교 가능한 매물이 없습니다" in text:
        return "분석 데이터 없음"
    return "분석 데이터 없음"


def _format_text_or_dash(value: object) -> str:
    if value is None or pd.isna(value):
        return "-"
    return str(value)


def _top_rank_reason_lines(row: dict) -> list[str]:
    lines: list[str] = []
    if row.get("investment_score") is not None:
        lines.append(f"투자점수 {_format_text_or_dash(row.get('investment_score'))}점")
    if row.get("bargain_score") is not None:
        lines.append(f"급매점수 {_format_text_or_dash(row.get('bargain_score'))}점")
    if row.get("jeonse_ratio") is not None:
        lines.append(f"전세가율 {_format_percent_or_dash(row.get('jeonse_ratio'))}")
    if row.get("complex_grade_label"):
        lines.append(f"단지등급 {row.get('complex_grade_label')}")
    shortage_cash = row.get("shortage_cash")
    if shortage_cash is not None:
        lines.append(f"추가 필요 현금 {_format_money_or_dash(shortage_cash)}")
    return lines[:5]
