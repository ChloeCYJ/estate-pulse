from __future__ import annotations

from modules.utils.money_utils import to_eok


def build_finance_profile_view_model(
    *,
    profile: dict | None,
    status: str = "ready",
    field_errors: dict[str, str] | None = None,
    notice: dict[str, str] | None = None,
) -> dict[str, object]:
    source = profile or {}
    page_status = "empty" if profile is None and status == "ready" else status
    cash_amount = int(source.get("cash_amount") or 0)
    real_estate_value = int(source.get("owned_real_estate_value") or 0)
    real_estate_debt = int(source.get("owned_real_estate_debt") or 0)
    credit_debt = int(source.get("credit_loan_balance") or 0)
    other_debt = int(source.get("other_loan_balance") or 0)
    total_debt = real_estate_debt + credit_debt + other_debt
    return {
        "page_status": page_status,
        "form": {
            "cash_amount_eok": to_eok(cash_amount),
            "annual_income_eok": to_eok(source.get("annual_income") or 0),
            "interest_rate_percent": float(source.get("interest_rate") or 0) * 100,
            "credit_loan_balance_eok": to_eok(credit_debt),
            "other_loan_balance_eok": to_eok(other_debt),
            "home_count": int(source.get("home_count") or 0),
            "owned_real_estate_value_eok": to_eok(real_estate_value),
            "owned_real_estate_debt_eok": to_eok(real_estate_debt),
            "use_manual_ltv": bool(source.get("use_manual_ltv") or False),
            "manual_ltv_rate": source.get("manual_ltv_rate"),
        },
        "summary": {
            "total_assets": cash_amount + real_estate_value,
            "total_debt": total_debt,
            "net_worth": cash_amount + real_estate_value - total_debt,
            "home_count": int(source.get("home_count") or 0),
        },
        "field_errors": field_errors or {},
        "notice": notice,
    }
