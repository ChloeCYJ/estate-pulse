from __future__ import annotations

import calendar
from datetime import date, datetime
import math


def calculate_recent_sale_average(
    sale_transactions: list[dict],
    *,
    months: int,
    reference_date: date | None = None,
) -> int | None:
    """Return the average sale price for transactions within the recent month window."""
    prices = [item["price"] for item in filter_recent_transactions(sale_transactions, months=months, reference_date=reference_date)]
    if not prices:
        return None
    return int(sum(prices) / len(prices))


def calculate_recent_3_month_sale_average(
    sale_transactions: list[dict], *, reference_date: date | None = None
) -> int | None:
    """Return the recent 3-month sale average."""
    return calculate_recent_sale_average(sale_transactions, months=3, reference_date=reference_date)


def calculate_recent_6_month_sale_average(
    sale_transactions: list[dict], *, reference_date: date | None = None
) -> int | None:
    """Return the recent 6-month sale average."""
    return calculate_recent_sale_average(sale_transactions, months=6, reference_date=reference_date)


def calculate_recent_12_month_sale_average(
    sale_transactions: list[dict], *, reference_date: date | None = None
) -> int | None:
    """Return the recent 12-month sale average."""
    return calculate_recent_sale_average(sale_transactions, months=12, reference_date=reference_date)


def calculate_one_year_high_sale_price(
    sale_transactions: list[dict], *, reference_date: date | None = None
) -> int | None:
    """Return the one-year high sale price."""
    prices = [item["price"] for item in filter_recent_transactions(sale_transactions, months=12, reference_date=reference_date)]
    return max(prices) if prices else None


def calculate_one_year_low_sale_price(
    sale_transactions: list[dict], *, reference_date: date | None = None
) -> int | None:
    """Return the one-year low sale price."""
    prices = [item["price"] for item in filter_recent_transactions(sale_transactions, months=12, reference_date=reference_date)]
    return min(prices) if prices else None


def calculate_latest_rent_deposit_average(
    rent_transactions: list[dict],
    *,
    limit: int = 3,
    reference_date: date | None = None,
) -> int | None:
    """Return the average deposit across the most recent rent transactions."""
    recent_transactions = filter_recent_transactions(
        rent_transactions,
        months=12,
        reference_date=reference_date,
    )
    if not recent_transactions:
        return None

    sorted_transactions = sorted(
        recent_transactions,
        key=lambda item: _parse_transaction_date(item),
        reverse=True,
    )
    deposits = [item["deposit"] for item in sorted_transactions[:limit] if item.get("deposit") is not None]
    if not deposits:
        return None
    return int(sum(deposits) / len(deposits))


def calculate_jeonse_ratio_from_rent_data(sale_price: int, rent_deposit_average: int | None) -> float:
    """Return the jeonse ratio using rent transaction data."""
    if not rent_deposit_average:
        return 0.0
    if sale_price <= 0:
        raise ValueError("sale_price must be greater than zero")
    return rent_deposit_average / sale_price * 100


def calculate_discount_rate_vs_recent_sale_average(
    sale_price: int,
    recent_sale_average: int | None,
) -> float:
    """Return the discount rate versus the recent sale average."""
    if not recent_sale_average:
        return 0.0
    return (recent_sale_average - sale_price) / recent_sale_average * 100


def calculate_drop_rate_from_one_year_high(
    sale_price: int,
    one_year_high_sale_price: int | None,
) -> float:
    """Return the drop rate from the one-year high sale price."""
    if not one_year_high_sale_price:
        return 0.0
    return (one_year_high_sale_price - sale_price) / one_year_high_sale_price * 100


def calculate_reference_price_metadata(
    sale_transactions: list[dict],
    *,
    reference_date: date | None = None,
) -> dict | None:
    """Build recent-transaction reference price metadata for one complex/area bucket."""
    target_date = reference_date or date.today()
    sample_transactions = _select_reference_sample_transactions(
        sale_transactions,
        reference_date=target_date,
    )
    if not sample_transactions:
        return None

    reference_price = _weighted_median_price(
        sample_transactions,
        reference_date=target_date,
    )
    latest_transaction = max(sample_transactions, key=_parse_transaction_date)
    latest_transaction_date = _parse_transaction_date(latest_transaction)
    latest_transaction_price = int(latest_transaction["price"])
    prices = [int(item["price"]) for item in sample_transactions]

    return {
        "reference_price": reference_price,
        "sample_count": len(sample_transactions),
        "latest_transaction_date": latest_transaction_date.isoformat(),
        "latest_transaction_price": latest_transaction_price,
        "sample_min_price": min(prices),
        "sample_max_price": max(prices),
        "confidence": _reference_confidence(
            sample_count=len(sample_transactions),
            latest_transaction_date=latest_transaction_date,
            reference_date=target_date,
        ),
        "volatility_status": _reference_volatility_status(
            sample_transactions=sample_transactions,
            reference_price=reference_price,
        ),
    }


