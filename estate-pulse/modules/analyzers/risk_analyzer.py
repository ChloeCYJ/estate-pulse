from __future__ import annotations


def summarize_risk(*, shortage_cash: int, jeonse_ratio: float) -> list[str]:
    risks: list[str] = []
    if shortage_cash > 0:
        risks.append("실행을 위해 추가 현금이 필요합니다.")
    if jeonse_ratio >= 80:
        risks.append("전세가율이 높아 역전세 리스크를 점검할 필요가 있습니다.")
    return risks
