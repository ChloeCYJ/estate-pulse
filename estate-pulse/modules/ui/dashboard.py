from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from modules.utils.money_utils import format_compact_won


def render_dashboard_page(
    *,
    complex_repository,
    listing_repository,
    finance_repository,
    analysis_repository,
    policy_event_service,
) -> None:
    st.title("Estate Pulse 투자 요약")
    st.caption("최근 분석 결과와 주요 정책 이벤트를 요약해서 보여줍니다.")

    complexes = complex_repository.list_all()
    listings = listing_repository.list_all()
    profiles = finance_repository.list_all()
    analyses = analysis_repository.list_recent(limit=10)
    policy_events = policy_event_service.list_high_impact_events()
    buyable_count = sum(1 for analysis in analyses if _numeric_value(analysis.get("shortage_cash")) <= 0)
    shortage_count = sum(1 for analysis in analyses if _numeric_value(analysis.get("shortage_cash")) > 0)
    best_investment_score = max(
        (_numeric_value(analysis.get("investment_score")) for analysis in analyses),
        default=0.0,
    )

    cols = st.columns(4)
    cols[0].metric("최근 분석", len(analyses))
    cols[1].metric("현금 충당 가능", buyable_count)
    cols[2].metric("추가 자금 필요", shortage_count)
    cols[3].metric("최고 후보 점수", f"{best_investment_score:.1f}")

    st.subheader("투자 요약")
    st.write(
        _investment_summary_text(
            analysis_count=len(analyses),
            buyable_count=buyable_count,
            best_investment_score=best_investment_score,
            policy_event_count=len(policy_events),
        )
    )

    if analyses:
        st.subheader("최근 분석 결과")
        analysis_df = pd.DataFrame(analyses)[
            [
                "complex_name",
                "sale_price",
                "investment_score",
                "complex_grade",
                "shortage_cash",
                "required_cash",
                "bargain_score",
                "liquidity_score",
                "created_at",
            ]
        ]
        analysis_df["cash_surplus"] = analysis_df["shortage_cash"].map(_cash_surplus_amount)
        analysis_df = analysis_df.rename(
            columns={
                "complex_name": "단지",
                "sale_price": "매수가",
                "required_cash": "총 필요 현금",
                "shortage_cash": "추가 필요 현금",
                "cash_surplus": "매수 후 현금 잔액",
                "bargain_score": "급매 점수",
                "liquidity_score": "유동성",
                "investment_score": "투자 점수",
                "complex_grade": "등급",
                "created_at": "분석일",
            }
        )
        analysis_df["추가 필요 현금"] = analysis_df["추가 필요 현금"].map(_shortage_needed_amount)
        for column in ["매수가", "총 필요 현금", "추가 필요 현금", "매수 후 현금 잔액"]:
            analysis_df[column] = analysis_df[column].map(format_compact_won)
        analysis_df["등급"] = analysis_df["등급"].map(_complex_grade_label)
        analysis_df["분석일"] = analysis_df["분석일"].map(_format_dashboard_datetime)
        analysis_df = analysis_df[
            [
                "단지",
                "매수가",
                "투자 점수",
                "등급",
                "추가 필요 현금",
                "매수 후 현금 잔액",
                "총 필요 현금",
                "급매 점수",
                "유동성",
                "분석일",
            ]
        ]
        st.dataframe(analysis_df.head(5), use_container_width=True, hide_index=True)
        if len(analysis_df) > 5:
            with st.expander("전체 최근 분석 보기", expanded=False):
                st.dataframe(analysis_df, use_container_width=True, hide_index=True)

        top_investment_df = pd.DataFrame(analyses).sort_values(
            by="investment_score",
            ascending=False,
        )
        top_investment_df = top_investment_df.drop_duplicates(
            subset=["complex_name"],
            keep="first",
        ).head(5)
        top_investment_df["cash_surplus"] = top_investment_df["shortage_cash"].map(_cash_surplus_amount)
        top_investment_df["shortage_cash"] = top_investment_df["shortage_cash"].map(
            _shortage_needed_amount
        )
        top_view_df = top_investment_df[
            [
                "complex_name",
                "investment_score",
                "liquidity_score",
                "bargain_score",
                "required_cash",
                "shortage_cash",
                "cash_surplus",
                "complex_grade",
            ]
        ].rename(
            columns={
                "complex_name": "단지",
                "investment_score": "투자 점수",
                "liquidity_score": "유동성",
                "bargain_score": "급매 점수",
                "required_cash": "총 필요 현금",
                "shortage_cash": "추가 필요 현금",
                "cash_surplus": "매수 후 현금 잔액",
                "complex_grade": "등급",
            }
        )
        top_view_df["총 필요 현금"] = top_view_df["총 필요 현금"].map(format_compact_won)
        top_view_df["추가 필요 현금"] = top_view_df["추가 필요 현금"].map(format_compact_won)
        top_view_df["매수 후 현금 잔액"] = top_view_df["매수 후 현금 잔액"].map(format_compact_won)
        top_view_df["등급"] = top_view_df["등급"].map(_complex_grade_label)
        st.subheader("최고 투자 후보")
        _render_best_candidate(top_view_df.iloc[0].to_dict())
        st.subheader("투자점수 상위 후보")
        _render_top_candidate_cards(top_view_df)
    else:
        st.info("저장된 분석 결과가 없습니다.")

    st.subheader("주요 정책/규제 이벤트")
    if not policy_events:
        st.info("현재 적용 중인 주요 정책/규제 이벤트가 없습니다.")
    else:
        event_df = pd.DataFrame(policy_events)[
            [
                "effective_from",
                "effective_to",
                "policy_type",
                "title",
                "summary",
                "impact_level",
                "status",
                "source_name",
            ]
        ]
        event_df["title"] = event_df.apply(
            lambda row: _policy_event_title(
                row.get("policy_type"),
                row.get("title"),
                row.get("summary"),
            ),
            axis=1,
        )
        event_df = event_df.drop(columns=["summary"]).rename(
            columns={
                "effective_from": "시작일",
                "effective_to": "종료일",
                "policy_type": "유형",
                "title": "제목",
                "impact_level": "영향도",
                "status": "상태",
                "source_name": "출처",
            }
        )
        event_df["시작일"] = event_df["시작일"].map(_format_dashboard_datetime)
        event_df["종료일"] = event_df["종료일"].map(_format_dashboard_datetime)
        event_df["유형"] = event_df["유형"].map(_policy_type_label)
        event_df["영향도"] = event_df["영향도"].map(_policy_impact_label)
        event_df["상태"] = event_df["상태"].map(_policy_status_label)
        st.dataframe(event_df, use_container_width=True, hide_index=True)

    with st.expander("관리자/데이터 관리 바로가기", expanded=False):
        st.caption("실제 메뉴 구조 기준 안내입니다. 직접 이동 기능은 포함하지 않았습니다.")
        st.markdown(
            "\n".join(
                [
                    "- 사용자 메뉴: 단지 관리, 매물 관리, 자금 프로필 관리, 분석, 관심단지, 비교, 랭킹",
                    "- 관리자 메뉴: 정책 이벤트 관리, 대출 규칙 관리, 세금 규칙 관리",
                    "- 관리자 메뉴: 중개보수 규칙 관리, 지역 규제 관리, 정책 가져오기",
                ]
            )
        )