def filter_recent_transactions(
    transactions: list[dict],
    *,
    months: int,
    reference_date: date | None = None,
) -> list[dict]:
    target_date = reference_date or date.today()
    cutoff_date = _subtract_months(target_date, months)
    return [
        item
        for item in transactions
        if not _is_canceled_transaction(item)
        if cutoff_date <= _parse_transaction_date(item) <= target_date
    ]


def filter_recent_transactions_by_days(
    transactions: list[dict],
    *,
    days: int,
    reference_date: date | None = None,
) -> list[dict]:
    target_date = reference_date or date.today()
    return [
        item
        for item in transactions
        if not _is_canceled_transaction(item)
        if 0 <= (target_date - _parse_transaction_date(item)).days <= days
    ]


def _parse_transaction_date(transaction: dict) -> date:
    if transaction.get("deal_date"):
        return datetime.fromisoformat(str(transaction["deal_date"])).date()
    return date(
        int(transaction["deal_year"]),
        int(transaction["deal_month"]),
        int(transaction["deal_day"]),
    )


def _subtract_months(target_date: date, months: int) -> date:
    month_index = target_date.month - months
    year = target_date.year
    while month_index <= 0:
        month_index += 12
        year -= 1

    day = min(target_date.day, calendar.monthrange(year, month_index)[1])
    return date(year, month_index, day)


def _select_reference_sample_transactions(
    sale_transactions: list[dict],
    *,
    reference_date: date,
) -> list[dict]:
    for window_days in (90, 180, 270, 365):
        sample_transactions = filter_recent_transactions_by_days(
            sale_transactions,
            days=window_days,
            reference_date=reference_date,
        )
        if len(sample_transactions) >= 3:
            return sample_transactions

    fallback_transactions = filter_recent_transactions_by_days(
        sale_transactions,
        days=365,
        reference_date=reference_date,
    )
    return fallback_transactions if fallback_transactions else []


def _weighted_median_price(
    sale_transactions: list[dict],
    *,
    reference_date: date,
) -> int:
    weighted_prices = sorted(
        (
            (
                int(item["price"]),
                math.exp(
                    -math.log(2)
                    * (reference_date - _parse_transaction_date(item)).days
                    / 45
                ),
            )
            for item in sale_transactions
        ),
        key=lambda item: item[0],
    )
    total_weight = sum(weight for _, weight in weighted_prices)
    half_weight = total_weight / 2
    cumulative_weight = 0.0
    for price, weight in weighted_prices:
        cumulative_weight += weight
        if cumulative_weight >= half_weight:
            return price
    return weighted_prices[-1][0]


def _reference_confidence(
    *,
    sample_count: int,
    latest_transaction_date: date,
    reference_date: date,
) -> str:
    if sample_count <= 2:
        return "LOW"
    latest_age_days = (reference_date - latest_transaction_date).days
    if sample_count >= 3 and latest_age_days <= 60:
        return "HIGH"
    if sample_count >= 3 and latest_age_days <= 90:
        return "MEDIUM"
    return "LOW"


def _reference_volatility_status(
    *,
    sample_transactions: list[dict],
    reference_price: int,
) -> str:
    if len(sample_transactions) < 2 or reference_price <= 0:
        return "INSUFFICIENT_DATA"

    latest_transaction = max(sample_transactions, key=_parse_transaction_date)
    latest_transaction_price = int(latest_transaction["price"])
    change_rate = (latest_transaction_price - reference_price) / reference_price * 100
    if change_rate >= 5:
        return "RAPID_RISE"
    if change_rate <= -5:
        return "RAPID_FALL"
    return "STABLE"


def _is_canceled_transaction(transaction: dict) -> bool:
    return bool(
        transaction.get("is_canceled")
        or transaction.get("is_cancelled")
        or transaction.get("cancelled")
        or transaction.get("canceled")
        or transaction.get("canceled_at")
        or transaction.get("cancelled_at")
        or transaction.get("cancel_date")
    )
