from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.utils.money_utils import format_compact_won, from_eok, to_eok


def render_finance_profile_page(finance_repository) -> None:
    st.title("자금 프로필")
    st.caption(
        "보유 현금, 부채, 보유 부동산 정보를 등록합니다. LTV는 기본적으로 분석 시점의 대출 규칙과 지역 규제로 자동 계산됩니다."
    )

    create_tab, manage_tab = st.tabs(["등록", "관리"])

    with create_tab:
        payload = _render_profile_form(
            form_key="create_finance_profile_form",
            submit_label="프로필 저장",
        )
        if payload is not None:
            finance_repository.create(**payload)
            st.success("자금 프로필을 저장했습니다.")
            st.rerun()

    with manage_tab:
        profiles = finance_repository.list_all()
        if not profiles:
            st.caption("등록된 자금 프로필이 없습니다.")
            return

        profile_df = pd.DataFrame(profiles).copy()
        profile_df["existing_debt"] = profile_df.apply(_calculate_existing_debt_won, axis=1)
        profile_df = profile_df[
            [
                "id",
                "cash_amount",
                "annual_income",
                "interest_rate",
                "existing_debt",
                "home_count",
                "owned_real_estate_value",
                "owned_real_estate_debt",
                "use_manual_ltv",
                "manual_ltv_rate",
                "created_at",
            ]
        ].copy()
        profile_df["cash_amount"] = profile_df["cash_amount"].map(format_compact_won)
        profile_df["annual_income"] = profile_df["annual_income"].map(_format_money_or_dash)
        profile_df["interest_rate"] = profile_df["interest_rate"].map(_format_rate_or_dash)
        profile_df["existing_debt"] = profile_df["existing_debt"].map(format_compact_won)
        profile_df["owned_real_estate_value"] = profile_df["owned_real_estate_value"].map(
            format_compact_won
        )
        profile_df["owned_real_estate_debt"] = profile_df["owned_real_estate_debt"].map(
            format_compact_won
        )
        profile_df["use_manual_ltv"] = profile_df["use_manual_ltv"].map(
            lambda value: "수동" if value else "자동"
        )
        profile_df["manual_ltv_rate"] = profile_df["manual_ltv_rate"].map(_format_ltv_or_dash)
        profile_df = profile_df.rename(
            columns={
                "id": "ID",
                "cash_amount": "보유 현금",
                "annual_income": "연소득",
                "interest_rate": "금리",
                "existing_debt": "기존 대출 총액",
                "home_count": "보유 주택 수",
                "owned_real_estate_value": "보유 부동산 시가",
                "owned_real_estate_debt": "보유 부동산 대출",
                "use_manual_ltv": "LTV 적용",
                "manual_ltv_rate": "수동 LTV",
                "created_at": "등록일시",
            }
        )
        st.dataframe(profile_df, use_container_width=True, hide_index=True)

        options = {
            f"#{item['id']} | 보유 현금 {format_compact_won(item['cash_amount'])}": item
            for item in profiles
        }
        selected_label = st.selectbox("수정할 프로필 선택", list(options.keys()))
        selected = options[selected_label]

        payload = _render_profile_form(
            form_key="update_finance_profile_form",
            submit_label="수정",
            selected=selected,
            include_delete=True,
        )

        if payload is None:
            return
        if payload == "DELETE":
            finance_repository.delete(selected["id"])
            st.warning("자금 프로필을 삭제했습니다.")
            st.rerun()

        finance_repository.update(
            selected["id"],
            **payload,
        )
        st.success("자금 프로필을 수정했습니다.")
        st.rerun()


