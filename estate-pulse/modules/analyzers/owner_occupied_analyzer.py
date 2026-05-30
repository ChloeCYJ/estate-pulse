from __future__ import annotations


def calculate_owner_occupied_metrics(
    *,
    sale_price: int,
    estimated_loan: int,
    acquisition_cost_total: int,
    cash_amount: int,
    annual_income: int | None = None,
    annual_interest_rate: float | None = None,
    loan_term_years: int = 30,
) -> dict:
    """Return affordability metrics for owner-occupied purchases."""
    required_cash = int(sale_price) - int(estimated_loan) + int(acquisition_cost_total)
    shortage_cash = required_cash - int(cash_amount)
    remaining_cash_after_purchase = int(cash_amount) - required_cash
    monthly_repayment = calculate_monthly_repayment(
        loan_amount=int(estimated_loan),
        annual_interest_rate=annual_interest_rate,
        loan_term_years=loan_term_years,
    )
    dsr = calculate_dsr(
        monthly_repayment=monthly_repayment,
        annual_income=annual_income,
    )

    return {
        "required_cash": required_cash,
        "shortage_cash": shortage_cash,
        "remaining_cash_after_purchase": remaining_cash_after_purchase,
        "monthly_repayment": monthly_repayment,
        "dsr": dsr,
        "scenario_explanation": "실거주 기준으로 전세 보증금은 차감하지 않고 자금 여력과 상환 부담을 함께 봤습니다.",
    }


def calculate_monthly_repayment(
    *,
    loan_amount: int,
    annual_interest_rate: float | None,
    loan_term_years: int = 30,
) -> int | None:
    """Estimate a monthly repayment using a standard amortized-loan formula."""
    loan_amount = int(loan_amount or 0)
    if loan_amount <= 0:
        return 0

    normalized_rate = _normalize_interest_rate(annual_interest_rate)
    if normalized_rate is None or normalized_rate <= 0:
        return None

    monthly_rate = normalized_rate / 12
    total_payments = int(loan_term_years) * 12
    growth = (1 + monthly_rate) ** total_payments
    factor = (monthly_rate * growth) / (growth - 1)
    return int(round(loan_amount * factor))


def calculate_dsr(
    *,
    monthly_repayment: int | None,
    annual_income: int | None,
) -> float | None:
    """Return the debt service ratio as a percent when income is available."""
    if monthly_repayment is None or not annual_income:
        return None
    if annual_income <= 0:
        return None
    return monthly_repayment * 12 / int(annual_income) * 100


def _normalize_interest_rate(value: float | None) -> float | None:
    if value is None:
        return None
    normalized = float(value)
    if normalized > 1:
        normalized /= 100
    return normalized
