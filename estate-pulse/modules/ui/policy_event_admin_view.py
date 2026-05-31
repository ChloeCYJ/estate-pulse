from __future__ import annotations

from datetime import date, timedelta
import json

import pandas as pd
import streamlit as st

from modules.services.policy_import_service import (
    CANDIDATE_STATUS_APPROVED,
    CANDIDATE_STATUS_PENDING_REVIEW,
    CANDIDATE_STATUS_REJECTED,
)


def render_policy_event_admin_page(*, rule_admin_service, policy_import_service) -> None:
    st.title("정책 이벤트 관리")
    st.caption(
        "계산 규칙으로 바로 적용하지 않는 정책 참고 정보를 등록하고, 가져온 정책 이벤트 후보를 검토합니다."
    )

    _render_policy_event_management(rule_admin_service=rule_admin_service)
    st.divider()
    _render_policy_event_candidate_review(policy_import_service=policy_import_service)


def _render_policy_event_management(*, rule_admin_service) -> None:
    st.subheader("정책 이벤트 직접 등록")

    with st.form("policy_event_create_form"):
        type_col, impact_col = st.columns(2)
        policy_type = type_col.selectbox(
            "정책 유형",
            rule_admin_service.list_policy_event_types(),
            format_func=_policy_type_label,
        )
        impact_level = impact_col.selectbox(
            "영향도",
            rule_admin_service.list_policy_event_impact_levels(),
            format_func=_impact_level_label,
        )

        title = st.text_input("제목")
        summary = st.text_area("요약", height=80)
        detail = st.text_area("상세 내용", height=140)

        date_col1, date_col2 = st.columns(2)
        effective_from = date_col1.date_input("시작일")
        use_end_date = date_col2.checkbox("종료일 설정")
        effective_to = date_col2.date_input("종료일") if use_end_date else None

        region_col1, region_col2, region_col3 = st.columns(3)
        affected_region_sido = region_col1.text_input("대상 시도")
        affected_region_sigungu = region_col2.text_input("대상 시군구")
        affected_region_dong = region_col3.text_input("대상 읍면동")

        scope_col1, scope_col2 = st.columns(2)
        affected_buyer_type = scope_col1.selectbox(
            "대상 매수자",
            rule_admin_service.list_policy_event_buyer_types(),
            index=rule_admin_service.list_policy_event_buyer_types().index("ANY"),
            format_func=_buyer_type_label,
        )
        affected_investment_purpose = scope_col2.selectbox(
            "대상 목적",
            rule_admin_service.list_policy_event_investment_purposes(),
            index=rule_admin_service.list_policy_event_investment_purposes().index("ANY"),
            format_func=_investment_purpose_label,
        )

        flag_col1, flag_col2 = st.columns(2)
        calculation_supported = flag_col1.checkbox("계산 반영 가능")
        action_required = flag_col2.checkbox("사용자 조치 필요")

        source_name = st.text_input("출처명")
        source_text = st.text_area("원문", height=120)
        submitted = st.form_submit_button("정책 이벤트 등록")

    if submitted:
        try:
            rule_admin_service.create_policy_event(
                policy_type=policy_type,
                title=title,
                summary=summary,
                detail=detail,
                effective_from=effective_from.isoformat(),
                effective_to=effective_to.isoformat() if effective_to else None,
                affected_region_sido=affected_region_sido or None,
                affected_region_sigungu=affected_region_sigungu or None,
                affected_region_dong=affected_region_dong or None,
                affected_buyer_type=affected_buyer_type,
                affected_investment_purpose=affected_investment_purpose,
                impact_level=impact_level,
                calculation_supported=calculation_supported,
                action_required=action_required,
                source_text=source_text,
                source_name=source_name or None,
            )
            st.success("정책 이벤트를 등록했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    policy_type_filter = filter_col1.selectbox(
        "정책 유형 필터",
        ["ALL", *rule_admin_service.list_policy_event_types()],
        format_func=_policy_type_label,
    )
    status_filter = filter_col2.selectbox(
        "상태 필터",
        ["ALL", *rule_admin_service.list_policy_event_statuses()],
        format_func=_status_label,
    )
    impact_filter = filter_col3.selectbox(
        "영향도 필터",
        ["ALL", *rule_admin_service.list_policy_event_impact_levels()],
        format_func=_impact_level_label,
    )

    rows = rule_admin_service.list_policy_events(
        policy_type=None if policy_type_filter == "ALL" else policy_type_filter,
        status=None if status_filter == "ALL" else status_filter,
        impact_level=None if impact_filter == "ALL" else impact_filter,
    )
    if not rows:
        st.info("조건에 맞는 정책 이벤트가 없습니다.")
        return

    table_df = pd.DataFrame(rows)[
        [
            "policy_event_id",
            "policy_type",
            "title",
            "impact_level",
            "status",
            "effective_from",
            "effective_to",
            "affected_buyer_type",
            "affected_investment_purpose",
            "source_name",
        ]
    ].copy()
    table_df["policy_type"] = table_df["policy_type"].map(_policy_type_label)
    table_df["impact_level"] = table_df["impact_level"].map(_impact_level_label)
    table_df["status"] = table_df["status"].map(_status_label)
    table_df["affected_buyer_type"] = table_df["affected_buyer_type"].map(_buyer_type_label)
    table_df["affected_investment_purpose"] = table_df[
        "affected_investment_purpose"
    ].map(_investment_purpose_label)
    table_df = table_df.rename(
        columns={
            "policy_event_id": "ID",
            "policy_type": "정책 유형",
            "title": "제목",
            "impact_level": "영향도",
            "status": "상태",
            "effective_from": "시작일",
            "effective_to": "종료일",
            "affected_buyer_type": "대상 매수자",
            "affected_investment_purpose": "대상 목적",
            "source_name": "출처",
        }
    )
    st.dataframe(table_df, use_container_width=True, hide_index=True)

    options = {
        f"#{row['policy_event_id']} | {row['title']} | {_status_label(row['status'])}": row
        for row in rows
    }
    selected_label = st.selectbox("수정할 정책 이벤트 선택", list(options.keys()))
    selected_event = options[selected_label]

    with st.form("policy_event_edit_form"):
        type_col, impact_col = st.columns(2)
        edit_policy_type = type_col.selectbox(
            "정책 유형",
            rule_admin_service.list_policy_event_types(),
            index=rule_admin_service.list_policy_event_types().index(selected_event["policy_type"]),
            format_func=_policy_type_label,
        )
        edit_impact_level = impact_col.selectbox(
            "영향도",
            rule_admin_service.list_policy_event_impact_levels(),
            index=rule_admin_service.list_policy_event_impact_levels().index(
                selected_event["impact_level"]
            ),
            format_func=_impact_level_label,
        )

        edit_title = st.text_input("제목", value=selected_event["title"])
        edit_summary = st.text_area("요약", value=selected_event["summary"], height=80)
        edit_detail = st.text_area("상세 내용", value=selected_event["detail"], height=140)

        date_col1, date_col2 = st.columns(2)
        edit_effective_from = date_col1.date_input(
            "시작일",
            value=date.fromisoformat(selected_event["effective_from"]),
        )
        has_effective_to = selected_event.get("effective_to") is not None
        edit_use_end_date = date_col2.checkbox("종료일 설정", value=has_effective_to)
        edit_effective_to = (
            date_col2.date_input(
                "종료일",
                value=(
                    date.fromisoformat(selected_event["effective_to"])
                    if selected_event.get("effective_to")
                    else date.today()
                ),
                key=f"edit_effective_to_{selected_event['policy_event_id']}",
            )
            if edit_use_end_date
            else None
        )

        region_col1, region_col2, region_col3 = st.columns(3)
        edit_region_sido = region_col1.text_input(
            "대상 시도",
            value=selected_event.get("affected_region_sido") or "",
        )
        edit_region_sigungu = region_col2.text_input(
            "대상 시군구",
            value=selected_event.get("affected_region_sigungu") or "",
        )
        edit_region_dong = region_col3.text_input(
            "대상 읍면동",
            value=selected_event.get("affected_region_dong") or "",
        )

        scope_col1, scope_col2 = st.columns(2)
        edit_buyer_type = scope_col1.selectbox(
            "대상 매수자",
            rule_admin_service.list_policy_event_buyer_types(),
            index=rule_admin_service.list_policy_event_buyer_types().index(
                selected_event["affected_buyer_type"]
            ),
            format_func=_buyer_type_label,
        )
        edit_investment_purpose = scope_col2.selectbox(
            "대상 목적",
            rule_admin_service.list_policy_event_investment_purposes(),
            index=rule_admin_service.list_policy_event_investment_purposes().index(
                selected_event["affected_investment_purpose"]
            ),
            format_func=_investment_purpose_label,
        )

        flag_col1, flag_col2 = st.columns(2)
        edit_calculation_supported = flag_col1.checkbox(
            "계산 반영 가능",
            value=bool(selected_event["calculation_supported"]),
        )
        edit_action_required = flag_col2.checkbox(
            "사용자 조치 필요",
            value=bool(selected_event["action_required"]),
        )

        edit_source_name = st.text_input("출처명", value=selected_event.get("source_name") or "")
        edit_source_text = st.text_area(
            "원문",
            value=selected_event["source_text"],
            height=120,
        )

        save_edit = st.form_submit_button("변경사항 저장")

    if save_edit:
        try:
            rule_admin_service.update_policy_event(
                int(selected_event["policy_event_id"]),
                policy_type=edit_policy_type,
                title=edit_title,
                summary=edit_summary,
                detail=edit_detail,
                effective_from=edit_effective_from.isoformat(),
                effective_to=edit_effective_to.isoformat() if edit_effective_to else None,
                affected_region_sido=edit_region_sido or None,
                affected_region_sigungu=edit_region_sigungu or None,
                affected_region_dong=edit_region_dong or None,
                affected_buyer_type=edit_buyer_type,
                affected_investment_purpose=edit_investment_purpose,
                impact_level=edit_impact_level,
                calculation_supported=edit_calculation_supported,
                action_required=edit_action_required,
                source_text=edit_source_text,
                source_name=edit_source_name or None,
            )
            st.success("정책 이벤트를 수정했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    if st.button("선택한 정책 이벤트 만료 처리"):
        try:
            rule_admin_service.expire_policy_event(
                int(selected_event["policy_event_id"]),
                expired_on=(date.today() - timedelta(days=1)).isoformat(),
            )
            st.success("정책 이벤트를 만료 처리했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _render_policy_event_candidate_review(*, policy_import_service) -> None:
    st.subheader("가져온 정책 이벤트 후보 검토")
    policy_imports = policy_import_service.list_policy_imports()
    if not policy_imports:
        st.info("가져온 정책 문서가 없습니다.")
        return

    import_options = {
        f"#{item['id']} | {item.get('source_name') or 'Untitled'} | {item['created_at']}": int(
            item["id"]
        )
        for item in policy_imports
    }
    selected_import = st.selectbox("가져온 정책 문서 선택", list(import_options.keys()))
    detail = policy_import_service.get_policy_import_detail(
        import_options[selected_import],
        include_policy_event_candidates=True,
    )
    candidates = [
        item for item in detail["candidates"] if item["target_rule_type"] == "POLICY_EVENT"
    ]
    if not candidates:
        st.caption("이 가져오기에는 정책 이벤트 후보가 없습니다.")
        return

    for candidate in candidates:
        with st.expander(
            (
                f"{candidate['candidate_key']} | {candidate['rule_name']} | "
                f"{_candidate_status_label(candidate['status'])}"
            ),
            expanded=False,
        ):
            st.write(candidate["proposed_rule"].get("summary") or candidate["rule_name"])
            if candidate["warnings_list"]:
                for warning in candidate["warnings_list"]:
                    st.warning(_warning_label(warning))

            edited_json = st.text_area(
                "후보 JSON",
                value=json.dumps(
                    candidate["proposed_rule"],
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ),
                height=260,
                key=f"policy_event_candidate_json_{candidate['candidate_key']}",
            )

            action_cols = st.columns(5)
            if action_cols[0].button("JSON 저장", key=f"save_{candidate['candidate_key']}"):
                try:
                    policy_import_service.update_candidate_proposed_rule(
                        candidate_key=candidate["candidate_key"],
                        proposed_rule_json_text=edited_json,
                    )
                    st.success("후보 내용을 수정했습니다.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if action_cols[1].button("승인", key=f"approve_{candidate['candidate_key']}"):
                try:
                    policy_import_service.set_candidate_status(
                        candidate_key=candidate["candidate_key"],
                        status=CANDIDATE_STATUS_APPROVED,
                    )
                    st.success("후보를 승인했습니다.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if action_cols[2].button("반려", key=f"reject_{candidate['candidate_key']}"):
                try:
                    policy_import_service.set_candidate_status(
                        candidate_key=candidate["candidate_key"],
                        status=CANDIDATE_STATUS_REJECTED,
                    )
                    st.success("후보를 반려했습니다.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if action_cols[3].button("재검토", key=f"pending_{candidate['candidate_key']}"):
                try:
                    policy_import_service.set_candidate_status(
                        candidate_key=candidate["candidate_key"],
                        status=CANDIDATE_STATUS_PENDING_REVIEW,
                    )
                    st.success("후보 상태를 재검토로 변경했습니다.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if action_cols[4].button("저장 반영", key=f"apply_{candidate['candidate_key']}"):
                try:
                    policy_import_service.apply_candidates(
                        candidate_keys=[candidate["candidate_key"]]
                    )
                    st.success("후보를 정책 이벤트로 저장했습니다.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


def _policy_type_label(value: str) -> str:
    return {
        "ALL": "전체",
        "LOAN": "대출",
        "TAX": "세금",
        "REGULATION": "규제",
        "TRANSACTION": "거래",
        "PERMISSION": "허가",
        "CONTRACT": "계약",
        "INFO": "일반 정보",
    }.get(value, value)


def _impact_level_label(value: str) -> str:
    return {
        "ALL": "전체",
        "HIGH": "높음",
        "MEDIUM": "보통",
        "LOW": "낮음",
    }.get(value, value)


def _status_label(value: str) -> str:
    return {
        "ALL": "전체",
        "ACTIVE": "활성",
        "FUTURE": "예정",
        "EXPIRED": "만료",
    }.get(value, value)


def _buyer_type_label(value: str) -> str:
    return {
        "NO_HOME": "무주택",
        "ONE_HOME": "1주택",
        "MULTI_HOME": "다주택",
        "ANY": "전체",
    }.get(value, value)


def _investment_purpose_label(value: str) -> str:
    return {
        "OWNER_OCCUPIED": "실거주",
        "INVESTMENT": "투자",
        "ANY": "전체",
    }.get(value, value)


def _candidate_status_label(value: str) -> str:
    return {
        CANDIDATE_STATUS_PENDING_REVIEW: "검토 대기",
        CANDIDATE_STATUS_APPROVED: "승인",
        CANDIDATE_STATUS_REJECTED: "반려",
        "APPLIED": "적용 완료",
    }.get(value, value)


def _warning_label(value: str) -> str:
    return {
        "Effective date may require manual confirmation.": "시행일 또는 종료일을 수동으로 확인해 주세요.",
        "Effective start date was inferred from the import date or today because only an end date was found.": (
            "종료일만 발견되어 시작일을 가져오기 기준일 또는 오늘 날짜로 추정했습니다."
        ),
    }.get(value, value)
