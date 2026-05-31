from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from modules.services.policy_import_service import (
    CANDIDATE_STATUS_APPLIED,
    CANDIDATE_STATUS_APPROVED,
    CANDIDATE_STATUS_PENDING_REVIEW,
    CANDIDATE_STATUS_REJECTED,
)
from modules.ui.policy_event_admin_view import render_policy_event_admin_page
from modules.utils.money_utils import format_compact_won


GROUP_ORDER = ("POLICY_EVENT", "REGION_POLICY", "LOAN", "TAX", "BROKERAGE", "UNKNOWN")
DRAFT_KEY = "policy_import_draft_sections"


def render_admin_page(*, rule_admin_service, policy_import_service, complex_repository=None) -> None:
    st.title("관리자")
    st.caption("규칙 조회, 지역 규제 상태 관리, 정책 문서 후보 생성과 검토를 처리합니다.")

    (
        policy_event_tab,
        loan_tab,
        tax_tab,
        brokerage_tab,
        region_tab,
        import_tab,
    ) = st.tabs(
        ["정책 이벤트", "대출 규칙", "세금 규칙", "중개보수 규칙", "지역 규제 상태", "정책 가져오기"]
    )

    with policy_event_tab:
        render_policy_event_admin_page(
            rule_admin_service=rule_admin_service,
            policy_import_service=policy_import_service,
        )
    with loan_tab:
        _render_rule_table("대출 규칙", rule_admin_service.list_loan_rules(), "loan")
    with tax_tab:
        _render_rule_table("세금 규칙", rule_admin_service.list_tax_rules(), "tax")
    with brokerage_tab:
        _render_rule_table("중개보수 규칙", rule_admin_service.list_brokerage_rules(), "brokerage")
    with region_tab:
        _render_region_policy_tab(
            rule_admin_service=rule_admin_service,
            complex_repository=complex_repository,
        )
    with import_tab:
        _render_policy_import_tab(policy_import_service=policy_import_service)


