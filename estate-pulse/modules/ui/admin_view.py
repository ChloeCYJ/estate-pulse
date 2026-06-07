from __future__ import annotations

import json
from datetime import date

import pandas as pd
import streamlit as st

from modules.services.policy_import_service import (
    CANDIDATE_STATUS_APPLIED,
    CANDIDATE_STATUS_APPROVED,
    CANDIDATE_STATUS_PENDING_REVIEW,
    CANDIDATE_STATUS_REJECTED,
)
from modules.ui.policy_event_admin_view import render_policy_event_admin_page
from modules.utils.money_utils import format_compact_won, from_eok, to_eok


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
        _render_loan_rule_tab(rule_admin_service=rule_admin_service)
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


def _render_loan_rule_tab(*, rule_admin_service) -> None:
    st.subheader("대출 규칙")
    st.caption(
        "분석 계산에 직접 반영되는 대출 규칙입니다. 정책 이벤트는 참고 정보이므로 여기 등록된 룰과 분리됩니다."
    )

    _render_loan_rule_wizard(rule_admin_service=rule_admin_service)

    with st.expander("대출 규칙 수동 등록", expanded=False):
        st.caption(
            "예: 15~20억 미만 주택 대출을 4억으로 제한하려면 가격 하한 15, 가격 상한 미만 20, 최대 대출액 4를 입력하세요."
        )
        st.info("최종 예상 대출은 LTV 기준 대출, DSR 기준 한도, 최대 대출액 중 가장 낮은 금액으로 제한됩니다.")
        with st.container():
            version_options = ["자동 생성", *rule_admin_service.list_loan_rule_versions()]
            selected_existing_version = st.selectbox(
                "기존 rule_version 선택",
                version_options,
                index=0,
                help="같은 정책 묶음이면 같은 rule_version을 선택해서 이어서 등록할 수 있습니다.",
            )
            input_rule_version = st.text_input(
                "rule_version",
                value="",
                help="직접 입력하면 이 값을 사용합니다. 비우면 선택한 기존 rule_version 또는 자동 생성값을 사용합니다.",
            )
            st.caption("규칙 버전은 저장 시 자동 채번됩니다.")
            description = st.text_input("설명", value="관리자 수동 대출 규칙")

            date_col1, date_col2 = st.columns(2)
            effective_from = date_col1.date_input("적용 시작일")
            use_end_date = date_col2.checkbox("종료일 입력", key="manual_loan_use_end_date")
            effective_to = st.date_input("적용 종료일") if use_end_date else None

            condition_col1, condition_col2, condition_col3 = st.columns(3)
            region_type = condition_col1.selectbox(
                "지역 유형",
                rule_admin_service.list_loan_region_types(),
                format_func=_loan_region_type_label,
            )
            buyer_type = condition_col2.selectbox(
                "매수자 유형",
                ["ALL", "NO_HOME", "ONE_HOME", "MULTI_HOME"],
                format_func=_buyer_type_label,
            )
            purpose = condition_col3.selectbox(
                "목적",
                ["OWNER_OCCUPIED", "INVESTMENT"],
                format_func=_investment_purpose_label,
            )

            price_col1, price_col2, price_col3 = st.columns(3)
            house_price_min_eok = price_col1.number_input(
                "가격 하한 (억 원)",
                min_value=0.0,
                value=20.0,
                step=0.1,
                format="%.2f",
            )
            use_price_max = price_col2.checkbox("가격 상한 미만 입력")
            house_price_max_exclusive_eok = price_col2.number_input(
                "가격 상한 미만 (억 원)",
                min_value=0.0,
                value=20.0,
                step=0.1,
                format="%.2f",
                disabled=not use_price_max,
                help="체크하지 않으면 가격 상한 없이 저장합니다. 체크하면 입력 금액 미만까지 적용됩니다.",
            )
            unlimited_max_loan = price_col3.checkbox("최대 대출액 제한 없음")
            max_loan_amount_eok = price_col3.number_input(
                "최대 대출액 (억 원)",
                min_value=0.0,
                value=2.0,
                step=0.1,
                format="%.2f",
                disabled=unlimited_max_loan,
                help="0을 입력하면 0원 대출 제한으로 저장됩니다. 제한 없음은 아래 체크박스를 사용하세요.",
            )

            ratio_col1, ratio_col2 = st.columns(2)
            ltv_rate = ratio_col1.number_input(
                "LTV",
                min_value=0.0,
                max_value=1.0,
                value=0.6,
                step=0.05,
                format="%.2f",
            )
            dsr_rate = ratio_col2.number_input(
                "DSR",
                min_value=0.0,
                max_value=1.0,
                value=0.4,
                step=0.05,
                format="%.2f",
            )

            submitted = st.button("대출 규칙 저장")

        if submitted:
            try:
                rule_version = input_rule_version.strip()
                if not rule_version and selected_existing_version != "자동 생성":
                    rule_version = selected_existing_version
                rule_admin_service.create_manual_loan_rule(
                    rule_version=rule_version,
                    effective_from=effective_from.isoformat(),
                    effective_to=effective_to.isoformat() if effective_to else None,
                    region_type=region_type,
                    buyer_type=buyer_type,
                    purpose=purpose,
                    house_price_min=int(from_eok(house_price_min_eok)),
                    house_price_max=(
                        int(from_eok(house_price_max_exclusive_eok)) - 1
                        if use_price_max
                        else None
                    ),
                    ltv_rate=float(ltv_rate),
                    dsr_rate=float(dsr_rate),
                    max_loan_amount=(
                        None if unlimited_max_loan else int(from_eok(max_loan_amount_eok))
                    ),
                    description=description,
                )
                st.success("대출 규칙을 저장하고 계산 룰에 반영했습니다.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    editable_rules = {
        int(item["candidate_id"]): item for item in rule_admin_service.list_editable_loan_rules()
    }
    st.subheader("현재 적용 대출 규칙 조회")
    with st.form("loan_rule_query_form"):
        filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)
        query_purpose = filter_col1.selectbox(
            "목적",
            ["전체", "OWNER_OCCUPIED", "INVESTMENT"],
            format_func=lambda value: "전체" if value == "전체" else _investment_purpose_label(value),
            key="loan_rule_query_purpose",
        )
        query_region_type = filter_col2.selectbox(
            "지역 유형",
            [
                "전체",
                "NON_REGULATED",
                "REGULATED",
                "SPECULATION_OVERHEATED_DISTRICT",
                "ADJUSTMENT_TARGET_AREA",
                "LAND_TRANSACTION_PERMISSION",
            ],
            format_func=lambda value: "전체" if value == "전체" else _loan_region_type_label(value),
            key="loan_rule_query_region_type",
        )
        query_buyer_type = filter_col3.selectbox(
            "매수자 유형",
            ["전체", "NO_HOME", "ONE_HOME", "MULTI_HOME"],
            format_func=lambda value: "전체" if value == "전체" else _buyer_type_label(value),
            key="loan_rule_query_buyer_type",
        )
        query_rule_version = filter_col4.selectbox(
            "rule_version",
            ["전체", *rule_admin_service.list_loan_rule_versions()],
            key="loan_rule_query_rule_version",
        )
        query_house_price_enabled = filter_col5.checkbox(
            "주택 가격 입력",
            key="loan_rule_query_house_price_enabled",
        )
        query_house_price_eok = filter_col5.number_input(
            "주택 가격(억 원)",
            min_value=0.0,
            value=19.0,
            step=0.1,
            format="%.2f",
            disabled=not query_house_price_enabled,
            key="loan_rule_query_house_price",
        )
        query_submitted = st.form_submit_button("현재 적용 룰 조회")

    if query_submitted:
        st.session_state["loan_rule_query_filters"] = {
            "purpose": None if query_purpose == "전체" else query_purpose,
            "region_type": None if query_region_type == "전체" else query_region_type,
            "buyer_type": None if query_buyer_type == "전체" else query_buyer_type,
            "rule_version": None if query_rule_version == "전체" else query_rule_version,
            "house_price": int(from_eok(query_house_price_eok)) if query_house_price_enabled else None,
        }

    query_filters = st.session_state.get("loan_rule_query_filters")
    loan_rule_rows: list[dict] = []
    if query_filters is None:
        st.info("목적, 지역 유형, 매수자 유형, 주택 가격, rule_version 조건을 선택한 뒤 조회하세요.")
    else:
        loan_rule_rows = rule_admin_service.query_current_loan_rules(
            purpose=query_filters["purpose"],
            region_type=query_filters["region_type"],
            buyer_type=query_filters["buyer_type"],
            house_price=query_filters["house_price"],
            rule_version=query_filters["rule_version"],
            reference_date=date.today(),
        )
        if loan_rule_rows:
            st.caption(_loan_rule_query_summary(query_filters))
            query_conflicts = _current_query_conflicts(loan_rule_rows)
            if query_conflicts:
                st.warning("동일 조건에 적용 가능한 룰이 2건 이상 있습니다. rule_version 또는 적용기간을 확인하세요.")
            query_selection = st.dataframe(
                pd.DataFrame(
                    [
                        {key: value for key, value in row.items() if not key.startswith("_")}
                        for row in loan_rule_rows
                    ]
                ).rename(columns=_loan_column_labels()),
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row",
                key="loan_rule_query_result_table",
            )
            selected_query_rows = query_selection.selection.rows
            selected_query_summaries = [loan_rule_rows[int(index)] for index in selected_query_rows]
            st.session_state["loan_rule_query_selected_candidate_ids"] = [
                int(row["_candidate_id"])
                for row in selected_query_summaries
                if row.get("_candidate_id") is not None
            ]
            if len(selected_query_summaries) == 1:
                st.markdown("#### 선택한 규칙 수정")
                _render_loan_rule_editor(
                    selected_summary=selected_query_summaries[0],
                    editable_rules=editable_rules,
                    rule_admin_service=rule_admin_service,
                    key_prefix="query_result",
                )
            elif len(selected_query_summaries) > 1:
                _render_selected_loan_rule_batch_actions(
                    selected_rows=selected_query_summaries,
                    rule_admin_service=rule_admin_service,
                    title="선택한 규칙 일괄 변경",
                    key_prefix="query_selected",
                )
        else:
            st.info("해당 조건에 현재 적용 가능한 대출규칙이 없습니다.")

    with st.expander("전체 현재 적용 룰 보기", expanded=False):
        st.caption("전체 룰 목록은 검증 또는 운영 점검용입니다.")
        list_mode = st.radio(
            "목록 보기",
            ["현재 적용 룰", "전체 보기"],
            horizontal=True,
            key="loan_rule_list_mode",
        )
        current_only = list_mode == "현재 적용 룰"
        all_loan_rule_rows = rule_admin_service.list_loan_rules(
            reference_date=date.today(),
            current_only=current_only,
        )
        if not current_only:
            state_filters = st.multiselect(
                "상태 필터",
                ["현재 적용", "비활성/만료", "예정"],
                default=["현재 적용", "비활성/만료", "예정"],
                key="loan_rule_state_filters",
            )
            all_loan_rule_rows = [row for row in all_loan_rule_rows if row["state"] in state_filters]
        if not all_loan_rule_rows:
            st.info("표시할 대출 규칙이 없습니다.")
        else:
            conflicts = rule_admin_service.list_loan_rule_conflicts(reference_date=date.today())
            if conflicts:
                st.warning("동일 조건에 현재 적용 가능한 대출규칙이 2건 이상 있습니다. 수정 또는 비활성화가 필요합니다.")
                st.dataframe(pd.DataFrame(conflicts), use_container_width=True, hide_index=True)
            _render_grouped_loan_rule_sections(
                all_loan_rule_rows,
                show_effective_dates=not current_only,
            )

    _render_loan_rule_batch_edit(rule_admin_service=rule_admin_service)

    with st.expander("고급: 규칙 ID 기준 수정/삭제", expanded=False):
        selected_summary = None
        if not loan_rule_rows:
            st.caption("조회 결과가 있을 때 선택 후 수정/삭제할 수 있습니다.")
        else:
            loan_rule_df = pd.DataFrame(
                [
                    {key: value for key, value in row.items() if not key.startswith("_")}
                    for row in loan_rule_rows
                ]
            ).rename(columns=_loan_column_labels())
            selection = st.dataframe(
                loan_rule_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row",
                key="active_loan_rules_table",
            )
            selected_rows = selection.selection.rows
            displayed_editable_candidate_ids = [
                int(row["_candidate_id"])
                for row in loan_rule_rows
                if row.get("_editable") and row.get("_candidate_id") is not None
            ]
            if not selected_rows and displayed_editable_candidate_ids:
                delete_all_confirmed = st.checkbox(
                    f"현재 표시된 적용 규칙 전체 {len(displayed_editable_candidate_ids)}개 삭제를 확인합니다.",
                    key="delete_all_displayed_loan_rules_confirm",
                )
                if st.button("현재 표시된 적용 규칙 전체 삭제", key="delete_all_displayed_loan_rules"):
                    if not delete_all_confirmed:
                        st.error("전체 삭제 확인 체크가 필요합니다.")
                    else:
                        deleted_count = rule_admin_service.delete_applied_loan_rules(
                            displayed_editable_candidate_ids
                        )
                        st.success(f"대출 규칙 {deleted_count}개를 삭제했습니다.")
                        st.rerun()

            if not selected_rows:
                st.caption("1개 선택 시 수정, 여러 개 선택 시 일괄 삭제를 할 수 있습니다.")
            else:
                selected_summaries = [loan_rule_rows[int(index)] for index in selected_rows]
                selected_editable_candidate_ids = [
                    int(row["_candidate_id"])
                    for row in selected_summaries
                    if row.get("_editable") and row.get("_candidate_id") is not None
                ]

                if len(selected_rows) > 1:
                    selected_builtin_count = len(selected_rows) - len(selected_editable_candidate_ids)
                    st.caption("여러 규칙을 선택했습니다. 선택한 적용 규칙만 한 번에 삭제할 수 있습니다.")
                    if not selected_editable_candidate_ids:
                        st.caption("선택한 항목이 모두 기본 내장 규칙이라 일괄 삭제 버튼은 표시되지 않습니다.")
                        st.caption("기본 내장 규칙은 삭제 대신 1개 선택 후 override로 대체해 주세요.")
                    else:
                        if selected_builtin_count > 0:
                            st.caption(
                                f"선택한 {len(selected_rows)}개 중 {len(selected_editable_candidate_ids)}개만 삭제 대상입니다. "
                                f"기본 내장 규칙 {selected_builtin_count}개는 유지됩니다."
                            )
                        bulk_delete_confirmed = st.checkbox(
                            f"선택한 적용 규칙 {len(selected_editable_candidate_ids)}개 삭제를 확인합니다.",
                            key="delete_selected_loan_rules_confirm",
                        )
                        if st.button("선택 규칙 일괄 삭제", key="delete_selected_loan_rules"):
                            if not bulk_delete_confirmed:
                                st.error("일괄 삭제 확인 체크가 필요합니다.")
                            else:
                                deleted_count = rule_admin_service.delete_applied_loan_rules(
                                    selected_editable_candidate_ids
                                )
                                st.success(f"대출 규칙 {deleted_count}개를 삭제했습니다.")
                                st.rerun()

                if len(selected_rows) == 1:
                    selected_summary = loan_rule_rows[int(selected_rows[0])]
        if selected_summary is None:
            return
        _render_loan_rule_editor(
            selected_summary=selected_summary,
            editable_rules=editable_rules,
            rule_admin_service=rule_admin_service,
            key_prefix="advanced",
        )

