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
    st.caption("지금 어떤 후보를 먼저 검토해야 하는지, 현재 자금과 정책 기준으로 빠르게 보여줍니다.")

    analyses = analysis_repository.list_recent(limit=10)
    policy_events = policy_event_service.list_high_impact_events()

    if analyses:
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
        best_candidate = _best_candidate_payload(top_investment_df.iloc[0].to_dict())
        buyable_count = sum(
            1 for analysis in analyses if _numeric_value(analysis.get("shortage_cash")) <= 0
        )
        best_investment_score = max(
            (_numeric_value(analysis.get("investment_score")) for analysis in analyses),
            default=0.0,
        )

        cols = st.columns(4)
        cols[0].metric("추천 후보", best_candidate["단지"])
        cols[1].metric("투자점수", _best_candidate_score_label(best_candidate))
        cols[1].caption("현재 등록 후보 중 최고점")
        cols[2].metric("부족 자금", _best_candidate_shortage_label(best_candidate))
        cols[3].metric("매수 가능 여부", _best_candidate_purchase_status(best_candidate))

        st.subheader("지금 무엇을 사야 하는가")
        st.caption(
            _investment_summary_text(
                analysis_count=len(analyses),
                buyable_count=buyable_count,
                best_investment_score=best_investment_score,
                policy_event_count=_active_policy_event_count(policy_events),
            )
        )
        _render_best_candidate(
            best_candidate,
            policy_summary=_dashboard_policy_summary(policy_events),
        )

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
        with st.expander("최근 분석 결과", expanded=False):
            st.dataframe(analysis_df, use_container_width=True, hide_index=True)
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


def _render_best_candidate(row: dict[str, object], *, policy_summary: str | None) -> None:
    with st.container(border=True):
        st.markdown(f"### {row['단지']}")
        summary_cols = st.columns(4)
        summary_cols[0].metric("현재 자금", row["현재 자금"])
        summary_cols[1].metric("총 필요 현금", row["총 필요 현금"])
        summary_cols[2].metric("현재 자금 기준", _best_candidate_cash_status(row))
        summary_cols[3].metric("투자점수", _best_candidate_score_label(row))

        detail_cols = st.columns(2)
        with detail_cols[0]:
            st.write("추천 이유")
            for item in _best_candidate_reasons(row):
                st.write(f"- {item}")
        with detail_cols[1]:
            st.write("주의사항")
            for item in _best_candidate_cautions(row):
                st.write(f"- {item}")

        st.write("한 줄 결론")
        st.info(_best_candidate_conclusion(row))
        if policy_summary:
            st.write("현재 투자 판단에 영향을 주는 정책")
            st.caption(policy_summary)


def _investment_summary_text(
    *,
    analysis_count: int,
    buyable_count: int,
    best_investment_score: float,
    policy_event_count: int,
) -> str:
    return (
        f"최근 분석 {analysis_count}건 기준 현재 자금으로 바로 검토 가능한 후보는 {buyable_count}건입니다. "
        f"최고 투자점수는 {best_investment_score:.1f}점이며, 현재 확인할 활성 정책 이벤트는 {policy_event_count}건입니다."
    )


def _minimum_shortage_cash(analyses: list[dict]) -> int | None:
    if not analyses:
        return None
    return min(_shortage_needed_amount(analysis.get("shortage_cash")) for analysis in analyses)


def _metric_money_label(value: int | None) -> str:
    if value is None:
        return "-"
    return format_compact_won(value)


def _active_policy_event_count(policy_events: list[dict]) -> int:
    return sum(1 for event in policy_events if str(event.get("status") or "").upper() == "ACTIVE")


def _best_candidate_payload(row: dict[str, object]) -> dict[str, object]:
    required_cash = int(_numeric_value(row.get("required_cash")))
    raw_shortage_cash = int(_numeric_value(row.get("shortage_cash")))
    shortage_cash = _shortage_needed_amount(row.get("shortage_cash"))
    available_cash = max(required_cash - raw_shortage_cash, 0)
    return {
        "단지": row.get("complex_name") or "-",
        "투자 점수": int(_numeric_value(row.get("investment_score"))),
        "유동성": int(_numeric_value(row.get("liquidity_score"))),
        "급매 점수": int(_numeric_value(row.get("bargain_score"))),
        "현재 자금": format_compact_won(available_cash),
        "현재 자금_raw": available_cash,
        "총 필요 현금": format_compact_won(required_cash),
        "총 필요 현금_raw": required_cash,
        "추가 필요 현금": format_compact_won(shortage_cash),
        "추가 필요 현금_raw": shortage_cash,
        "매수 후 현금 잔액": format_compact_won(_cash_surplus_amount(row.get("shortage_cash"))),
        "매수 후 현금 잔액_raw": _cash_surplus_amount(row.get("shortage_cash")),
        "등급": _complex_grade_label(str(row.get("complex_grade") or "")),
    }


