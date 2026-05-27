from __future__ import annotations

import calendar
from datetime import date, datetime


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
        if cutoff_date <= _parse_transaction_date(item) <= target_date
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
