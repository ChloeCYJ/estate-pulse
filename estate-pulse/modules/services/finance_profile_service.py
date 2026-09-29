from __future__ import annotations

from collections.abc import Mapping

from modules.utils.money_utils import from_eok


class FinanceProfileValidationError(ValueError):
    def __init__(self, field_errors: dict[str, str]) -> None:
        super().__init__("finance_profile_validation_failed")
        self.field_errors = field_errors


def build_finance_profile_payload(
    *,
    cash_amount_eok: float,
    annual_income_eok: float,
    interest_rate_percent: float,
    credit_loan_balance_eok: float,
    other_loan_balance_eok: float,
    home_count: int,
    owned_real_estate_value_eok: float,
    owned_real_estate_debt_eok: float,
    use_manual_ltv: bool,
    manual_ltv_rate: float | None,
    existing_profile: Mapping[str, object] | None = None,
) -> dict[str, object]:
    field_errors: dict[str, str] = {}
    values = {
        "cash_amount_eok": _non_negative_number(
            "cash_amount_eok", cash_amount_eok, field_errors
        ),
        "annual_income_eok": _non_negative_number(
            "annual_income_eok", annual_income_eok, field_errors
        ),
        "interest_rate_percent": _non_negative_number(
            "interest_rate_percent", interest_rate_percent, field_errors
        ),
        "credit_loan_balance_eok": _non_negative_number(
            "credit_loan_balance_eok", credit_loan_balance_eok, field_errors
        ),
        "other_loan_balance_eok": _non_negative_number(
            "other_loan_balance_eok", other_loan_balance_eok, field_errors
        ),
        "owned_real_estate_value_eok": _non_negative_number(
            "owned_real_estate_value_eok", owned_real_estate_value_eok, field_errors
        ),
        "owned_real_estate_debt_eok": _non_negative_number(
            "owned_real_estate_debt_eok", owned_real_estate_debt_eok, field_errors
        ),
    }
    try:
        normalized_home_count = int(home_count)
        if normalized_home_count < 0:
            raise ValueError
    except (TypeError, ValueError):
        normalized_home_count = 0
        field_errors["home_count"] = "보유 주택 수는 0 이상이어야 합니다."

    if values["cash_amount_eok"] <= 0:
        field_errors["cash_amount_eok"] = "보유 현금을 입력해 주세요."
    if 0 < values["interest_rate_percent"] < 1:
        field_errors["interest_rate_percent"] = (
            "금리는 % 단위로 입력해 주세요. 예: 4%는 4.0"
        )

    normalized_manual_ltv: float | None = None
    if use_manual_ltv:
        try:
            normalized_manual_ltv = float(manual_ltv_rate)  # type: ignore[arg-type]
            if not 0 <= normalized_manual_ltv <= 1:
                raise ValueError
        except (TypeError, ValueError):
            field_errors["manual_ltv_rate"] = "수동 LTV는 0~1 범위로 입력해 주세요."

    if field_errors:
        raise FinanceProfileValidationError(field_errors)

    existing = existing_profile or {}
    total_debt_eok = (
        values["owned_real_estate_debt_eok"]
        + values["credit_loan_balance_eok"]
        + values["other_loan_balance_eok"]
    )
    return {
        "cash_amount": int(from_eok(values["cash_amount_eok"])),
        "annual_income": _optional_won(values["annual_income_eok"]),
        "existing_debt": int(from_eok(total_debt_eok)),
        "interest_rate": _optional_ratio(values["interest_rate_percent"]),
        "ltv_limit": existing.get("ltv_limit"),
        "dsr_limit": existing.get("dsr_limit"),
        "home_count": normalized_home_count,
        "owned_real_estate_value": int(
            from_eok(values["owned_real_estate_value_eok"])
        ),
        "owned_real_estate_debt": int(
            from_eok(values["owned_real_estate_debt_eok"])
        ),
        "credit_loan_balance": int(from_eok(values["credit_loan_balance_eok"])),
        "other_loan_balance": int(from_eok(values["other_loan_balance_eok"])),
        "use_manual_ltv": bool(use_manual_ltv),
        "manual_ltv_rate": normalized_manual_ltv,
    }


class FinanceProfileService:
    def __init__(self, finance_repository) -> None:
        self.finance_repository = finance_repository

    def get_current(self, user_id: int) -> dict | None:
        return self.finance_repository.get_for_user(user_id)

    def save_current(
        self,
        *,
        user_id: int,
        payload: Mapping[str, object],
    ) -> dict:
        current = self.finance_repository.get_for_user(user_id)
        if current is None:
            self.finance_repository.create_for_user(user_id=user_id, payload=payload)
        elif not self.finance_repository.update_for_user(
            user_id=user_id,
            payload=payload,
        ):
            raise RuntimeError("finance_profile_update_failed")

        saved = self.finance_repository.get_for_user(user_id)
        if saved is None:
            raise RuntimeError("finance_profile_reload_failed")
        return saved


def _non_negative_number(
    field_name: str,
    value: object,
    field_errors: dict[str, str],
) -> float:
    try:
        normalized = float(value)
        if normalized < 0:
            raise ValueError
        return normalized
    except (TypeError, ValueError):
        field_errors[field_name] = "0 이상의 숫자를 입력해 주세요."
        return 0.0


def _optional_won(value_eok: float) -> int | None:
    return int(from_eok(value_eok)) if value_eok > 0 else None


def _optional_ratio(value_percent: float) -> float | None:
    return value_percent / 100 if value_percent > 0 else None
