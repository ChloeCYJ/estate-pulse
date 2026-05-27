from __future__ import annotations

import pandas as pd
import streamlit as st


def render_finance_profile_page(finance_repository) -> None:
    st.title("자금 프로필")
    st.caption("Phase 1 분석에 실제로 필요한 정보 위주로 간단하게 입력합니다.")

    create_tab, manage_tab = st.tabs(["등록", "관리"])

    with create_tab:
        with st.form("create_finance_profile_form"):
            cash_amount = st.number_input("보유 현금 *", min_value=0, step=1000000, value=0)
            existing_debt = st.number_input("기존 대출", min_value=0, step=1000000, value=0)
            ltv_limit = st.number_input("예상 LTV 한도", min_value=0.0, max_value=1.0, step=0.05, value=0.6)
            submitted = st.form_submit_button("프로필 저장")

        if submitted:
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
        st.dataframe(profile_df, use_container_width=True)
        options = {
            f"#{item['id']} | 보유 현금 {item['cash_amount']:,}원": item for item in profiles
        }
        selected_label = st.selectbox("수정할 프로필 선택", list(options.keys()))
        selected = options[selected_label]

        with st.form("update_finance_profile_form"):
            cash_amount = st.number_input(
                "보유 현금 *",
                min_value=0,
                step=1000000,
                value=int(selected["cash_amount"]),
            )
            existing_debt = st.number_input(
                "기존 대출",
                min_value=0,
                step=1000000,
                value=int(selected["existing_debt"] or 0),
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
