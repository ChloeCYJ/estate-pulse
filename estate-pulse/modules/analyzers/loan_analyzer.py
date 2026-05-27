from __future__ import annotations


def estimate_loan_amount(sale_price: int, ltv_limit: float) -> int:
    return int(sale_price * max(ltv_limit, 0))
