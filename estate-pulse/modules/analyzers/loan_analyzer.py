from __future__ import annotations

from datetime import date
import math

from config.loan_rules import LoanRule, get_loan_rules


def select_loan_rule(
    *,
    sale_price: int,
    region_type: str,
    buyer_type: str,
    purpose: str,
    reference_date: date | None = None,
    rules: list[LoanRule] | None = None,
) -> LoanRule:
    """Return the active loan rule that matches the input conditions."""
    target_date = reference_date or date.today()

    for rule in rules or get_loan_rules():
        if rule.region_type != region_type:
            continue
        if rule.buyer_type != buyer_type:
            continue
        if rule.purpose != purpose:
            continue
        if not rule.is_effective_on(target_date):
            continue
        if not rule.matches_price(sale_price):
            continue
        return rule

    raise ValueError("No matching loan rule was found.")


def calculate_loan_terms(
    *,
    sale_price: int,
    region_type: str,
    buyer_type: str,
    purpose: str,
    reference_date: date | None = None,
    ltv_rate_override: float | None = None,
    final_loan_amount_override: int | None = None,
    annual_income: int | None = None,
    existing_debt: int = 0,
    annual_interest_rate: float | None = None,
    loan_term_years: int = 30,
    rules: list[LoanRule] | None = None,
) -> dict:
    """Calculate the applicable loan terms from the configured rule set."""
    rule = select_loan_rule(
        sale_price=sale_price,
        region_type=region_type,
        buyer_type=buyer_type,
        purpose=purpose,
        reference_date=reference_date,
        rules=rules,
    )

    applied_ltv_rate = (
        max(float(ltv_rate_override), 0.0)
        if ltv_rate_override is not None
        else rule.ltv_rate
    )
    loan_amount_by_ltv = int(sale_price * applied_ltv_rate)
    dsr_based_loan_limit = _calculate_dsr_based_loan_limit(
        annual_income=annual_income,
        existing_debt=existing_debt,
        annual_interest_rate=annual_interest_rate,
        dsr_rate=rule.dsr_rate,
        loan_term_years=loan_term_years,
    )

    policy_limits = [loan_amount_by_ltv]
    if dsr_based_loan_limit is not None:
        policy_limits.append(dsr_based_loan_limit)
    if rule.max_loan_amount is not None:
        policy_limits.append(int(rule.max_loan_amount))
    policy_capped_loan_amount = min(policy_limits)

    manual_loan_amount_override = (
        max(int(final_loan_amount_override), 0)
        if final_loan_amount_override is not None
        else None
    )
    final_loan_amount = min(
        [policy_capped_loan_amount]
        + ([manual_loan_amount_override] if manual_loan_amount_override is not None else [])
    )

    return {
        "rule_version": rule.rule_version,
        "rule_description": rule.description,
        "region_type": rule.region_type,
        "buyer_type": rule.buyer_type,
        "purpose": rule.purpose,
        "house_price_min": rule.house_price_min,
        "house_price_max": rule.house_price_max,
        "applied_ltv_rate": applied_ltv_rate,
        "applied_dsr_rate": rule.dsr_rate,
        "max_loan_amount": rule.max_loan_amount,
        "loan_amount_by_ltv": loan_amount_by_ltv,
        "dsr_based_loan_limit": dsr_based_loan_limit,
        "policy_capped_loan_amount": policy_capped_loan_amount,
        "capped_loan_amount": policy_capped_loan_amount,
        "manual_loan_amount_override": manual_loan_amount_override,
        "final_loan_amount": final_loan_amount,
        "ltv_source": "manual override" if ltv_rate_override is not None else "rule application",
        "loan_amount_source": _loan_amount_source(
            policy_capped_loan_amount=policy_capped_loan_amount,
            manual_loan_amount_override=manual_loan_amount_override,
        ),
    }


def _loan_amount_source(
    *,
    policy_capped_loan_amount: int,
    manual_loan_amount_override: int | None,
) -> str:
    if (
        manual_loan_amount_override is not None
        and manual_loan_amount_override < policy_capped_loan_amount
    ):
        return "manual override"
    return "rule application"


def _calculate_dsr_based_loan_limit(
    *,
    annual_income: int | None,
    existing_debt: int,
    annual_interest_rate: float | None,
    dsr_rate: float,
    loan_term_years: int,
) -> int | None:
    if not annual_income or annual_income <= 0:
        return None

    normalized_rate = _normalize_interest_rate(annual_interest_rate)
    if normalized_rate is None:
        return None

    monthly_budget = annual_income * dsr_rate / 12
    existing_monthly_debt_service = _calculate_monthly_repayment(
        loan_amount=max(int(existing_debt or 0), 0),
        annual_interest_rate=normalized_rate,
        loan_term_years=loan_term_years,
    )
    available_monthly_budget = max(monthly_budget - existing_monthly_debt_service, 0)

    return _principal_from_monthly_budget(
        monthly_budget=available_monthly_budget,
        annual_interest_rate=normalized_rate,
        loan_term_years=loan_term_years,
    )


def _calculate_monthly_repayment(
    *,
    loan_amount: int,
    annual_interest_rate: float,
    loan_term_years: int,
) -> float:
    if loan_amount <= 0:
        return 0.0
    if annual_interest_rate <= 0:
        months = max(int(loan_term_years) * 12, 1)
        return loan_amount / months

    monthly_rate = annual_interest_rate / 12
    total_payments = max(int(loan_term_years) * 12, 1)
    growth = (1 + monthly_rate) ** total_payments
    factor = (monthly_rate * growth) / (growth - 1)
    return loan_amount * factor


def _principal_from_monthly_budget(
    *,
    monthly_budget: float,
    annual_interest_rate: float,
    loan_term_years: int,
) -> int:
    if monthly_budget <= 0:
        return 0

    total_payments = max(int(loan_term_years) * 12, 1)
    if annual_interest_rate <= 0:
        return int(monthly_budget * total_payments)

    monthly_rate = annual_interest_rate / 12
    growth = (1 + monthly_rate) ** total_payments
    factor = (monthly_rate * growth) / (growth - 1)
    if factor <= 0:
        return 0
    return int(math.floor(monthly_budget / factor))


def _normalize_interest_rate(value: float | None) -> float | None:
    if value is None:
        return None
    normalized = float(value)
    if normalized > 1:
        normalized /= 100
    return normalized