def _render_loan_rule_wizard(*, rule_admin_service) -> None:
    with st.expander("Loan Rule Wizard", expanded=False):
        st.caption("공통 조건을 한 번 입력하고 가격구간별 row를 한 번에 생성합니다.")
        version_options = ["자동 생성", *rule_admin_service.list_loan_rule_versions()]
        version_col1, version_col2 = st.columns(2)
        selected_existing_version = version_col1.selectbox(
            "기존 rule_version 선택",
            version_options,
            index=0,
            key="loan_wizard_existing_version",
        )
        input_rule_version = version_col2.text_input(
            "rule_version",
            value="",
            key="loan_wizard_rule_version",
        )
        common_col1, common_col2, common_col3, common_col4 = st.columns(4)
        purpose = common_col1.selectbox(
            "목적",
            ["OWNER_OCCUPIED", "INVESTMENT"],
            format_func=_investment_purpose_label,
            key="loan_wizard_purpose",
        )
        region_type = common_col2.selectbox(
            "지역 유형",
            rule_admin_service.list_loan_region_types(),
            format_func=_loan_region_type_label,
            key="loan_wizard_region_type",
        )
        buyer_type = common_col3.selectbox(
            "매수자 유형",
            ["ALL", "NO_HOME", "ONE_HOME", "MULTI_HOME"],
            format_func=_buyer_type_label,
            key="loan_wizard_buyer_type",
        )
        description = common_col4.text_input(
            "설명",
            value="관리자 Wizard 대출 규칙",
            key="loan_wizard_description",
        )
        date_col1, date_col2 = st.columns(2)
        effective_from = date_col1.date_input("적용 시작일", key="loan_wizard_effective_from")
        use_end_date = date_col2.checkbox("종료일 입력", key="loan_wizard_use_end_date")
        effective_to = (
            date_col2.date_input("적용 종료일", key="loan_wizard_effective_to")
            if use_end_date
            else None
        )

        st.markdown("##### 가격구간 매트릭스")
        st.caption("기본 4개 가격구간이 자동으로 채워집니다. 필요한 row만 선택해 저장할 수 있습니다.")
        matrix_rows: list[dict] = []
        for index, default_band in enumerate(rule_admin_service.list_default_loan_price_bands()):
            st.markdown(f"**구간 {index + 1}**")
            row_col1, row_col2, row_col3, row_col4 = st.columns(4)
            enabled = row_col1.checkbox("사용", value=True, key=f"loan_wizard_enabled_{index}")
            house_price_min_eok = row_col2.number_input(
                "가격 하한(억 원)",
                min_value=0.0,
                value=to_eok(default_band["house_price_min"]),
                step=0.1,
                format="%.2f",
                key=f"loan_wizard_min_{index}",
            )
            use_price_max = row_col3.checkbox(
                "가격 상한 미만 입력",
                value=default_band["house_price_max"] is not None,
                key=f"loan_wizard_use_max_{index}",
            )
            house_price_max_eok = row_col4.number_input(
                "가격 상한 미만(억 원)",
                min_value=0.0,
                value=(
                    to_eok(int(default_band["house_price_max"]) + 1)
                    if default_band["house_price_max"] is not None
                    else to_eok(default_band["house_price_min"])
                ),
                step=0.1,
                format="%.2f",
                disabled=not use_price_max,
                key=f"loan_wizard_max_{index}",
            )
            ratio_col1, ratio_col2, ratio_col3, ratio_col4 = st.columns(4)
            ltv_rate = ratio_col1.number_input(
                "LTV",
                min_value=0.0,
                max_value=1.0,
                value=0.6,
                step=0.05,
                format="%.2f",
                key=f"loan_wizard_ltv_{index}",
            )
            dsr_rate = ratio_col2.number_input(
                "DSR",
                min_value=0.0,
                max_value=1.0,
                value=0.4,
                step=0.05,
                format="%.2f",
                key=f"loan_wizard_dsr_{index}",
            )
            unlimited_max_loan = ratio_col3.checkbox(
                "최대 대출액 제한 없음",
                value=True,
                key=f"loan_wizard_unlimited_{index}",
            )
            max_loan_amount_eok = ratio_col4.number_input(
                "최대 대출액(억 원)",
                min_value=0.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                disabled=unlimited_max_loan,
                key=f"loan_wizard_max_loan_{index}",
            )
            if enabled:
                matrix_rows.append(
                    {
                        "house_price_min": int(from_eok(house_price_min_eok)),
                        "house_price_max": (
                            int(from_eok(house_price_max_eok)) - 1 if use_price_max else None
                        ),
                        "ltv_rate": float(ltv_rate),
                        "dsr_rate": float(dsr_rate),
                        "max_loan_amount": (
                            None if unlimited_max_loan else int(from_eok(max_loan_amount_eok))
                        ),
                    }
                )

        if st.button("생성 예정 룰 미리보기", key="loan_wizard_preview"):
            try:
                rule_version = input_rule_version.strip()
                if not rule_version and selected_existing_version != "자동 생성":
                    rule_version = selected_existing_version
                st.session_state["loan_rule_wizard_preview"] = rule_admin_service.preview_manual_loan_rule_batch(
                    rule_version=rule_version,
                    effective_from=effective_from.isoformat(),
                    effective_to=effective_to.isoformat() if effective_to else None,
                    region_type=region_type,
                    buyer_type=buyer_type,
                    purpose=purpose,
                    description=description,
                    matrix_rows=matrix_rows,
                )
            except Exception as exc:
                st.error(str(exc))

        preview = st.session_state.get("loan_rule_wizard_preview")
        if preview:
            st.caption(f"생성 예정 row 수: {preview['row_count']}건")
            if preview["warnings"]:
                for warning in preview["warnings"]:
                    st.warning(warning)
            st.dataframe(
                pd.DataFrame(preview["preview_rows"]).rename(
                    columns={
                        "rule_version": "규칙 버전",
                        "purpose": "목적",
                        "region_type": "지역 유형",
                        "buyer_type": "매수자 유형",
                        "house_price_range": "주택 가격 구간",
                        "ltv_rate": "LTV",
                        "dsr_rate": "DSR",
                        "max_loan_amount": "최대 대출 한도",
                        "effective_from": "적용 시작일",
                        "effective_to": "적용 종료일",
                        "duplicate_in_batch": "Wizard 중복",
                        "current_overlap_count": "현재 적용 중복 수",
                        "current_overlap": "현재 적용 룰 존재",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
            confirmed = st.checkbox(
                "Preview를 확인했고 생성 예정 룰을 저장합니다.",
                key="loan_wizard_confirm",
            )
            if st.button("Wizard 저장", key="loan_wizard_save"):
                if not confirmed:
                    st.error("저장 확인 체크가 필요합니다.")
                else:
                    try:
                        created_ids = rule_admin_service.create_manual_loan_rule_rows(preview["rows"])
                        st.session_state.pop("loan_rule_wizard_preview", None)
                        st.success(f"대출 규칙 {len(created_ids)}개를 생성했습니다.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


def _render_loan_rule_batch_edit(*, rule_admin_service) -> None:
    with st.expander("일괄 변경 / 일괄 종료 처리", expanded=False):
        editable_rows = rule_admin_service.list_editable_loan_rules()
        if not editable_rows:
            st.caption("일괄 작업 가능한 관리자 적용/override 규칙이 없습니다.")
            return

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        version_options = ["전체", *sorted({str(item["rule_version"]) for item in editable_rows})]
        purpose_options = ["전체", "OWNER_OCCUPIED", "INVESTMENT"]
        region_options = ["전체", *rule_admin_service.list_loan_region_types()]
        buyer_options = ["전체", "ALL", "NO_HOME", "ONE_HOME", "MULTI_HOME"]
        bulk_rule_version_filter = filter_col1.selectbox("규칙 버전", version_options, key="bulk_rule_version_filter")
        bulk_purpose_filter = filter_col2.selectbox("목적", purpose_options, key="bulk_purpose_filter")
        bulk_region_filter = filter_col3.selectbox("지역 유형", region_options, key="bulk_region_filter")
        bulk_buyer_filter = filter_col4.selectbox("매수자 유형", buyer_options, key="bulk_buyer_filter")
        filter_col5, filter_col6, filter_col7 = st.columns(3)
        bulk_state_filter = filter_col5.selectbox(
            "대상 상태",
            ["전체", "현재 적용", "비활성/만료"],
            key="bulk_state_filter",
        )
        bulk_use_effective_from_filter = filter_col6.checkbox(
            "적용 시작일 필터",
            key="bulk_use_effective_from_filter",
        )
        bulk_effective_from_filter = filter_col6.date_input(
            "적용 시작일",
            value=date.today(),
            disabled=not bulk_use_effective_from_filter,
            key="bulk_effective_from_filter",
        )
        bulk_use_effective_to_filter = filter_col7.checkbox(
            "적용 종료일 필터",
            key="bulk_use_effective_to_filter",
        )
        bulk_effective_to_filter = filter_col7.date_input(
            "적용 종료일",
            value=date.today(),
            disabled=not bulk_use_effective_to_filter,
            key="bulk_effective_to_filter",
        )

        filtered_bulk_rows = rule_admin_service.filter_editable_loan_rules(
            rule_version=None if bulk_rule_version_filter == "전체" else bulk_rule_version_filter,
            purpose=None if bulk_purpose_filter == "전체" else bulk_purpose_filter,
            region_type=None if bulk_region_filter == "전체" else bulk_region_filter,
            buyer_type=None if bulk_buyer_filter == "전체" else bulk_buyer_filter,
            effective_from=bulk_effective_from_filter.isoformat() if bulk_use_effective_from_filter else None,
            effective_to=bulk_effective_to_filter.isoformat() if bulk_use_effective_to_filter else None,
            current_only=None,
            state=None if bulk_state_filter == "전체" else bulk_state_filter,
            reference_date=date.today(),
        )
        st.caption(f"대상 규칙 {len(filtered_bulk_rows)}건")
        if not filtered_bulk_rows:
            return

        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "rule_version": item["rule_version"],
                        "purpose": _investment_purpose_label(item["purpose"]),
                        "region_type": _loan_region_type_label(item["region_type"]),
                        "buyer_type": _buyer_type_label(item["buyer_type"]),
                        "house_price_range": _loan_house_price_range_label(item),
                        "ltv_rate": f"{float(item['ltv_rate']) * 100:.1f}%",
                        "dsr_rate": f"{float(item['dsr_rate']) * 100:.1f}%",
                        "max_loan_amount": _bulk_max_loan_label(item["max_loan_amount"]),
                        "state": item["state"],
                        "effective_from": item["effective_from"],
                        "effective_to": item["effective_to"] or "-",
                    }
                    for item in filtered_bulk_rows
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

        bulk_action = st.radio(
            "일괄 작업",
            ["일괄 수정", "일괄 종료 처리"],
            horizontal=True,
            key="bulk_loan_action",
        )
        preview_payload: dict | None = None
        candidate_ids = [int(item["candidate_id"]) for item in filtered_bulk_rows]
        if bulk_action == "일괄 종료 처리":
            st.caption("선택한 룰을 지정한 날짜 이후 현재 계산에서 제외합니다.")
            bulk_deactivate_from = st.date_input(
                "종료 처리 기준일",
                value=date.today(),
                key="bulk_deactivate_from",
            )
            try:
                preview_payload = rule_admin_service.preview_bulk_update_applied_loan_rules(
                    candidate_ids=candidate_ids,
                    deactivate_from=bulk_deactivate_from.isoformat(),
                )
            except Exception as exc:
                st.error(str(exc))
        else:
            bulk_change_col1, bulk_change_col2, bulk_change_col3 = st.columns(3)
            bulk_change_ltv = bulk_change_col1.checkbox("LTV 변경", key="bulk_change_ltv")
            bulk_ltv_rate = bulk_change_col1.number_input(
                "변경 LTV",
                min_value=0.0,
                max_value=1.0,
                value=0.4,
                step=0.05,
                format="%.2f",
                disabled=not bulk_change_ltv,
                key="bulk_ltv_rate",
            )
            bulk_change_dsr = bulk_change_col2.checkbox("DSR 변경", key="bulk_change_dsr")
            bulk_dsr_rate = bulk_change_col2.number_input(
                "변경 DSR",
                min_value=0.0,
                max_value=1.0,
                value=0.4,
                step=0.05,
                format="%.2f",
                disabled=not bulk_change_dsr,
                key="bulk_dsr_rate",
            )
            bulk_change_max_loan = bulk_change_col3.checkbox("최대 대출액 변경", key="bulk_change_max_loan")
            bulk_max_loan_unlimited = bulk_change_col3.checkbox(
                "제한 없음",
                key="bulk_max_loan_unlimited",
                disabled=not bulk_change_max_loan,
            )
            bulk_max_loan_amount = bulk_change_col3.number_input(
                "변경 최대 대출액(억 원)",
                min_value=0.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                disabled=not bulk_change_max_loan or bulk_max_loan_unlimited,
                key="bulk_max_loan_amount",
            )
            bulk_change_version = st.checkbox("rule_version 변경", key="bulk_change_version")
            bulk_rule_version = st.text_input(
                "변경 rule_version",
                value="",
                disabled=not bulk_change_version,
                key="bulk_rule_version",
            )
            bulk_date_col1, bulk_date_col2 = st.columns(2)
            bulk_change_effective_from = bulk_date_col1.checkbox("적용 시작일 변경", key="bulk_change_effective_from")
            bulk_effective_from = bulk_date_col1.date_input(
                "변경 적용 시작일",
                value=date.today(),
                disabled=not bulk_change_effective_from,
                key="bulk_effective_from",
            )
            bulk_change_effective_to = bulk_date_col2.checkbox("적용 종료일 변경", key="bulk_change_effective_to")
            bulk_use_effective_to = bulk_date_col2.checkbox(
                "종료일 값 입력",
                disabled=not bulk_change_effective_to,
                key="bulk_use_effective_to",
            )
            bulk_effective_to = bulk_date_col2.date_input(
                "변경 적용 종료일",
                value=date.today(),
                disabled=not bulk_change_effective_to or not bulk_use_effective_to,
                key="bulk_effective_to",
            )
            bulk_change_description = st.checkbox("설명 변경", key="bulk_change_description")
            bulk_description = st.text_input(
                "변경 설명",
                value="",
                disabled=not bulk_change_description,
                key="bulk_description",
            )
            try:
                preview_payload = rule_admin_service.preview_bulk_update_applied_loan_rules(
                    candidate_ids=candidate_ids,
                    rule_version=bulk_rule_version.strip() if bulk_change_version and bulk_rule_version.strip() else None,
                    ltv_rate=bulk_ltv_rate if bulk_change_ltv else None,
                    dsr_rate=bulk_dsr_rate if bulk_change_dsr else None,
                    max_loan_amount_changed=bulk_change_max_loan,
                    max_loan_amount=(
                        None if bulk_max_loan_unlimited else int(from_eok(bulk_max_loan_amount))
                    ),
                    effective_from_changed=bulk_change_effective_from,
                    effective_from=bulk_effective_from.isoformat(),
                    effective_to_changed=bulk_change_effective_to,
                    effective_to=bulk_effective_to.isoformat() if bulk_use_effective_to else None,
                    description=bulk_description.strip() if bulk_change_description and bulk_description.strip() else None,
                )
            except ValueError:
                preview_payload = None
                st.caption("변경할 항목을 선택하면 Preview가 표시됩니다.")
            except Exception as exc:
                preview_payload = None
                st.error(str(exc))

        if preview_payload:
            st.caption(f"Preview 대상 {preview_payload['row_count']}건")
            st.dataframe(
                pd.DataFrame(preview_payload["rows"]).rename(
                    columns={
                        "candidate_id": "후보 ID",
                        "buyer_type": "매수자 유형",
                        "house_price_range": "주택 가격 구간",
                        "before_rule_version": "변경 전 rule_version",
                        "after_rule_version": "변경 후 rule_version",
                        "before_ltv_rate": "변경 전 LTV",
                        "after_ltv_rate": "변경 후 LTV",
                        "before_dsr_rate": "변경 전 DSR",
                        "after_dsr_rate": "변경 후 DSR",
                        "before_max_loan_amount": "변경 전 최대 대출액",
                        "after_max_loan_amount": "변경 후 최대 대출액",
                        "before_effective_from": "변경 전 시작일",
                        "after_effective_from": "변경 후 시작일",
                        "before_effective_to": "변경 전 종료일",
                        "after_effective_to": "변경 후 종료일",
                        "before_description": "변경 전 설명",
                        "after_description": "변경 후 설명",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
            bulk_confirmed = st.checkbox(
                "Preview를 확인했고 일괄 작업을 적용합니다.",
                key="bulk_update_confirm",
            )
            action_label = "일괄 종료 처리" if bulk_action == "일괄 종료 처리" else "일괄 변경 적용"
            if st.button(action_label, key="bulk_update_apply"):
                if not bulk_confirmed:
                    st.error("일괄 작업 확인 체크가 필요합니다.")
                else:
                    try:
                        if bulk_action == "일괄 종료 처리":
                            updated_count = rule_admin_service.deactivate_applied_loan_rules(
                                candidate_ids=candidate_ids,
                                inactive_from=bulk_deactivate_from.isoformat(),
                            )
                            st.success(f"대출 규칙 {updated_count}개를 일괄 종료 처리했습니다.")
                        else:
                            updated_count = rule_admin_service.bulk_update_applied_loan_rules(
                                candidate_ids=candidate_ids,
                                rule_version=bulk_rule_version.strip() if bulk_change_version and bulk_rule_version.strip() else None,
                                ltv_rate=bulk_ltv_rate if bulk_change_ltv else None,
                                dsr_rate=bulk_dsr_rate if bulk_change_dsr else None,
                                max_loan_amount_changed=bulk_change_max_loan,
                                max_loan_amount=(
                                    None if bulk_max_loan_unlimited else int(from_eok(bulk_max_loan_amount))
                                ),
                                effective_from_changed=bulk_change_effective_from,
                                effective_from=bulk_effective_from.isoformat(),
                                effective_to_changed=bulk_change_effective_to,
                                effective_to=bulk_effective_to.isoformat() if bulk_use_effective_to else None,
                                description=bulk_description.strip() if bulk_change_description and bulk_description.strip() else None,
                            )
                            st.success(f"대출 규칙 {updated_count}개를 일괄 변경했습니다.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


def _render_selected_loan_rule_batch_actions(
    *,
    selected_rows: list[dict],
    rule_admin_service,
    title: str,
    key_prefix: str,
) -> None:
    st.markdown(f"#### {title}")
    st.caption(f"선택한 {len(selected_rows)}개 규칙에만 일괄 작업을 적용합니다.")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "rule_version": item["rule_version"],
                    "purpose": item["investment_purpose"],
                    "region_type": item["region_type"],
                    "buyer_type": item["buyer_type"],
                    "house_price_range": item["house_price_range"],
                    "ltv_rate": item["ltv_rate"],
                    "dsr_rate": item["dsr_rate"],
                    "max_loan_amount": item["max_loan_amount"],
                }
                for item in selected_rows
            ]
        ).rename(
            columns={
                "rule_version": "규칙 버전",
                "purpose": "목적",
                "region_type": "지역 유형",
                "buyer_type": "매수자 유형",
                "house_price_range": "주택 가격 구간",
                "ltv_rate": "LTV",
                "dsr_rate": "DSR",
                "max_loan_amount": "최대 대출 한도",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    bulk_action = st.radio(
        "선택 규칙 작업",
        ["일괄 수정", "일괄 종료 처리"],
        horizontal=True,
        key=f"{key_prefix}_bulk_action",
    )
    candidate_ids = [
        int(item["_candidate_id"])
        for item in selected_rows
        if item.get("_candidate_id") is not None
    ]
    if len(candidate_ids) != len(selected_rows):
        st.caption("기본 내장 규칙이 포함되어 있어 선택한 적용 규칙만 일괄 변경/종료 처리할 수 있습니다.")
    if not candidate_ids:
        return

    preview_payload: dict | None = None
    if bulk_action == "일괄 종료 처리":
        deactivate_from = st.date_input(
            "종료 처리 기준일",
            value=date.today(),
            key=f"{key_prefix}_deactivate_from",
        )
        preview_payload = rule_admin_service.preview_bulk_update_applied_loan_rules(
            candidate_ids=candidate_ids,
            deactivate_from=deactivate_from.isoformat(),
        )
    else:
        bulk_change_col1, bulk_change_col2, bulk_change_col3 = st.columns(3)
        bulk_change_ltv = bulk_change_col1.checkbox("LTV 변경", key=f"{key_prefix}_change_ltv")
        bulk_ltv_rate = bulk_change_col1.number_input(
            "변경 LTV",
            min_value=0.0,
            max_value=1.0,
            value=0.4,
            step=0.05,
            format="%.2f",
            disabled=not bulk_change_ltv,
            key=f"{key_prefix}_ltv_rate",
        )
        bulk_change_dsr = bulk_change_col2.checkbox("DSR 변경", key=f"{key_prefix}_change_dsr")
        bulk_dsr_rate = bulk_change_col2.number_input(
            "변경 DSR",
            min_value=0.0,
            max_value=1.0,
            value=0.4,
            step=0.05,
            format="%.2f",
            disabled=not bulk_change_dsr,
            key=f"{key_prefix}_dsr_rate",
        )
        bulk_change_max_loan = bulk_change_col3.checkbox("최대 대출액 변경", key=f"{key_prefix}_change_max_loan")
        bulk_max_loan_unlimited = bulk_change_col3.checkbox(
            "제한 없음",
            key=f"{key_prefix}_max_loan_unlimited",
            disabled=not bulk_change_max_loan,
        )
        bulk_max_loan_amount = bulk_change_col3.number_input(
            "변경 최대 대출액(억 원)",
            min_value=0.0,
            value=0.0,
            step=0.1,
            format="%.2f",
            disabled=not bulk_change_max_loan or bulk_max_loan_unlimited,
            key=f"{key_prefix}_max_loan_amount",
        )
        bulk_change_version = st.checkbox("rule_version 변경", key=f"{key_prefix}_change_version")
        bulk_rule_version = st.text_input(
            "변경 rule_version",
            value="",
            disabled=not bulk_change_version,
            key=f"{key_prefix}_rule_version",
        )
        bulk_date_col1, bulk_date_col2 = st.columns(2)
        bulk_change_effective_from = bulk_date_col1.checkbox("적용 시작일 변경", key=f"{key_prefix}_change_effective_from")
        bulk_effective_from = bulk_date_col1.date_input(
            "변경 적용 시작일",
            value=date.today(),
            disabled=not bulk_change_effective_from,
            key=f"{key_prefix}_effective_from",
        )
        bulk_change_effective_to = bulk_date_col2.checkbox("적용 종료일 변경", key=f"{key_prefix}_change_effective_to")
        bulk_use_effective_to = bulk_date_col2.checkbox(
            "종료일 값 입력",
            disabled=not bulk_change_effective_to,
            key=f"{key_prefix}_use_effective_to",
        )
        bulk_effective_to = bulk_date_col2.date_input(
            "변경 적용 종료일",
            value=date.today(),
            disabled=not bulk_change_effective_to or not bulk_use_effective_to,
            key=f"{key_prefix}_effective_to",
        )
        bulk_change_description = st.checkbox("설명 변경", key=f"{key_prefix}_change_description")
        bulk_description = st.text_input(
            "변경 설명",
            value="",
            disabled=not bulk_change_description,
            key=f"{key_prefix}_description",
        )
        try:
            preview_payload = rule_admin_service.preview_bulk_update_applied_loan_rules(
                candidate_ids=candidate_ids,
                rule_version=bulk_rule_version.strip() if bulk_change_version and bulk_rule_version.strip() else None,
                ltv_rate=bulk_ltv_rate if bulk_change_ltv else None,
                dsr_rate=bulk_dsr_rate if bulk_change_dsr else None,
                max_loan_amount_changed=bulk_change_max_loan,
                max_loan_amount=None if bulk_max_loan_unlimited else int(from_eok(bulk_max_loan_amount)),
                effective_from_changed=bulk_change_effective_from,
                effective_from=bulk_effective_from.isoformat(),
                effective_to_changed=bulk_change_effective_to,
                effective_to=bulk_effective_to.isoformat() if bulk_use_effective_to else None,
                description=bulk_description.strip() if bulk_change_description and bulk_description.strip() else None,
            )
        except ValueError:
            preview_payload = None
            st.caption("변경할 항목을 선택하면 Preview가 표시됩니다.")

    if not preview_payload:
        return
    st.dataframe(
        pd.DataFrame(preview_payload["rows"]).rename(
            columns={
                "candidate_id": "후보 ID",
                "buyer_type": "매수자 유형",
                "house_price_range": "주택 가격 구간",
                "before_rule_version": "변경 전 rule_version",
                "after_rule_version": "변경 후 rule_version",
                "before_ltv_rate": "변경 전 LTV",
                "after_ltv_rate": "변경 후 LTV",
                "before_dsr_rate": "변경 전 DSR",
                "after_dsr_rate": "변경 후 DSR",
                "before_max_loan_amount": "변경 전 최대 대출액",
                "after_max_loan_amount": "변경 후 최대 대출액",
                "before_effective_from": "변경 전 시작일",
                "after_effective_from": "변경 후 시작일",
                "before_effective_to": "변경 전 종료일",
                "after_effective_to": "변경 후 종료일",
                "before_description": "변경 전 설명",
                "after_description": "변경 후 설명",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    confirmed = st.checkbox(
        "선택한 규칙에 대한 일괄 작업을 확인합니다.",
        key=f"{key_prefix}_confirm",
    )
    if st.button(
        "선택 규칙 일괄 종료 처리" if bulk_action == "일괄 종료 처리" else "선택 규칙 일괄 변경 적용",
        key=f"{key_prefix}_apply",
    ):
        if not confirmed:
            st.error("일괄 작업 확인 체크가 필요합니다.")
            return
        try:
            if bulk_action == "일괄 종료 처리":
                updated_count = rule_admin_service.deactivate_applied_loan_rules(
                    candidate_ids=candidate_ids,
                    inactive_from=deactivate_from.isoformat(),
                )
                st.success(f"대출 규칙 {updated_count}개를 종료 처리했습니다.")
            else:
                updated_count = rule_admin_service.bulk_update_applied_loan_rules(
                    candidate_ids=candidate_ids,
                    rule_version=bulk_rule_version.strip() if bulk_change_version and bulk_rule_version.strip() else None,
                    ltv_rate=bulk_ltv_rate if bulk_change_ltv else None,
                    dsr_rate=bulk_dsr_rate if bulk_change_dsr else None,
                    max_loan_amount_changed=bulk_change_max_loan,
                    max_loan_amount=None if bulk_max_loan_unlimited else int(from_eok(bulk_max_loan_amount)),
                    effective_from_changed=bulk_change_effective_from,
                    effective_from=bulk_effective_from.isoformat(),
                    effective_to_changed=bulk_change_effective_to,
                    effective_to=bulk_effective_to.isoformat() if bulk_use_effective_to else None,
                    description=bulk_description.strip() if bulk_change_description and bulk_description.strip() else None,
                )
                st.success(f"대출 규칙 {updated_count}개를 일괄 변경했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _render_loan_rule_editor(
    *,
    selected_summary: dict,
    editable_rules: dict[int, dict],
    rule_admin_service,
    key_prefix: str,
) -> None:
    candidate_id = selected_summary.get("_candidate_id")
    is_builtin_rule = not selected_summary.get("_editable") or candidate_id is None
    if is_builtin_rule:
        selected_rule = dict(selected_summary["_rule_payload"])
        field_key = (
            f"{key_prefix}-builtin-{selected_rule['rule_version']}-{selected_rule['effective_from']}-"
            f"{selected_rule['region_type']}-{selected_rule['buyer_type']}-{selected_rule['purpose']}-"
            f"{selected_rule['house_price_min']}"
        )
        st.info("선택한 기본 내장 규칙을 기준으로 수정용 override를 저장할 수 있습니다.")
    else:
        selected_rule = editable_rules[int(candidate_id)]
        field_key = f"{key_prefix}-{selected_rule['candidate_id']}"

    edit_region_options = rule_admin_service.list_loan_region_types()
    if selected_rule["region_type"] not in edit_region_options:
        edit_region_options = [selected_rule["region_type"], *edit_region_options]

    st.caption(
        "선택한 기본 규칙을 대체할 override를 저장할 수 있습니다."
        if is_builtin_rule
        else "선택한 적용 규칙을 바로 수정하거나 삭제할 수 있습니다."
    )
    generated_name = _generated_loan_rule_name(
        purpose=selected_rule["purpose"],
        region_type=selected_rule["region_type"],
        buyer_type=selected_rule["buyer_type"],
    )
    edit_rule_version = st.text_input("규칙 버전", value=str(selected_rule["rule_version"]), key=f"edit_loan_rule_version_{field_key}")
    st.caption(f"표시명: {generated_name}")
    edit_date_col1, edit_date_col2 = st.columns(2)
    edit_effective_from = edit_date_col1.date_input(
        "적용 시작일",
        value=date.fromisoformat(selected_rule["effective_from"]),
        key=f"edit_loan_effective_from_{field_key}",
    )
    edit_use_end_date = edit_date_col2.checkbox(
        "종료일 입력",
        value=selected_rule["effective_to"] is not None,
        key=f"edit_loan_use_end_date_{field_key}",
    )
    edit_effective_to = (
        st.date_input(
            "적용 종료일",
            value=(date.fromisoformat(selected_rule["effective_to"]) if selected_rule["effective_to"] else edit_effective_from),
            key=f"edit_loan_effective_to_{field_key}",
        )
        if edit_use_end_date
        else None
    )
    edit_condition_col1, edit_condition_col2, edit_condition_col3 = st.columns(3)
    edit_region_type = edit_condition_col1.selectbox(
        "지역 유형",
        edit_region_options,
        index=edit_region_options.index(selected_rule["region_type"]),
        format_func=_loan_region_type_label,
        key=f"edit_loan_region_type_{field_key}",
    )
    edit_buyer_type = edit_condition_col2.selectbox(
        "매수자 유형",
        ["ALL", "NO_HOME", "ONE_HOME", "MULTI_HOME"],
        index=["ALL", "NO_HOME", "ONE_HOME", "MULTI_HOME"].index(selected_rule["buyer_type"]),
        format_func=_buyer_type_label,
        key=f"edit_loan_buyer_type_{field_key}",
    )
    edit_purpose = edit_condition_col3.selectbox(
        "목적",
        ["OWNER_OCCUPIED", "INVESTMENT"],
        index=["OWNER_OCCUPIED", "INVESTMENT"].index(selected_rule["purpose"]),
        format_func=_investment_purpose_label,
        key=f"edit_loan_purpose_{field_key}",
    )
    edit_price_col1, edit_price_col2, edit_price_col3 = st.columns(3)
    edit_house_price_min_eok = edit_price_col1.number_input("가격 하한 (억 원)", min_value=0.0, value=to_eok(selected_rule["house_price_min"]), step=0.1, format="%.2f", key=f"edit_loan_house_price_min_{field_key}")
    edit_use_price_max = edit_price_col2.checkbox("가격 상한 미만 입력", value=selected_rule["house_price_max"] is not None, key=f"edit_loan_use_price_max_{field_key}")
    edit_house_price_max_exclusive_eok = edit_price_col2.number_input(
        "가격 상한 미만 (억 원)",
        min_value=0.0,
        value=(to_eok(int(selected_rule["house_price_max"]) + 1) if selected_rule["house_price_max"] is not None else to_eok(selected_rule["house_price_min"])),
        step=0.1,
        format="%.2f",
        disabled=not edit_use_price_max,
        key=f"edit_loan_house_price_max_{field_key}",
    )
    edit_unlimited_max_loan = edit_price_col3.checkbox("최대 대출액 제한 없음", value=selected_rule["max_loan_amount"] is None, key=f"edit_loan_unlimited_max_loan_{field_key}")
    edit_max_loan_amount_eok = edit_price_col3.number_input(
        "최대 대출액 (억 원)",
        min_value=0.0,
        value=(0.0 if selected_rule["max_loan_amount"] is None else to_eok(selected_rule["max_loan_amount"])),
        step=0.1,
        format="%.2f",
        disabled=edit_unlimited_max_loan,
        key=f"edit_loan_max_loan_amount_{field_key}",
    )
    edit_ratio_col1, edit_ratio_col2 = st.columns(2)
    edit_ltv_rate = edit_ratio_col1.number_input("LTV", min_value=0.0, max_value=1.0, value=float(selected_rule["ltv_rate"]), step=0.05, format="%.2f", key=f"edit_loan_ltv_rate_{field_key}")
    edit_dsr_rate = edit_ratio_col2.number_input("DSR", min_value=0.0, max_value=1.0, value=float(selected_rule["dsr_rate"]), step=0.05, format="%.2f", key=f"edit_loan_dsr_rate_{field_key}")
    edit_description = st.text_input("설명", value=selected_rule["description"], key=f"edit_loan_description_{field_key}")
    st.dataframe(
        pd.DataFrame(
            [
                {"항목": "rule_version", "변경 전": str(selected_rule["rule_version"]), "변경 후": edit_rule_version},
                {"항목": "LTV", "변경 전": f"{float(selected_rule['ltv_rate']) * 100:.1f}%", "변경 후": f"{float(edit_ltv_rate) * 100:.1f}%"},
                {"항목": "DSR", "변경 전": f"{float(selected_rule['dsr_rate']) * 100:.1f}%", "변경 후": f"{float(edit_dsr_rate) * 100:.1f}%"},
                {"항목": "최대 대출액", "변경 전": _bulk_max_loan_label(selected_rule["max_loan_amount"]), "변경 후": "제한 없음" if edit_unlimited_max_loan else format_compact_won(int(from_eok(edit_max_loan_amount_eok)))},
                {"항목": "설명", "변경 전": selected_rule["description"], "변경 후": edit_description},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    action_col1, action_col2 = st.columns(2)
    if action_col1.button("수정용 override 저장" if is_builtin_rule else "선택 규칙 수정", key=f"update_loan_rule_{field_key}"):
        try:
            if is_builtin_rule:
                rule_admin_service.create_loan_rule_override(
                    previous_rule=selected_summary["_rule_payload"],
                    rule_version=edit_rule_version,
                    effective_from=edit_effective_from.isoformat(),
                    effective_to=edit_effective_to.isoformat() if edit_effective_to else None,
                    region_type=edit_region_type,
                    buyer_type=edit_buyer_type,
                    purpose=edit_purpose,
                    house_price_min=int(from_eok(edit_house_price_min_eok)),
                    house_price_max=(int(from_eok(edit_house_price_max_exclusive_eok)) - 1 if edit_use_price_max else None),
                    ltv_rate=float(edit_ltv_rate),
                    dsr_rate=float(edit_dsr_rate),
                    max_loan_amount=(None if edit_unlimited_max_loan else int(from_eok(edit_max_loan_amount_eok))),
                    description=edit_description,
                )
                st.success("기본 규칙을 대체하는 override를 저장했습니다.")
            else:
                rule_admin_service.update_applied_loan_rule(
                    candidate_id=int(selected_rule["candidate_id"]),
                    rule_version=edit_rule_version,
                    effective_from=edit_effective_from.isoformat(),
                    effective_to=edit_effective_to.isoformat() if edit_effective_to else None,
                    region_type=edit_region_type,
                    buyer_type=edit_buyer_type,
                    purpose=edit_purpose,
                    house_price_min=int(from_eok(edit_house_price_min_eok)),
                    house_price_max=(int(from_eok(edit_house_price_max_exclusive_eok)) - 1 if edit_use_price_max else None),
                    ltv_rate=float(edit_ltv_rate),
                    dsr_rate=float(edit_dsr_rate),
                    max_loan_amount=(None if edit_unlimited_max_loan else int(from_eok(edit_max_loan_amount_eok))),
                    description=edit_description,
                )
                st.success("대출 규칙을 수정했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    deactivate_col, delete_col = st.columns(2)
    deactivate_from = deactivate_col.date_input("종료 처리 기준일", value=date.today(), key=f"deactivate_loan_rule_date_{field_key}", help="현재 계산에서 제외되지만 이력은 보존됩니다.")
    if deactivate_col.button("종료 처리", key=f"deactivate_loan_rule_{field_key}"):
        try:
            rule_admin_service.deactivate_loan_rule(selected_summary=selected_summary, inactive_from=deactivate_from.isoformat())
            st.success("대출 규칙을 종료 처리했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    if is_builtin_rule:
        delete_col.caption("기본 내장 규칙은 직접 삭제되지 않습니다. 필요하면 종료 처리 또는 override를 사용해 주세요.")
    else:
        delete_confirmed = delete_col.checkbox("선택한 규칙 삭제를 확인합니다.", key=f"delete_loan_confirm_{field_key}")
        if delete_col.button("선택 규칙 삭제", key=f"delete_loan_rule_{field_key}"):
            if not delete_confirmed:
                st.error("삭제 확인 체크가 필요합니다.")
            else:
                try:
                    rule_admin_service.delete_applied_loan_rule(int(selected_rule["candidate_id"]))
                    st.success("대출 규칙을 삭제했습니다.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


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
        [
            "NON_REGULATED",
            "LAND_TRANSACTION_PERMISSION",
            "SPECULATION_OVERHEATED_DISTRICT",
            "ADJUSTMENT_TARGET_AREA",
        ],
        format_func=_loan_region_type_label,
        key=f"preview_region_{candidate['id']}",
    )
    buyer_type = preview_cols[2].selectbox(
        "매수자 유형",
        ["ALL", "NO_HOME", "ONE_HOME", "MULTI_HOME"],
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
        "REGULATED": "공통 규제 규칙",
        "LAND_TRANSACTION_PERMISSION": "토지거래허가구역",
        "LAND_TRANSACTION_PERMISSION_AREA": "토지거래허가구역",
        "SPECULATION_OVERHEATED": "투기과열지구",
        "SPECULATION_OVERHEATED_DISTRICT": "투기과열지구",
        "ADJUSTMENT_TARGET": "조정대상지역",
        "ADJUSTMENT_TARGET_AREA": "조정대상지역",
    }.get(value, value)


def _buyer_type_label(value: str) -> str:
    return {
        "ALL": "전체",
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


def _loan_rule_query_summary(filters: dict) -> str:
    parts = [
        _investment_purpose_label(filters["purpose"]) if filters.get("purpose") else "전체 목적",
        _loan_region_type_label(filters["region_type"]) if filters.get("region_type") else "전체 지역 유형",
        _buyer_type_label(filters["buyer_type"]) if filters.get("buyer_type") else "전체 매수자 유형",
    ]
    if filters.get("house_price") is not None:
        parts.append(f"{format_compact_won(int(filters['house_price']))} 기준")
    if filters.get("rule_version"):
        parts.append(f"버전 {filters['rule_version']}")
    return " / ".join(parts) + " 적용 가능한 룰입니다."


def _current_query_conflicts(rows: list[dict[str, str]]) -> list[tuple]:
    counts: dict[tuple, int] = {}
    for row in rows:
        payload = row["_rule_payload"]
        key = (
            str(payload["purpose"]),
            str(payload["region_type"]),
            str(payload["buyer_type"]),
            int(payload["house_price_min"]),
            payload["house_price_max"],
        )
        counts[key] = counts.get(key, 0) + 1
    return [key for key, count in counts.items() if count > 1]


def _render_grouped_loan_rule_sections(
    rows: list[dict[str, str]],
    *,
    show_effective_dates: bool,
) -> None:
    grouped_rows = _group_loan_rule_rows(rows)
    for rule_version, purpose, region_type in grouped_rows:
        st.markdown(f"#### {rule_version} / {purpose} / {region_type}")
        group_df = pd.DataFrame(
            [
                _loan_group_row_view(item, show_effective_dates=show_effective_dates)
                for item in grouped_rows[(rule_version, purpose, region_type)]
            ]
        ).rename(columns=_loan_group_column_labels(show_effective_dates=show_effective_dates))
        st.dataframe(group_df, use_container_width=True, hide_index=True)


def _group_loan_rule_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], list[dict[str, str]]]:
    grouped_rows: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        group_key = (
            str(row["rule_version"]),
            str(row["investment_purpose"]),
            str(row["region_type"]),
        )
        grouped_rows.setdefault(group_key, []).append(row)
    return grouped_rows


def _loan_group_row_view(
    row: dict[str, str],
    *,
    show_effective_dates: bool,
) -> dict[str, str]:
    view = {
        "state": row["state"],
        "buyer_type": row["buyer_type"],
        "house_price_range": row["house_price_range"],
        "ltv_rate": row["ltv_rate"],
        "dsr_rate": row["dsr_rate"],
        "max_loan_amount": row["max_loan_amount"],
        "conditions": row["conditions"],
        "description": row["description"],
    }
    if show_effective_dates:
        view = {
            "effective_from": row["effective_from"],
            "effective_to": row["effective_to"],
            **view,
        }
    return view


def _loan_group_column_labels(*, show_effective_dates: bool) -> dict[str, str]:
    labels = {
        "state": "상태",
        "buyer_type": "매수자 유형",
        "house_price_range": "주택 가격 구간",
        "ltv_rate": "LTV",
        "dsr_rate": "DSR",
        "max_loan_amount": "최대 대출 한도",
        "conditions": "조건",
        "description": "설명",
    }
    if show_effective_dates:
        return {
            "effective_from": "적용 시작일",
            "effective_to": "적용 종료일",
            **labels,
        }
    return labels


def _generated_loan_rule_name(*, purpose: str, region_type: str, buyer_type: str) -> str:
    return f"{_investment_purpose_label(purpose)} / {_loan_region_type_label(region_type)} / {_buyer_type_label(buyer_type)}"


def _loan_house_price_range_label(item: dict) -> str:
    min_value = int(item["house_price_min"])
    max_value = item["house_price_max"]
    if max_value is None:
        return f"{format_compact_won(min_value)} 이상"
    return f"{format_compact_won(min_value)} ~ {format_compact_won(int(max_value))}"


def _bulk_max_loan_label(value) -> str:
    if value is None:
        return "제한 없음"
    return format_compact_won(int(value))


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
