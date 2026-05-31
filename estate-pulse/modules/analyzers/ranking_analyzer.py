from __future__ import annotations

from config.scoring_rules import (
    COMPLEX_GRADE_TO_SCORE,
    OVERALL_INVESTMENT_SCORE_RULE_VERSION,
    OVERALL_INVESTMENT_WEIGHTS,
)


def calculate_required_cash_efficiency(*, required_cash: int, sale_price: int) -> float:
    """Return a 0-100 score where lower required cash earns a higher score."""
    if sale_price <= 0:
        raise ValueError("sale_price must be greater than zero")
    ratio = max(0.0, min(1.0, 1 - (max(required_cash, 0) / sale_price)))
    return ratio * 100


def calculate_overall_investment_score(
    *,
    bargain_score: int,
    liquidity_score: int,
    complex_grade: str,
    required_cash: int,
    sale_price: int,
    shortage_cash: int,
) -> dict:
    """Return a weighted investment score across price, liquidity, grade, and cash efficiency."""
    cash_efficiency = calculate_required_cash_efficiency(
        required_cash=required_cash,
        sale_price=sale_price,
    )
    complex_grade_score = COMPLEX_GRADE_TO_SCORE.get(complex_grade, 20)
    weighted_score = (
        bargain_score * OVERALL_INVESTMENT_WEIGHTS["bargain_score"]
        + liquidity_score * OVERALL_INVESTMENT_WEIGHTS["liquidity_score"]
        + complex_grade_score * OVERALL_INVESTMENT_WEIGHTS["complex_grade"]
        + cash_efficiency * OVERALL_INVESTMENT_WEIGHTS["required_cash_efficiency"]
    )
    shortage_penalty = min(20, max(shortage_cash, 0) / max(sale_price, 1) * 100)
    investment_score = round(max(0.0, min(100.0, weighted_score - shortage_penalty)))

    return {
        "investment_score": investment_score,
        "required_cash_efficiency_score": round(cash_efficiency, 2),
        "complex_grade_score": complex_grade_score,
        "rule_version": OVERALL_INVESTMENT_SCORE_RULE_VERSION,
        "shortage_penalty": round(shortage_penalty, 2),
    }
