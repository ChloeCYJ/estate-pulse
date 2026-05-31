from __future__ import annotations

import math


def format_won(value: int | float | None) -> str:
    amount = _safe_int(value)
    return f"{amount:,}원"


def format_compact_won(value: int | float | None) -> str:
    amount = _safe_int(value)

    if abs(amount) >= 100_000_000:
        return f"{amount / 100_000_000:.1f}억"
    if abs(amount) >= 10_000:
        return f"{amount / 10_000:.0f}만"
    return f"{amount:,}원"


def to_eok(value: int | float | None) -> float:
    amount = _safe_float(value)
    return amount / 100_000_000


def from_eok(value: int | float | None) -> int:
    amount = _safe_float(value)
    return int(round(amount * 100_000_000))


def _safe_int(value: int | float | None) -> int:
    if _is_missing_number(value):
        return 0
    return int(value)


def _safe_float(value: int | float | None) -> float:
    if _is_missing_number(value):
        return 0.0
    return float(value)


def _is_missing_number(value: int | float | None) -> bool:
    if value is None:
        return True

    try:
        if value != value:
            return True
    except TypeError:
        pass

    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False