def _complex_grade_label(value: str | None) -> str:
    labels = {
        "LEADER": "리더",
        "SUB_LEADER": "준대장",
        "NORMAL": "보통",
        "SMALL": "소형",
        "RISKY": "주의",
    }
    return labels.get(value or "", value or "-")


def _format_dashboard_datetime(value: str | None) -> str:
    if not value:
        return "-"
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        text = value.replace("T", " ")
        return text[:16] if len(text) >= 16 else text


def _numeric_value(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _shortage_needed_amount(value: object) -> int:
    return max(int(_numeric_value(value)), 0)


def _cash_surplus_amount(value: object) -> int:
    return max(int(-_numeric_value(value)), 0)


def _policy_event_title(policy_type: object, title: object, summary: object) -> str:
    policy_label = _policy_type_label(str(policy_type or "").strip().upper())
    title_text = str(title or "").strip()
    summary_text = str(summary or "").strip()
    title_text = _prettify_policy_title_text(title_text)
    summary_text = _prettify_policy_title_text(summary_text)
    if not summary_text:
        if not title_text:
            return "-"
        if len(title_text) < 16 and policy_label not in {"-", ""}:
            return f"{policy_label} 규제: {title_text}"
        return title_text
    if not title_text:
        return summary_text
    if len(title_text) < 16 and summary_text != title_text and policy_label not in {"-", ""}:
        return f"{policy_label} 규제: {summary_text}"
    if len(title_text) < 12 and summary_text != title_text:
        return f"{title_text} - {summary_text}"
    return title_text


def _policy_type_label(value: str | None) -> str:
    labels = {
        "LOAN": "대출",
        "TAX": "세금",
        "REGULATION": "규제",
        "SUPPLY": "공급",
        "OTHER": "기타",
        "TRANSACTION": "거래",
        "PERMISSION": "허가",
        "CONTRACT": "계약",
        "INFO": "정보",
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


def _render_top_candidate_cards(top_view_df: pd.DataFrame) -> None:
    if top_view_df.empty:
        st.caption("표시할 상위 후보가 없습니다.")
        return

    rows = top_view_df.to_dict(orient="records")
    for start in range(0, len(rows), 3):
        cols = st.columns(min(3, len(rows) - start))
        for idx, row in enumerate(rows[start : start + 3]):
            with cols[idx].container(border=True):
                st.markdown(f"**{row['단지']}**")
                st.caption(f"등급: {row['등급']}")
                st.metric("투자 점수", row["투자 점수"])
                st.write(f"총 필요 현금: {row['총 필요 현금']}")
                st.write(f"추가 필요 현금: {row['추가 필요 현금']}")
                st.write(f"매수 후 현금 잔액: {row['매수 후 현금 잔액']}")


def _render_best_candidate(row: dict[str, object]) -> None:
    with st.container(border=True):
        st.markdown(f"**{row['단지']}**")
        cols = st.columns(5)
        cols[0].metric("투자 점수", row["투자 점수"])
        cols[1].metric("등급", row["등급"])
        cols[2].metric("총 필요 현금", row["총 필요 현금"])
        cols[3].metric("추가 필요 현금", row["추가 필요 현금"])
        cols[4].metric("매수 후 현금 잔액", row["매수 후 현금 잔액"])


def _investment_summary_text(
    *,
    analysis_count: int,
    buyable_count: int,
    best_investment_score: float,
    policy_event_count: int,
) -> str:
    return (
        f"최근 분석 결과 {analysis_count}건 기준 현금으로 매수 가능한 후보는 {buyable_count}건이며, "
        f"최고 투자점수는 {best_investment_score:.1f}점입니다. "
        f"현재 주요 정책 이벤트는 {policy_event_count}건입니다."
    )


def _prettify_policy_title_text(text: str) -> str:
    if not text:
        return ""
    updated = text
    replacements = {
        "이상": " 이상",
        "이하": " 이하",
        "초과": " 초과",
        "미만": " 미만",
        "20억이상": "20억 이상",
        "25억이상": "25억 이상",
        "15억이상": "15억 이상",
        "2억대출": "2억 한도",
        "4억대출": "4억 한도",
        "6억대출": "6억 한도",
    }
    for source, target in replacements.items():
        updated = updated.replace(source, target)
    while "  " in updated:
        updated = updated.replace("  ", " ")
    return updated.strip()
