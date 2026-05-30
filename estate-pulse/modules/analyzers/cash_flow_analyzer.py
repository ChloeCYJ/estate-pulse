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


def calculate_acquisition_cost_total(
    *,
    acquisition_tax: int,
    brokerage_fee: int,
    legal_fee: int,
    repair_cost: int,
    contingency_fee: int,
) -> int:
    """Return the total acquisition-related costs."""
    return (
        int(acquisition_tax)
        + int(brokerage_fee)
        + int(legal_fee)
        + int(repair_cost)
        + int(contingency_fee)
    )


def calculate_investment_scenario_cash(
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
    """Return required-cash outputs for the requested investment scenario."""
    sale_price = int(sale_price)
    estimated_loan = int(estimated_loan)
    acquisition_cost_total = int(acquisition_cost_total)
    expected_jeonse_price = int(expected_jeonse_price or 0)
    takeover_jeonse_deposit = int(takeover_jeonse_deposit or 0)
    rent_deposit = int(rent_deposit or 0)
    expected_monthly_rent = int(expected_monthly_rent or 0)

    if investment_type == "OWNER_OCCUPIED":
        required_cash = sale_price - estimated_loan + acquisition_cost_total
        return {
            "investment_type": investment_type,
            "required_cash": required_cash,
            "current_required_cash": required_cash,
            "future_required_cash": None,
            "monthly_cash_flow": None,
            "scenario_explanation": "실거주 시나리오로 계산되어 전세보증금은 차감하지 않았습니다.",
        }

    if investment_type == "GAP_INVESTMENT":
        required_cash = sale_price - estimated_loan - expected_jeonse_price + acquisition_cost_total
        return {
            "investment_type": investment_type,
            "required_cash": required_cash,
            "current_required_cash": required_cash,
            "future_required_cash": None,
            "monthly_cash_flow": None,
            "scenario_explanation": "갭투자 시나리오로 계산되어 예상 전세가를 차감했습니다.",
        }

    if investment_type == "JEONSE_TAKEOVER":
        required_cash = sale_price - estimated_loan - takeover_jeonse_deposit + acquisition_cost_total
        return {
            "investment_type": investment_type,
            "required_cash": required_cash,
            "current_required_cash": required_cash,
            "future_required_cash": None,
            "monthly_cash_flow": None,
            "scenario_explanation": "전세 승계 시나리오로 계산되어 인수 전세보증금을 차감했습니다.",
        }

    if investment_type == "MONTHLY_RENT":
        required_cash = sale_price - estimated_loan - rent_deposit + acquisition_cost_total
        return {
            "investment_type": investment_type,
            "required_cash": required_cash,
            "current_required_cash": required_cash,
            "future_required_cash": None,
            "monthly_cash_flow": expected_monthly_rent,
            "scenario_explanation": "월세 임대 시나리오로 계산되어 임대보증금을 차감하고 월세 현금흐름을 함께 표시합니다.",
        }

    if investment_type == "FUTURE_MOVE_IN":
        current_required_cash = sale_price - estimated_loan - expected_jeonse_price + acquisition_cost_total
        future_required_cash = sale_price - estimated_loan + acquisition_cost_total
        return {
            "investment_type": investment_type,
            "required_cash": current_required_cash,
            "current_required_cash": current_required_cash,
            "future_required_cash": future_required_cash,
            "monthly_cash_flow": None,
            "scenario_explanation": "현재는 임차보증금을 반영하고, 추후 실입주 시 필요한 현금을 별도로 계산했습니다.",
        }

    raise ValueError("지원하지 않는 투자 시나리오입니다.")


def calculate_shortage_cash(required_cash: int, cash_amount: int) -> int:
    return int(required_cash) - int(cash_amount)


def calculate_jeonse_ratio(expected_jeonse_price: int, sale_price: int) -> float:
    if sale_price <= 0:
        raise ValueError("sale_price must be greater than zero")
    return expected_jeonse_price / sale_price * 100 if expected_jeonse_price else 0.0