def _best_candidate_feasibility_label(row: dict[str, object]) -> str:
    return "가능" if _numeric_value(row.get("추가 필요 현금_raw")) <= 0 else "추가 자금 필요"


def _best_candidate_cash_status(row: dict[str, object]) -> str:
    shortage_cash = int(_numeric_value(row.get("추가 필요 현금_raw")))
    if shortage_cash <= 0:
        return "매수 가능"
    return f"{format_compact_won(shortage_cash)} 부족"


def _best_candidate_shortage_label(row: dict[str, object]) -> str:
    shortage_cash = int(_numeric_value(row.get("추가 필요 현금_raw")))
    if shortage_cash <= 0:
        return "0원"
    return format_compact_won(shortage_cash)


def _best_candidate_purchase_status(row: dict[str, object]) -> str:
    return "매수 가능" if _numeric_value(row.get("추가 필요 현금_raw")) <= 0 else "자금 보강 필요"


def _best_candidate_score_label(row: dict[str, object]) -> str:
    return f"{int(_numeric_value(row.get('투자 점수')))}점"


def _best_candidate_reasons(row: dict[str, object]) -> list[str]:
    reasons: list[str] = ["투자점수 1위"]
    if _numeric_value(row.get("유동성")) >= 80:
        reasons.append("유동성 우수")
    if str(row.get("등급") or "") == "준대장":
        reasons.append("단지등급 준대장")
    elif str(row.get("등급") or "") == "리더":
        reasons.append("단지등급 리더")
    if _numeric_value(row.get("추가 필요 현금_raw")) <= 0:
        reasons.append("현재 자금으로 검토 가능")
    return reasons[:4]


def _best_candidate_cautions(row: dict[str, object]) -> list[str]:
    cautions: list[str] = []
    if _numeric_value(row.get("추가 필요 현금_raw")) > 0:
        cautions.append(f"{row.get('추가 필요 현금', '-')} 부족")
    if _numeric_value(row.get("급매 점수")) < 30:
        cautions.append("급매 매력 낮음")
    if _numeric_value(row.get("유동성")) < 60:
        cautions.append("유동성 점검 필요")
    if str(row.get("등급") or "") not in {"리더", "준대장"}:
        cautions.append("단지 경쟁력은 보수적으로 확인 필요")
    if len(cautions) < 2 and _numeric_value(row.get("추가 필요 현금_raw")) > 0:
        cautions.append("자금 계획을 먼저 점검할 필요가 있습니다.")
    if len(cautions) < 2:
        cautions.append("정책/대출 조건 변화는 함께 확인하는 편이 좋습니다.")
    return cautions[:3]


def _best_candidate_conclusion(row: dict[str, object]) -> str:
    if _numeric_value(row.get("추가 필요 현금_raw")) <= 0:
        return f"{row.get('단지', '이 후보')}는 현재 후보 중 가장 현실적인 선택지입니다."
    return (
        f"{row.get('단지', '이 후보')}는 현재 후보 중 가장 현실적인 선택지입니다. "
        f"다만 매수하려면 약 {row.get('추가 필요 현금', '-')}의 추가 자금 확보가 필요합니다."
    )


def _dashboard_policy_summary(policy_events: list[dict]) -> str | None:
    active_events = [
        event for event in policy_events if str(event.get("status") or "").upper() == "ACTIVE"
    ]
    if not active_events:
        return None
    primary_event = active_events[0]
    policy_label = _policy_type_label(str(primary_event.get("policy_type") or "").upper())
    title = _policy_event_title(
        primary_event.get("policy_type"),
        primary_event.get("title"),
        primary_event.get("summary"),
    )
    if policy_label == "-":
        return title
    return f"{policy_label}: {title}"


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
