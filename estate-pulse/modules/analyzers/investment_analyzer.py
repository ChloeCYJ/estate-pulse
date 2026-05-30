from __future__ import annotations

from modules.analyzers.cash_flow_analyzer import calculate_investment_scenario_cash


def calculate_investment_metrics(
    *,
    investment_type: str,
    sale_price: int,
    estimated_loan: int,
    acquisition_cost_total: int,
    expected_jeonse_price: int = 0,
    takeover_jeonse_deposit: int = 0,
    rent_deposit: int = 0,
    expected_monthly_rent: int = 0,
) -> dict:
    """Return gap-investment metrics while preserving internal scenario support."""
    scenario_result = calculate_investment_scenario_cash(
        investment_type=investment_type,
        sale_price=sale_price,
        estimated_loan=estimated_loan,
        acquisition_cost_total=acquisition_cost_total,
        expected_jeonse_price=expected_jeonse_price,
        takeover_jeonse_deposit=takeover_jeonse_deposit,
        rent_deposit=rent_deposit,
        expected_monthly_rent=expected_monthly_rent,
    )

    gap_base_amount = _resolve_gap_base_amount(
        investment_type=investment_type,
        expected_jeonse_price=expected_jeonse_price,
        takeover_jeonse_deposit=takeover_jeonse_deposit,
        rent_deposit=rent_deposit,
    )
    gap_amount = max(int(sale_price) - gap_base_amount, 0)
    estimated_investment_efficiency = calculate_investment_efficiency(
        sale_price=int(sale_price),
        required_cash=int(scenario_result["required_cash"]),
    )

    return {
        **scenario_result,
        "gap_amount": gap_amount,
        "estimated_investment_efficiency": estimated_investment_efficiency,
    }


def calculate_investment_efficiency(*, sale_price: int, required_cash: int) -> float | None:
    """Return the asset multiple secured per unit of required equity."""
    if required_cash <= 0:
        return None
    return sale_price / required_cash


def _resolve_gap_base_amount(
    *,
    investment_type: str,
    expected_jeonse_price: int,
    takeover_jeonse_deposit: int,
    rent_deposit: int,
) -> int:
    if investment_type == "JEONSE_TAKEOVER":
        return int(takeover_jeonse_deposit or 0)
    if investment_type == "MONTHLY_RENT":
        return int(rent_deposit or 0)
    return int(expected_jeonse_price or 0)