def _render_profile_form(
    *,
    form_key: str,
    submit_label: str,
    selected: dict | None = None,
    include_delete: bool = False,
) -> dict | str | None:
    selected = selected or {}
    with st.container():
        st.markdown("### 현금")
        cash_amount_eok = st.number_input(
            "보유 현금 (억원) *",
            min_value=0.0,
            step=0.1,
            value=to_eok(selected.get("cash_amount") or 0),
            format="%.2f",
            help="예: 2억원은 2.0, 8억 5천만원은 8.5로 입력해 주세요.",
            key=f"{form_key}_cash_amount",
        )
        annual_income_eok = st.number_input(
            "연소득 (억원)",
            min_value=0.0,
            step=0.1,
            value=to_eok(selected.get("annual_income") or 0),
            format="%.2f",
            help="입력하지 않으면 DSR 계산을 생략합니다.",
            key=f"{form_key}_annual_income",
        )
        interest_rate = st.number_input(
            "금리",
            min_value=0.0,
            step=0.005,
            value=float(selected.get("interest_rate") or 0.0),
            format="%.3f",
            help="예: 4%는 0.04로 입력합니다. 입력하지 않으면 월상환액과 DSR 계산을 생략합니다.",
            key=f"{form_key}_interest_rate",
        )

        st.markdown("### 부채")
        debt_col1, debt_col2 = st.columns(2)
        credit_loan_balance_eok = debt_col1.number_input(
            "신용대출 잔액 (억원)",
            min_value=0.0,
            step=0.1,
            value=to_eok(selected.get("credit_loan_balance") or 0),
            format="%.2f",
            key=f"{form_key}_credit_loan_balance",
        )
        other_loan_balance_eok = debt_col2.number_input(
            "기타 대출 잔액 (억원)",
            min_value=0.0,
            step=0.1,
            value=to_eok(selected.get("other_loan_balance") or 0),
            format="%.2f",
            key=f"{form_key}_other_loan_balance",
        )

        st.markdown("### 보유 부동산")
        estate_col1, estate_col2, estate_col3 = st.columns(3)
        home_count = estate_col1.number_input(
            "보유 주택 수",
            min_value=0,
            step=1,
            value=int(selected.get("home_count") or 0),
            key=f"{form_key}_home_count",
        )
        owned_real_estate_value_eok = estate_col2.number_input(
            "보유 부동산 시가 (억원)",
            min_value=0.0,
            step=0.1,
            value=to_eok(selected.get("owned_real_estate_value") or 0),
            format="%.2f",
            key=f"{form_key}_owned_real_estate_value",
        )
        owned_real_estate_debt_eok = estate_col3.number_input(
            "보유 부동산 대출 잔액 (억원)",
            min_value=0.0,
            step=0.1,
            value=to_eok(selected.get("owned_real_estate_debt") or 0),
            format="%.2f",
            key=f"{form_key}_owned_real_estate_debt",
        )
        existing_debt_eok = _calculate_existing_debt_eok(
            owned_real_estate_debt_eok=owned_real_estate_debt_eok,
            credit_loan_balance_eok=credit_loan_balance_eok,
            other_loan_balance_eok=other_loan_balance_eok,
        )
        st.metric(
            "기존 대출 총액",
            format_compact_won(from_eok(existing_debt_eok)),
            help="보유 부동산 대출 잔액 + 신용대출 잔액 + 기타 대출 잔액의 자동 합산값입니다.",
        )

        st.markdown("### 대출 설정")
        st.info("자동 계산 LTV: 분석 시 선택한 매물의 지역 규제와 대출 규칙 엔진으로 계산됩니다.")
        use_manual_ltv = st.checkbox(
            "수동 LTV 사용",
            value=bool(selected.get("use_manual_ltv") or False),
            help="정책 데이터 오류, 특수 은행 조건 등 예외적인 경우에만 사용하세요.",
            key=f"{form_key}_use_manual_ltv",
        )
        manual_ltv_rate = st.number_input(
            "수동 LTV 입력값",
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            value=float(selected.get("manual_ltv_rate") or 0.0),
            format="%.2f",
            disabled=not use_manual_ltv,
            key=f"{form_key}_manual_ltv_rate",
        )

        if include_delete:
            col_update, col_delete = st.columns(2)
            submitted = col_update.button(submit_label, key=f"{form_key}_submit")
            delete_clicked = col_delete.button("삭제", key=f"{form_key}_delete")
        else:
            submitted = st.button(submit_label, key=f"{form_key}_submit")
            delete_clicked = False

    if delete_clicked:
        return "DELETE"
    if not submitted:
        return None

    payload = _build_profile_payload(
        cash_amount_eok=cash_amount_eok,
        annual_income_eok=annual_income_eok,
        interest_rate=interest_rate,
        credit_loan_balance_eok=credit_loan_balance_eok,
        other_loan_balance_eok=other_loan_balance_eok,
        home_count=int(home_count),
        owned_real_estate_value_eok=owned_real_estate_value_eok,
        owned_real_estate_debt_eok=owned_real_estate_debt_eok,
        use_manual_ltv=use_manual_ltv,
        manual_ltv_rate=float(manual_ltv_rate) if use_manual_ltv else None,
        selected=selected,
    )
    if payload["cash_amount"] <= 0:
        st.error("보유 현금은 필수입니다.")
        return None
    if payload["use_manual_ltv"] and payload["manual_ltv_rate"] is None:
        st.error("수동 LTV를 사용하려면 0~1 범위의 값을 입력해 주세요.")
        return None
    return payload


