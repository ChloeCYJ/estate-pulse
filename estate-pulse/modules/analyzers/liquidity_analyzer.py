from __future__ import annotations

from config.scoring_rules import LIQUIDITY_RULE_VERSION, LIQUIDITY_SCORE_RULES
from modules.analyzers.transaction_analyzer import filter_recent_transactions


def calculate_liquidity_score(
    *,
    sale_transactions: list[dict],
    rent_transactions: list[dict],
    reference_date=None,
) -> dict:
    """Return a 0-100 liquidity score using recent sale/rent activity."""
    months = int(LIQUIDITY_SCORE_RULES["recent_window_months"])
    recent_sale_transactions = filter_recent_transactions(
        sale_transactions,
        months=months,
        reference_date=reference_date,
    )
    recent_rent_transactions = filter_recent_transactions(
        rent_transactions,
        months=months,
        reference_date=reference_date,
    )

    sale_count = len(recent_sale_transactions)
    rent_count = len(recent_rent_transactions)
    active_months = _count_active_months(recent_sale_transactions + recent_rent_transactions)
    score = round(
        _weighted_score(
            sale_count=sale_count,
            rent_count=rent_count,
            active_months=active_months,
        )
    )
    band = _classify_liquidity_score(score)

    return {
        "score": max(0, min(score, 100)),
        "band": band["band"],
        "label": band["label"],
        "rule_version": LIQUIDITY_RULE_VERSION,
        "recent_sale_transaction_count": sale_count,
        "recent_rent_transaction_count": rent_count,
        "active_months": active_months,
        "transaction_frequency": round((sale_count + rent_count) / months, 2),
    }


def _weighted_score(*, sale_count: int, rent_count: int, active_months: int) -> float:
    sale_weight = float(LIQUIDITY_SCORE_RULES["weights"]["sale_count"])
    rent_weight = float(LIQUIDITY_SCORE_RULES["weights"]["rent_count"])
    active_month_weight = float(LIQUIDITY_SCORE_RULES["weights"]["active_months"])

    sale_score = min(sale_count, int(LIQUIDITY_SCORE_RULES["sale_count_full_score"])) / int(
        LIQUIDITY_SCORE_RULES["sale_count_full_score"]
    )
    rent_score = min(rent_count, int(LIQUIDITY_SCORE_RULES["rent_count_full_score"])) / int(
        LIQUIDITY_SCORE_RULES["rent_count_full_score"]
    )
    active_month_score = min(
        active_months,
        int(LIQUIDITY_SCORE_RULES["active_months_full_score"]),
    ) / int(LIQUIDITY_SCORE_RULES["active_months_full_score"])

    return (
        sale_score * sale_weight
        + rent_score * rent_weight
        + active_month_score * active_month_weight
    )


def _count_active_months(transactions: list[dict]) -> int:
    active_months = {
        f"{item['deal_year']:04d}-{item['deal_month']:02d}"
        if "deal_year" in item
        else str(item["deal_date"])[:7]
        for item in transactions
    }
    return len(active_months)


def _classify_liquidity_score(score: int) -> dict:
    for minimum, band, label in LIQUIDITY_SCORE_RULES["bands"]:
        if score >= minimum:
            return {"band": band, "label": label}
    return {"band": "CAUTION", "label": "liquidity caution"}
