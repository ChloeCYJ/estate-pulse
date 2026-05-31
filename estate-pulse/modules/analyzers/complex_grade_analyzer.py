from __future__ import annotations

from config.scoring_rules import COMPLEX_GRADE_LABELS, COMPLEX_GRADE_RULE_VERSION


def calculate_complex_grade(
    *,
    household_count: int | None,
    building_age: int | None,
    recent_sale_transaction_count: int,
    recent_rent_transaction_count: int,
    average_sale_price_rank: int | None,
    price_per_area_rank: int | None,
    region_complex_count: int,
    liquidity_score: int,
) -> dict:
    """Return a complex grade using scale, age, price rank, and liquidity."""
    household_count = int(household_count or 0)
    building_age = int(building_age or 99)
    sale_count = int(recent_sale_transaction_count)
    rent_count = int(recent_rent_transaction_count)
    total_score = (
        _score_household_count(household_count)
        + _score_building_age(building_age)
        + _score_transaction_count(sale_count)
        + _score_transaction_count(rent_count)
        + _score_rank(average_sale_price_rank, region_complex_count)
        + _score_rank(price_per_area_rank, region_complex_count)
        + _score_liquidity(liquidity_score)
    )
    grade = _resolve_grade(
        household_count=household_count,
        sale_count=sale_count,
        rent_count=rent_count,
        liquidity_score=liquidity_score,
        total_score=total_score,
    )

    return {
        "grade": grade,
        "label": COMPLEX_GRADE_LABELS[grade],
        "score": total_score,
        "rule_version": COMPLEX_GRADE_RULE_VERSION,
        "inputs": {
            "household_count": household_count,
            "building_age": building_age,
            "recent_sale_transaction_count": sale_count,
            "recent_rent_transaction_count": rent_count,
            "average_sale_price_rank": average_sale_price_rank,
            "price_per_area_rank": price_per_area_rank,
            "region_complex_count": region_complex_count,
            "liquidity_score": liquidity_score,
        },
    }


def _score_household_count(household_count: int) -> int:
    if household_count >= 1_500:
        return 20
    if household_count >= 700:
        return 16
    if household_count >= 300:
        return 12
    if household_count >= 150:
        return 8
    return 4


def _score_building_age(building_age: int) -> int:
    if building_age <= 10:
        return 15
    if building_age <= 20:
        return 12
    if building_age <= 30:
        return 8
    return 4


def _score_transaction_count(transaction_count: int) -> int:
    if transaction_count >= 18:
        return 15
    if transaction_count >= 10:
        return 12
    if transaction_count >= 6:
        return 8
    if transaction_count >= 3:
        return 4
    return 1


def _score_rank(rank: int | None, total_count: int) -> int:
    if rank is None or total_count <= 1:
        return 8
    percentile = (total_count - rank) / max(total_count - 1, 1)
    if percentile >= 0.80:
        return 15
    if percentile >= 0.60:
        return 12
    if percentile >= 0.40:
        return 8
    if percentile >= 0.20:
        return 4
    return 1


def _score_liquidity(liquidity_score: int) -> int:
    if liquidity_score >= 80:
        return 15
    if liquidity_score >= 60:
        return 10
    if liquidity_score >= 40:
        return 5
    return 1


def _resolve_grade(
    *,
    household_count: int,
    sale_count: int,
    rent_count: int,
    liquidity_score: int,
    total_score: int,
) -> str:
    if liquidity_score < 35:
        return "RISKY"
    if household_count < 150 and sale_count < 2 and rent_count < 2:
        return "RISKY"
    if household_count < 300 and liquidity_score < 60:
        return "SMALL" if total_score >= 35 else "RISKY"
    if total_score >= 90:
        return "LEADER"
    if total_score >= 72:
        return "SUB_LEADER"
    if total_score >= 50:
        return "NORMAL"
    if total_score >= 35:
        return "SMALL"
    return "RISKY"
