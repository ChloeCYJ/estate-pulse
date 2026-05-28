from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.utils.money_utils import format_compact_won, from_eok, to_eok


def render_finance_profile_page(finance_repository) -> None:
    st.title("자금 프로필")
    st.caption("Phase 1 분석에 실제로 필요한 정보 위주로 간단하게 입력합니다.")

    create_tab, manage_tab = st.tabs(["등록", "관리"])

    with create_tab:
        with st.form("create_finance_profile_form"):
            cash_amount_eok = st.number_input(
                "보유 현금 (억원) *",
                min_value=0.0,
                step=0.1,
                value=0.0,
                format="%.2f",
                help="예: 2억이면 2.0, 8억 5천이면 8.5처럼 입력해 주세요.",
            )
            existing_debt_eok = st.number_input(
                "기존 대출 (억원)",
                min_value=0.0,
                step=0.1,
                value=0.0,
                format="%.2f",
                help="없으면 0으로 두면 됩니다.",
            )
            ltv_limit = st.number_input("예상 LTV 한도", min_value=0.0, max_value=1.0, step=0.05, value=0.6)
            submitted = st.form_submit_button("프로필 저장")

        if submitted:
            cash_amount = from_eok(cash_amount_eok)
            existing_debt = from_eok(existing_debt_eok)
            if cash_amount <= 0:
                st.error("보유 현금은 필수입니다.")
            else:
                finance_repository.create(
                    cash_amount=int(cash_amount),
                    annual_income=None,
                    existing_debt=int(existing_debt),
                    interest_rate=None,
                    ltv_limit=float(ltv_limit) or None,
                    dsr_limit=None,
                )
                st.success("자금 프로필을 저장했습니다.")
                st.rerun()

    with manage_tab:
        profiles = finance_repository.list_all()
        if not profiles:
            st.caption("등록된 자금 프로필이 없습니다.")
            return

        profile_df = pd.DataFrame(profiles)[
            ["id", "cash_amount", "existing_debt", "ltv_limit", "created_at"]
        ].rename(
            columns={
                "id": "ID",
                "cash_amount": "보유 현금",
                "existing_debt": "기존 대출",
                "ltv_limit": "LTV 한도",
                "created_at": "등록일시",
            }
        )
        profile_df["보유 현금"] = profile_df["보유 현금"].map(format_compact_won)
        profile_df["기존 대출"] = profile_df["기존 대출"].map(format_compact_won)
        st.dataframe(profile_df, use_container_width=True)
        options = {
            f"#{item['id']} | 보유 현금 {format_compact_won(item['cash_amount'])}": item
            for item in profiles
        }
        selected_label = st.selectbox("수정할 프로필 선택", list(options.keys()))
        selected = options[selected_label]

        with st.form("update_finance_profile_form"):
            cash_amount_eok = st.number_input(
                "보유 현금 (억원) *",
                min_value=0.0,
                step=0.1,
                value=to_eok(selected["cash_amount"]),
                format="%.2f",
                help="예: 2억이면 2.0, 8억 5천이면 8.5처럼 입력해 주세요.",
            )
            existing_debt_eok = st.number_input(
                "기존 대출 (억원)",
                min_value=0.0,
                step=0.1,
                value=to_eok(selected["existing_debt"] or 0),
                format="%.2f",
                help="없으면 0으로 두면 됩니다.",
            )
            ltv_limit = st.number_input(
                "예상 LTV 한도",
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                value=float(selected["ltv_limit"] or 0.6),
            )
            col_update, col_delete = st.columns(2)
            update_clicked = col_update.form_submit_button("수정")
            delete_clicked = col_delete.form_submit_button("삭제")

        if update_clicked:
            cash_amount = from_eok(cash_amount_eok)
            existing_debt = from_eok(existing_debt_eok)
            finance_repository.update(
                selected["id"],
                cash_amount=int(cash_amount),
                annual_income=selected.get("annual_income"),
                existing_debt=int(existing_debt),
                interest_rate=selected.get("interest_rate"),
                ltv_limit=float(ltv_limit) or None,
                dsr_limit=selected.get("dsr_limit"),
            )
            st.success("자금 프로필을 수정했습니다.")
            st.rerun()

        if delete_clicked:
            finance_repository.delete(selected["id"])
            st.warning("자금 프로필을 삭제했습니다.")
            st.rerun()