def _render_rule_table(title: str, rows: list[dict[str, str]], kind: str) -> None:
    st.subheader(title)
    if not rows:
        st.info("표시할 규칙이 없습니다.")
        return

    df = pd.DataFrame(rows)
    if kind == "loan":
        df = df.rename(columns=_loan_column_labels())
    elif kind == "tax":
        df = df.rename(columns=_tax_column_labels())
    else:
        df = df.rename(columns=_brokerage_column_labels())
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_region_policy_tab(*, rule_admin_service, complex_repository=None) -> None:
    st.subheader("지역 규제 상태")
    st.caption("분석의 지역 규제 판정은 여기 등록된 상태를 우선 사용합니다.")
    if complex_repository is not None:
        st.caption(f"등록 단지 수: {len(complex_repository.list_all())}")

    with st.form("region_policy_status_form"):
        level_col, type_col = st.columns(2)
        region_level = level_col.selectbox(
            "지역 레벨",
            rule_admin_service.list_region_levels(),
            format_func=_region_level_label,
        )
        policy_type = type_col.selectbox(
            "정책 유형",
            rule_admin_service.list_region_policy_types(),
            format_func=_region_policy_type_label,
        )

        addr_col1, addr_col2, addr_col3 = st.columns(3)
        sido = addr_col1.text_input("시도", value="서울")
        sigungu = addr_col2.text_input("시군구")
        dong = addr_col3.text_input("동")

        date_col1, date_col2 = st.columns(2)
        effective_from = date_col1.date_input("적용 시작일")
        use_end_date = date_col2.checkbox("종료일 입력")
        effective_to = st.date_input("적용 종료일") if use_end_date else None

        notes = st.text_input("메모")
        submitted = st.form_submit_button("지역 규제 상태 저장")

    if submitted:
        try:
            rule_admin_service.create_region_policy_status(
                region_level=region_level,
                sido=sido,
                sigungu=sigungu,
                dong=dong,
                policy_type=policy_type,
                effective_from=effective_from.isoformat(),
                effective_to=effective_to.isoformat() if effective_to else None,
                notes=notes or None,
            )
            st.success("지역 규제 상태를 저장했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    st.divider()
    rows = rule_admin_service.list_region_policy_statuses()
    if not rows:
        st.info("등록된 지역 규제 상태가 없습니다.")
        return

    st.dataframe(
        pd.DataFrame(rows).rename(columns=_region_policy_column_labels()),
        use_container_width=True,
        hide_index=True,
    )

    options = {
        f"#{row['id']} | {row['region_scope']} | {row['policy_type']} | {row['effective_from']}": int(
            row["id"]
        )
        for row in rows
    }
    selected = st.selectbox("삭제할 지역 규제 상태", list(options.keys()))
    if st.button("선택 항목 삭제"):
        try:
            rule_admin_service.delete_region_policy_status(options[selected])
            st.success("지역 규제 상태를 삭제했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _render_policy_import_tab(*, policy_import_service) -> None:
    st.subheader("정책 문서 가져오기")
    st.caption("문단 분석 -> 지역 그룹 확장 확인 -> 후보 생성 -> 승인 -> 최종 적용 순서로 진행합니다.")

    with st.form("policy_import_analysis_form"):
        source_name = st.text_input("정책 문서 이름", value="관리자 입력 정책")
        selector_cols = st.columns(3)
        target_rule_type = selector_cols[0].selectbox(
            "대상 규칙 유형",
            policy_import_service.list_import_target_rule_types(),
            format_func=_target_rule_type_label,
        )
        parser_name = selector_cols[1].selectbox(
            "파서",
            policy_import_service.list_parser_names(),
            index=0,
        )
        effective_date = selector_cols[2].date_input("시행일")
        source_text = st.text_area(
            "정책 원문",
            height=220,
            placeholder="예: 현재 규제지역은 서울 전역과 경기 주요 12개 지역입니다.",
        )
        submitted = st.form_submit_button("문단 분석")

    if submitted:
        try:
            sections = policy_import_service.preview_policy_sections(
                source_text=source_text,
                target_rule_type=target_rule_type,
                parser_name=parser_name,
            )
            st.session_state[DRAFT_KEY] = {
                "source_name": source_name or None,
                "target_rule_type": target_rule_type,
                "parser_name": parser_name,
                "effective_date": effective_date.isoformat(),
                "source_text": source_text,
                "sections": sections,
            }
            st.success(f"문단 {len(sections)}건을 분석했습니다.")
        except Exception as exc:
            st.error(str(exc))

    draft = st.session_state.get(DRAFT_KEY)
    if draft:
        _render_section_review(draft=draft, policy_import_service=policy_import_service)

    st.divider()
    _render_policy_import_review(policy_import_service=policy_import_service)


def _render_section_review(*, draft: dict, policy_import_service) -> None:
    st.subheader("문단 분류 결과")
    grouped_sections = _group_items_by_target_rule_type(draft["sections"])
    section_type_options = [
        "POLICY_EVENT",
        "REGION_POLICY",
        "LOAN",
        "TAX",
        "BROKERAGE",
        "UNKNOWN",
    ]

    for section in draft["sections"]:
        selected_key = f"section_selected_{section['section_id']}"
        type_key = f"section_type_{section['section_id']}"
        if selected_key not in st.session_state:
            st.session_state[selected_key] = section["target_rule_type"] != "UNKNOWN"
        if type_key not in st.session_state:
            st.session_state[type_key] = section["target_rule_type"]

    action_cols = st.columns(4)
    if action_cols[0].button("전체 선택", key="policy_section_select_all"):
        for section in draft["sections"]:
            st.session_state[f"section_selected_{section['section_id']}"] = True
    if action_cols[1].button("추천만 선택", key="policy_section_select_recommended"):
        for section in draft["sections"]:
            st.session_state[f"section_selected_{section['section_id']}"] = (
                st.session_state.get(
                    f"section_type_{section['section_id']}",
                    section["target_rule_type"],
                )
                != "UNKNOWN"
            )
    if action_cols[2].button("전체 해제", key="policy_section_clear_all"):
        for section in draft["sections"]:
            st.session_state[f"section_selected_{section['section_id']}"] = False
    selected_count = sum(
        1
        for section in draft["sections"]
        if st.session_state.get(f"section_selected_{section['section_id']}", False)
    )
    action_cols[3].metric("선택 문단", f"{selected_count} / {len(draft['sections'])}")

    summary_rows = []
    for section in draft["sections"]:
        metadata = dict(section.get("metadata") or {})
        summary_rows.append(
            {
                "문단 ID": section["section_id"],
                "분류 유형": _target_rule_type_label(section["target_rule_type"]),
                "검토 상태": _review_state_label(metadata.get("review_state")),
                "신뢰도": _format_confidence(section.get("confidence")),
                "경고": " / ".join(section.get("warnings", [])) or "-",
                "원문": section["source_text"],
            }
        )
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    for target_rule_type in GROUP_ORDER:
        sections = grouped_sections.get(target_rule_type, [])
        if not sections:
            continue
        st.subheader(_group_section_title(target_rule_type))
        for section in sections:
            metadata = dict(section.get("metadata") or {})
            with st.expander(
                f"{section['section_id']} | {_target_rule_type_label(section['target_rule_type'])}",
                expanded=section["target_rule_type"] == "POLICY_EVENT",
            ):
                st.write(section["source_text"])
                if metadata.get("review_state") == "REVIEW_REQUIRED":
                    st.info("이 문단은 추가 확인 필요 상태입니다. 지역 목록을 직접 확인하거나 입력해 주세요.")
                if section.get("warnings"):
                    for warning in section["warnings"]:
                        st.warning(warning)
                cols = st.columns(2)
                cols[0].selectbox(
                    "분류 유형 수정",
                    section_type_options,
                    index=section_type_options.index(
                        st.session_state.get(
                            f"section_type_{section['section_id']}",
                            section["target_rule_type"],
                        )
                    ),
                    format_func=_target_rule_type_label,
                    key=f"section_type_{section['section_id']}",
                )
                cols[1].checkbox(
                    "후보 생성에 포함",
                    value=st.session_state.get(
                        f"section_selected_{section['section_id']}",
                        section["target_rule_type"] != "UNKNOWN",
                    ),
                    key=f"section_selected_{section['section_id']}",
                )
                if section["target_rule_type"] == "REGION_POLICY":
                    _render_region_expansion_editor(section=section, metadata=metadata)

    if st.button("선택 문단으로 후보 생성", type="primary"):
        selected_sections = []
        for section in draft["sections"]:
            if not st.session_state.get(f"section_selected_{section['section_id']}", False):
                continue
            selected_sections.append(
                {
                    **section,
                    "target_rule_type": st.session_state.get(
                        f"section_type_{section['section_id']}",
                        section["target_rule_type"],
                    ),
                    "metadata": _collect_section_metadata(section),
                }
            )

        try:
            result = policy_import_service.create_policy_import_from_sections(
                source_text=draft["source_text"],
                source_name=draft["source_name"],
                target_rule_type=draft["target_rule_type"],
                effective_date=draft["effective_date"],
                parser_name=draft["parser_name"],
                selected_sections=selected_sections,
            )
            st.success(
                f"정책 가져오기 #{result['policy_import_id']} 생성 완료. "
                f"후보 {len(result['candidate_ids'])}건을 검토해 주세요."
            )
            st.session_state.pop(DRAFT_KEY, None)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _render_region_expansion_editor(*, section: dict, metadata: dict) -> None:
    group_label = metadata.get("region_group_label")
    expanded_regions = metadata.get("expanded_regions") or []
    initial_value = "\n".join(_format_region_line(item) for item in expanded_regions)

    if metadata.get("requires_region_expansion"):
        st.info(
            f"지역 그룹 표현 감지: {group_label or '미확정 그룹'}. "
            "문서에 실제 목록이 없으면 관리자가 직접 입력한 지역만 확장됩니다."
        )
    elif group_label:
        st.caption(f"감지된 범위: {group_label}")

    st.text_area(
        "확장 지역 목록",
        value=initial_value,
        placeholder="예: 서울 강남구\n경기 수원시 영통구",
        key=f"section_expanded_regions_{section['section_id']}",
        height=120,
    )


def _collect_section_metadata(section: dict) -> dict:
    metadata = dict(section.get("metadata") or {})
    if section["target_rule_type"] != "REGION_POLICY":
        return metadata
    expanded_regions = _parse_region_lines(
        st.session_state.get(f"section_expanded_regions_{section['section_id']}", "")
    )
    metadata["expanded_regions"] = expanded_regions
    if expanded_regions:
        metadata["requires_region_expansion"] = False
        metadata["review_state"] = "READY"
    elif metadata.get("requires_region_expansion"):
        metadata["review_state"] = "REVIEW_REQUIRED"
    return metadata


def _render_policy_import_review(*, policy_import_service) -> None:
    st.subheader("가져온 정책 검토")
    imports = policy_import_service.list_policy_imports()
    if not imports:
        st.info("아직 가져온 정책 문서가 없습니다.")
        return

    options = {_policy_import_label(item): int(item["id"]) for item in imports}
    selected_label = st.selectbox("검토할 정책 가져오기", list(options.keys()))
    detail = policy_import_service.get_policy_import_detail(options[selected_label])
    policy_import = detail["policy_import"]
    candidates = detail["candidates"]
    grouped_candidates = _group_items_by_target_rule_type(candidates)

    cols = st.columns(4)
    cols[0].metric("정책 ID", str(policy_import["id"]))
    cols[1].metric("대상 규칙", _target_rule_type_label(str(policy_import["target_rule_type"])))
    cols[2].metric("파서", str(policy_import["parser_name"]))
    cols[3].metric("상태", str(policy_import["parser_status"]))
    st.caption(f"시행일: {policy_import.get('effective_date') or '-'}")

    if not candidates:
        st.info("이 정책 문서에서 기존 활성 규칙과 비교해 실제로 달라지는 항목이 없어 후보가 생성되지 않았습니다.")
        return

    summary_rows = []
    for item in candidates:
        summary_rows.append(
            {
                "후보 ID": item["id"],
                "규칙 유형": _target_rule_type_label(item["target_rule_type"]),
                "상태": _candidate_status_label(item["status"]),
                "변경 요약": item.get("change_summary") or "-",
                "규칙 버전": item.get("rule_version") or "-",
                "신뢰도": _format_confidence(item.get("confidence")),
                "경고": " / ".join(item["warnings_list"]) or "-",
            }
        )
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    for target_rule_type in GROUP_ORDER:
        rows = grouped_candidates.get(target_rule_type, [])
        if not rows:
            continue
        st.subheader(_group_section_title(target_rule_type))
        for candidate in rows:
            with st.expander(
                f"후보 #{candidate['id']} | {_candidate_status_label(candidate['status'])} | {candidate['rule_name']}",
                expanded=False,
            ):
                _render_candidate_detail(
                    candidate=candidate,
                    policy_import_service=policy_import_service,
                )

    st.divider()
    _render_apply_section(
        grouped_candidates=grouped_candidates,
        policy_import_service=policy_import_service,
    )


def _render_candidate_detail(*, candidate: dict, policy_import_service) -> None:
    cols = st.columns(5)
    cols[0].metric("후보 ID", str(candidate["id"]))
    cols[1].metric("규칙 유형", _target_rule_type_label(candidate["target_rule_type"]))
    cols[2].metric("상태", _candidate_status_label(candidate["status"]))
    cols[3].metric("신뢰도", _format_confidence(candidate.get("confidence")))
    cols[4].metric("변경 필드 수", str(len(candidate["changed_fields_list"])))

    if candidate.get("changed_field_details"):
        st.write("변경 내용")
        st.dataframe(
            pd.DataFrame(candidate["changed_field_details"]).rename(
                columns={
                    "label": "항목",
                    "previous_value": "이전 값",
                    "proposed_value": "제안 값",
                }
            )[["항목", "이전 값", "제안 값"]],
            use_container_width=True,
            hide_index=True,
        )
    elif candidate["target_rule_type"] in {"LOAN", "TAX", "BROKERAGE"}:
        st.info("실제 정책 변경 필드가 없습니다. 이 후보는 적용 대상이 아닙니다.")

    compare_cols = st.columns(2)
    with compare_cols[0]:
        st.write("이전 값")
        if candidate["previous_rule"] is None:
            st.caption("이전 값 없음")
        else:
            st.json(candidate["previous_rule"], expanded=False)
    with compare_cols[1]:
        st.write("제안 값")
        st.json(candidate["proposed_rule"], expanded=False)

    if candidate["warnings_list"]:
        st.write("경고")
        for warning in candidate["warnings_list"]:
            if warning.startswith("ERROR:"):
                st.error(warning)
            else:
                st.warning(warning)

    edited_json = st.text_area(
        "제안 규칙 JSON 수정",
        value=json.dumps(candidate["proposed_rule"], ensure_ascii=False, indent=2, sort_keys=True),
        height=260,
        key=f"candidate_json_editor_{candidate['id']}",
    )
    action_cols = st.columns(4)
    if action_cols[0].button("JSON 저장", key=f"save_candidate_{candidate['id']}"):
        try:
            policy_import_service.update_candidate_proposed_rule(
                candidate_id=int(candidate["id"]),
                proposed_rule_json_text=edited_json,
            )
            st.success("후보 JSON을 저장했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    if action_cols[1].button("승인", key=f"approve_candidate_{candidate['id']}"):
        try:
            policy_import_service.set_candidate_status(
                candidate_id=int(candidate["id"]),
                status=CANDIDATE_STATUS_APPROVED,
            )
            st.success("후보를 승인했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    if action_cols[2].button("반려", key=f"reject_candidate_{candidate['id']}"):
        try:
            policy_import_service.set_candidate_status(
                candidate_id=int(candidate["id"]),
                status=CANDIDATE_STATUS_REJECTED,
            )
            st.success("후보를 반려했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    if action_cols[3].button("재검토", key=f"pending_candidate_{candidate['id']}"):
        try:
            policy_import_service.set_candidate_status(
                candidate_id=int(candidate["id"]),
                status=CANDIDATE_STATUS_PENDING_REVIEW,
            )
            st.success("후보를 재검토 상태로 변경했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    if candidate["target_rule_type"] == "LOAN":
        st.divider()
        _render_loan_preview(candidate=candidate, policy_import_service=policy_import_service)
    elif candidate["target_rule_type"] == "UNKNOWN":
        st.info("미분류 후보는 검토만 가능하고 적용은 할 수 없습니다.")


def _render_loan_preview(*, candidate: dict, policy_import_service) -> None:
    st.write("대출 규칙 미리보기")
    preview_cols = st.columns(4)
    sale_price = int(
        preview_cols[0].number_input(
            "매매가",
            min_value=0,
            value=1_200_000_000,
            step=10_000_000,
            key=f"preview_sale_price_{candidate['id']}",
        )
    )
    region_type = preview_cols[1].selectbox(
        "지역 유형",
        ["NON_REGULATED", "REGULATED"],
        format_func=_loan_region_type_label,
        key=f"preview_region_{candidate['id']}",
    )
    buyer_type = preview_cols[2].selectbox(
        "매수자 유형",
        ["NO_HOME", "ONE_HOME", "MULTI_HOME"],
        format_func=_buyer_type_label,
        key=f"preview_buyer_{candidate['id']}",
    )
    purpose = preview_cols[3].selectbox(
        "투자 목적",
        ["OWNER_OCCUPIED", "INVESTMENT"],
        format_func=_investment_purpose_label,
        key=f"preview_purpose_{candidate['id']}",
    )

    extra_cols = st.columns(3)
    annual_income = int(
        extra_cols[0].number_input(
            "연소득",
            min_value=0,
            value=120_000_000,
            step=10_000_000,
            key=f"preview_income_{candidate['id']}",
        )
    )
    existing_debt = int(
        extra_cols[1].number_input(
            "기존 대출",
            min_value=0,
            value=0,
            step=10_000_000,
            key=f"preview_debt_{candidate['id']}",
        )
    )
    annual_interest_rate = float(
        extra_cols[2].number_input(
            "금리",
            min_value=0.0,
            value=0.04,
            step=0.01,
            format="%.2f",
            key=f"preview_rate_{candidate['id']}",
        )
    )

    if st.button("미리보기 계산", key=f"preview_button_{candidate['id']}"):
        try:
            preview = policy_import_service.preview_loan_candidate(
                candidate_id=int(candidate["id"]),
                sale_price=sale_price,
                region_type=region_type,
                buyer_type=buyer_type,
                investment_purpose=purpose,
                annual_income=annual_income or None,
                existing_debt=existing_debt,
                annual_interest_rate=annual_interest_rate or None,
            )
            result_cols = st.columns(3)
            result_cols[0].metric("기존 예상 대출액", format_compact_won(preview["old_result"]["final_loan_amount"]))
            result_cols[1].metric("제안 예상 대출액", format_compact_won(preview["proposed_result"]["final_loan_amount"]))
            result_cols[2].metric("차이", format_compact_won(preview["difference_in_estimated_loan_amount"]))
        except Exception as exc:
            st.error(str(exc))


def _render_apply_section(*, grouped_candidates: dict[str, list[dict]], policy_import_service) -> None:
    selectable_groups = ("REGION_POLICY", "LOAN", "TAX", "BROKERAGE")
    approved_found = any(
        item["status"] == CANDIDATE_STATUS_APPROVED
        for group in selectable_groups
        for item in grouped_candidates.get(group, [])
    )
    if not approved_found:
        st.info("최종 적용을 하려면 먼저 지역 규제, 대출, 세금, 중개보수 후보를 승인해 주세요.")
        return

    selected_ids: list[int] = []
    for target_rule_type in selectable_groups:
        approved_rows = [
            item
            for item in grouped_candidates.get(target_rule_type, [])
            if item["status"] == CANDIDATE_STATUS_APPROVED
        ]
        if not approved_rows:
            continue
        st.write(f"{_group_section_title(target_rule_type)} 최종 적용 선택")
        options = {
            f"#{item['id']} | {item['rule_name']} | {_candidate_status_label(item['status'])}": int(
                item["id"]
            )
            for item in approved_rows
        }
        labels = st.multiselect(
            f"{_group_section_title(target_rule_type)}에서 적용할 후보",
            list(options.keys()),
            key=f"apply_select_{target_rule_type}",
        )
        selected_ids.extend(options[label] for label in labels)

    if grouped_candidates.get("UNKNOWN"):
        approved_unknown = [item for item in grouped_candidates["UNKNOWN"] if item["status"] == CANDIDATE_STATUS_APPROVED]
        if approved_unknown:
            st.warning("미분류 후보는 승인 상태여도 적용 대상에 포함되지 않습니다.")

    confirmed = st.checkbox("선택한 후보를 실제 활성 규칙으로 적용하는 것을 확인합니다.")
    if st.button("선택 후보 최종 적용", type="primary"):
        if not selected_ids:
            st.error("적용할 후보를 선택해 주세요.")
            return
        if not confirmed:
            st.error("최종 확인 체크가 필요합니다.")
            return
        try:
            applied_ids = policy_import_service.apply_candidates(candidate_ids=selected_ids)
            st.success(f"후보 {len(applied_ids)}건을 활성 규칙으로 적용했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _group_items_by_target_rule_type(items: list[dict]) -> dict[str, list[dict]]:
    grouped = {key: [] for key in GROUP_ORDER}
    for item in items:
        grouped.setdefault(str(item["target_rule_type"]), []).append(item)
    return grouped


def _group_section_title(target_rule_type: str) -> str:
    return {
        "POLICY_EVENT": "정책 이벤트 후보",
        "REGION_POLICY": "지역 규제 후보",
        "LOAN": "대출 규칙 후보",
        "TAX": "세금 규칙 후보",
        "BROKERAGE": "중개보수 규칙 후보",
        "UNKNOWN": "미분류 / 추가 검토 필요",
    }.get(target_rule_type, target_rule_type)


def _policy_import_label(item: dict) -> str:
    return (
        f"#{item['id']} | {_target_rule_type_label(str(item['target_rule_type']))} | "
        f"{item.get('source_name') or '이름 없음'} | {item['created_at']}"
    )


def _candidate_status_label(value: str) -> str:
    return {
        CANDIDATE_STATUS_PENDING_REVIEW: "검토 대기",
        CANDIDATE_STATUS_APPROVED: "승인",
        CANDIDATE_STATUS_REJECTED: "반려",
        CANDIDATE_STATUS_APPLIED: "적용 완료",
    }.get(value, value)


def _target_rule_type_label(value: str) -> str:
    return {
        "POLICY_EVENT": "정책 이벤트",
        "INTEGRATED": "통합 문서",
        "REGION_POLICY": "지역 규제",
        "LOAN": "대출",
        "TAX": "세금",
        "BROKERAGE": "중개보수",
        "UNKNOWN": "미분류",
    }.get(value, value)


def _region_policy_type_label(value: str) -> str:
    return {
        "REGULATED_AREA": "규제지역(기존 상위개념)",
        "NON_REGULATED_AREA": "비규제지역",
        "LAND_TRANSACTION_PERMISSION": "토지거래허가구역",
        "SPECULATION_OVERHEATED_DISTRICT": "투기과열지구",
        "ADJUSTMENT_TARGET_AREA": "조정대상지역",
    }.get(value, value)


def _region_level_label(value: str) -> str:
    return {
        "SIDO": "시도",
        "SIGUNGU": "시군구",
        "DONG": "동",
    }.get(value, value)


def _loan_region_type_label(value: str) -> str:
    return {
        "NON_REGULATED": "비규제지역",
        "REGULATED": "규제지역",
    }.get(value, value)


def _buyer_type_label(value: str) -> str:
    return {
        "NO_HOME": "무주택",
        "ONE_HOME": "1주택",
        "MULTI_HOME": "다주택",
    }.get(value, value)


def _investment_purpose_label(value: str) -> str:
    return {
        "OWNER_OCCUPIED": "실거주",
        "INVESTMENT": "투자",
    }.get(value, value)


def _review_state_label(value: str | None) -> str:
    return {
        None: "-",
        "READY": "준비 완료",
        "REVIEW_REQUIRED": "추가 확인 필요",
    }.get(value, str(value))


def _parse_region_lines(value: str) -> list[dict]:
    expanded_regions: list[dict] = []
    for raw_line in value.splitlines():
        line = " ".join(raw_line.strip().split())
        if not line:
            continue
        parts = line.split()
        if len(parts) == 1:
            expanded_regions.append({"region_level": "SIDO", "sido": parts[0], "sigungu": None, "dong": None})
        elif len(parts) == 2:
            expanded_regions.append({"region_level": "SIGUNGU", "sido": parts[0], "sigungu": parts[1], "dong": None})
        else:
            expanded_regions.append(
                {
                    "region_level": "DONG",
                    "sido": parts[0],
                    "sigungu": " ".join(parts[1:-1]),
                    "dong": parts[-1],
                }
            )
    return expanded_regions


def _format_region_line(item: dict) -> str:
    return " ".join(
        part
        for part in [
            str(item.get("sido") or "").strip(),
            str(item.get("sigungu") or "").strip(),
            str(item.get("dong") or "").strip(),
        ]
        if part
    )


def _format_confidence(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.0f}%"


def _loan_column_labels() -> dict[str, str]:
    return {
        "rule_version": "규칙 버전",
        "rule_name": "규칙 이름",
        "effective_from": "적용 시작일",
        "effective_to": "적용 종료일",
        "investment_purpose": "투자 목적",
        "region_type": "지역 유형",
        "buyer_type": "매수자 유형",
        "house_price_range": "주택 가격 구간",
        "ltv_rate": "LTV 비율",
        "dsr_rate": "DSR 비율",
        "max_loan_amount": "최대 대출 한도",
        "conditions": "조건",
        "description": "설명",
    }


def _tax_column_labels() -> dict[str, str]:
    return {
        "rule_version": "규칙 버전",
        "rule_name": "규칙 이름",
        "effective_from": "적용 시작일",
        "effective_to": "적용 종료일",
        "conditions": "조건",
        "rate_values": "세율 값",
        "limit_values": "한도 값",
        "description": "설명",
    }


def _brokerage_column_labels() -> dict[str, str]:
    return {
        "rule_version": "규칙 버전",
        "rule_name": "규칙 이름",
        "effective_from": "적용 시작일",
        "effective_to": "적용 종료일",
        "conditions": "조건",
        "rate_values": "비율 값",
        "limit_values": "한도 값",
        "description": "설명",
    }


def _region_policy_column_labels() -> dict[str, str]:
    return {
        "id": "ID",
        "region_scope": "적용 지역",
        "region_level": "지역 레벨",
        "sido": "시도",
        "sigungu": "시군구",
        "dong": "동",
        "policy_type": "정책 유형",
        "loan_region_type": "대출 지역 판정",
        "effective_from": "적용 시작일",
        "effective_to": "적용 종료일",
        "notes": "메모",
    }
