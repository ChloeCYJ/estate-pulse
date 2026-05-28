from __future__ import annotations


def format_won(value: int | float | None) -> str:
    amount = int(value or 0)
    return f"{amount:,}원"


def format_compact_won(value: int | float | None) -> str:
    amount = int(value or 0)

    if abs(amount) >= 100_000_000:
        return f"{amount / 100_000_000:.1f}억"
    if abs(amount) >= 10_000:
        return f"{amount / 10_000:.0f}만"
    return f"{amount:,}원"


def to_eok(value: int | float | None) -> float:
    amount = float(value or 0)
    return amount / 100_000_000


def from_eok(value: int | float | None) -> int:
    amount = float(value or 0)
    return int(round(amount * 100_000_000))
