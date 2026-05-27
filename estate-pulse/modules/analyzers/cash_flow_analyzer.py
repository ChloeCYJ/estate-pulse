from __future__ import annotations


def calculate_required_cash(
    *,
    sale_price: int,
    expected_loan_amount: int,
    expected_jeonse_price: int,
    acquisition_tax: int,
    brokerage_fee: int,
    legal_fee: int,
    repair_cost: int,
    contingency_fee: int,
) -> int:
    return (
        int(sale_price)
        - int(expected_loan_amount)
        - int(expected_jeonse_price)
        + int(acquisition_tax)
        + int(brokerage_fee)
        + int(legal_fee)
        + int(repair_cost)
        + int(contingency_fee)
    )


def calculate_shortage_cash(required_cash: int, cash_amount: int) -> int:
    return int(required_cash) - int(cash_amount)


def calculate_jeonse_ratio(expected_jeonse_price: int, sale_price: int) -> float:
    if sale_price <= 0:
        raise ValueError("sale_price must be greater than zero")
    return expected_jeonse_price / sale_price * 100 if expected_jeonse_price else 0.0
