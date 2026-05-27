from __future__ import annotations

from modules.utils.money_utils import format_won


def build_analysis_summary(
    *,
    complex_name: str,
    listing: dict,
    finance_profile: dict,
    expected_jeonse_price: int,
    required_cash: int,
    shortage_cash: int,
    bargain_result: dict,
    decision: str,
) -> str:
    return (
        f"단지: {complex_name}\n"
        f"매물가: {format_won(listing['sale_price'])}\n"
        f"예상 전세가: {format_won(expected_jeonse_price)}\n"
        f"필요 현금: {format_won(required_cash)}\n"
        f"보유 현금: {format_won(finance_profile['cash_amount'])}\n"
        f"부족 현금: {format_won(shortage_cash)}\n"
        f"급매 점수: {bargain_result['score']}점 ({bargain_result['grade']})\n"
        f"판정: {decision}"
    )