def _build_profile_payload(
    *,
    cash_amount_eok: float,
    annual_income_eok: float,
    interest_rate: float,
    credit_loan_balance_eok: float,
    other_loan_balance_eok: float,
    home_count: int,
    owned_real_estate_value_eok: float,
    owned_real_estate_debt_eok: float,
    use_manual_ltv: bool,
    manual_ltv_rate: float | None,
    selected: dict,
) -> dict:
    return {
        "cash_amount": int(from_eok(cash_amount_eok)),
        "annual_income": _to_optional_won(annual_income_eok),
        "existing_debt": int(
            from_eok(
                _calculate_existing_debt_eok(
                    owned_real_estate_debt_eok=owned_real_estate_debt_eok,
                    credit_loan_balance_eok=credit_loan_balance_eok,
                    other_loan_balance_eok=other_loan_balance_eok,
                )
            )
        ),
        "interest_rate": _to_optional_ratio(interest_rate),
        "ltv_limit": selected.get("ltv_limit"),
        "dsr_limit": selected.get("dsr_limit"),
        "home_count": home_count,
        "owned_real_estate_value": int(from_eok(owned_real_estate_value_eok)),
        "owned_real_estate_debt": int(from_eok(owned_real_estate_debt_eok)),
        "credit_loan_balance": int(from_eok(credit_loan_balance_eok)),
        "other_loan_balance": int(from_eok(other_loan_balance_eok)),
        "use_manual_ltv": use_manual_ltv,
        "manual_ltv_rate": manual_ltv_rate,
    }


def _calculate_existing_debt_eok(
    *,
    owned_real_estate_debt_eok: float,
    credit_loan_balance_eok: float,
    other_loan_balance_eok: float,
) -> float:
    return owned_real_estate_debt_eok + credit_loan_balance_eok + other_loan_balance_eok


def _calculate_existing_debt_won(profile: dict | pd.Series) -> int:
    return int(profile.get("owned_real_estate_debt") or 0) + int(
        profile.get("credit_loan_balance") or 0
    ) + int(profile.get("other_loan_balance") or 0)


def _to_optional_won(value_eok: float) -> int | None:
    if value_eok <= 0:
        return None
    return int(from_eok(value_eok))


def _to_optional_ratio(value: float) -> float | None:
    if value <= 0:
        return None
    return float(value)


def _format_money_or_dash(value: int | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return format_compact_won(int(value))


def _format_rate_or_dash(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value) * 100:.1f}%"


def _format_ltv_or_dash(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value) * 100:.1f}%"
