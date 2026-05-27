from __future__ import annotations


def format_won(value: int | float | None) -> str:
    amount = int(value or 0)
    return f"{amount:,}원"
