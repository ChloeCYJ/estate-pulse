from __future__ import annotations


def calculate_acquisition_tax(sale_price: int, tax_rate: float) -> int:
    return int(sale_price * tax_rate)


def calculate_brokerage_fee(sale_price: int, fee_rate: float) -> int:
    return int(sale_price * fee_rate)


def calculate_contingency_fee(sale_price: int, contingency_rate: float) -> int:
    return int(sale_price * contingency_rate)
