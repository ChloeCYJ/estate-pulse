from __future__ import annotations

from modules.utils.money_utils import format_won


def build_analysis_summary(
    *,
    primary_user_mode: str,
    complex_name: str,
    listing: dict,
    finance_profile: dict,
    expected_jeonse_price: int,
    required_cash: int,
    shortage_cash: int,
    bargain_result: dict,
    decision: str,
    monthly_repayment: int | None = None,
    dsr: float | None = None,
    remaining_cash_after_purchase: int | None = None,
    gap_amount: int | None = None,
    estimated_investment_efficiency: float | None = None,
    jeonse_ratio: float | None = None,
) -> str:
    if primary_user_mode == "OWNER_OCCUPIED":
        monthly_repayment_text = (
            format_won(monthly_repayment) if monthly_repayment is not None else "소득/금리 정보가 없어 계산하지 못했습니다."
        )
        dsr_text = f"{dsr:.1f}%" if dsr is not None else "소득 정보가 없어 계산하지 못했습니다."
        remaining_cash_text = (
            format_won(remaining_cash_after_purchase)
            if remaining_cash_after_purchase is not None
            else "계산 정보 없음"
        )
        return (
            f"단지: {complex_name}\n"
            f"매매가: {format_won(listing['sale_price'])}\n"
            f"총 필요 자기자본: {format_won(required_cash)}\n"
            f"추가 필요 현금: {format_won(shortage_cash)}\n"
            f"예상 월 상환액: {monthly_repayment_text}\n"
            f"예상 DSR: {dsr_text}\n"
            f"매수 후 남는 현금: {remaining_cash_text}\n"
            f"판단: {decision}"
        )

    efficiency_text = (
        f"{estimated_investment_efficiency:.2f}배"
        if estimated_investment_efficiency is not None
        else "계산 불가"
    )
    return (
        f"단지: {complex_name}\n"
        f"매매가: {format_won(listing['sale_price'])}\n"
        f"예상 전세가: {format_won(expected_jeonse_price)}\n"
        f"갭 금액: {format_won(gap_amount)}\n"
        f"전세가율: {jeonse_ratio:.1f}%\n"
        f"총 필요 자기자본: {format_won(required_cash)}\n"
        f"추가 필요 현금: {format_won(shortage_cash)}\n"
        f"투자 효율: {efficiency_text}\n"
        f"급매 점수: {bargain_result['score']}점 ({bargain_result['grade']})\n"
        f"판단: {decision}"
    )
