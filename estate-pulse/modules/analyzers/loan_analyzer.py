from __future__ import annotations

from datetime import date

from config.loan_rules import LoanRule, get_loan_rules


def select_loan_rule(
    *,
    sale_price: int,
    region_type: str,
    buyer_type: str,
    purpose: str,
    reference_date: date | None = None,
) -> LoanRule:
    """Return the active loan rule that matches the input conditions."""
    target_date = reference_date or date.today()

    for rule in get_loan_rules():
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

    raise ValueError("적용 가능한 대출 규칙을 찾을 수 없습니다.")


def calculate_loan_terms(
    *,
    sale_price: int,
    region_type: str,
    buyer_type: str,
    purpose: str,
    reference_date: date | None = None,
    ltv_rate_override: float | None = None,
    final_loan_amount_override: int | None = None,
) -> dict:
    """Calculate the applicable loan terms from the configured rule set."""
    rule = select_loan_rule(
        sale_price=sale_price,
        region_type=region_type,
        buyer_type=buyer_type,
        purpose=purpose,
        reference_date=reference_date,
    )

    applied_ltv_rate = max(ltv_rate_override, 0.0) if ltv_rate_override is not None else rule.ltv_rate
    loan_amount_by_ltv = int(sale_price * applied_ltv_rate)

    if rule.max_loan_amount is None:
        capped_loan_amount = loan_amount_by_ltv
    else:
        capped_loan_amount = min(loan_amount_by_ltv, rule.max_loan_amount)

    final_loan_amount = (
        final_loan_amount_override if final_loan_amount_override is not None else capped_loan_amount
    )

    return {
        "rule_version": rule.rule_version,
        "rule_description": rule.description,
        "region_type": rule.region_type,
        "buyer_type": rule.buyer_type,
        "purpose": rule.purpose,
        "applied_ltv_rate": applied_ltv_rate,
        "applied_dsr_rate": rule.dsr_rate,
        "max_loan_amount": rule.max_loan_amount,
        "loan_amount_by_ltv": loan_amount_by_ltv,
        "capped_loan_amount": capped_loan_amount,
        "final_loan_amount": final_loan_amount,
        "ltv_source": "수동 입력" if ltv_rate_override is not None else "규칙 적용",
        "loan_amount_source": "수동 입력" if final_loan_amount_override is not None else "규칙 적용",
    }
