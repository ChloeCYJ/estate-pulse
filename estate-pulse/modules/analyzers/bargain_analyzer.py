from __future__ import annotations

from modules.utils.score_utils import classify_bargain_score


def calculate_bargain_score(
    sale_price: int,
    recent_avg_price: int,
    one_year_high_price: int,
    expected_jeonse_price: int,
    required_cash: int,
    user_cash: int,
) -> dict:
    if sale_price <= 0:
        raise ValueError("sale_price must be greater than zero")
    if recent_avg_price <= 0:
        raise ValueError("recent_avg_price must be greater than zero")
    if one_year_high_price <= 0:
        raise ValueError("one_year_high_price must be greater than zero")

    score = 0
    reasons: list[str] = []

    discount_rate = (recent_avg_price - sale_price) / recent_avg_price * 100
    drop_from_high = (one_year_high_price - sale_price) / one_year_high_price * 100
    jeonse_ratio = expected_jeonse_price / sale_price * 100 if expected_jeonse_price else 0.0

    if discount_rate >= 10:
        score += 30
        reasons.append("최근 평균 실거래가 대비 10% 이상 낮습니다.")
    elif discount_rate >= 5:
        score += 20
        reasons.append("최근 평균 실거래가 대비 5% 이상 낮습니다.")
    elif discount_rate >= 3:
        score += 10
        reasons.append("최근 평균 실거래가 대비 3% 이상 낮습니다.")

    if drop_from_high >= 20:
        score += 20
        reasons.append("최근 1년 최고가 대비 20% 이상 하락했습니다.")
    elif drop_from_high >= 10:
        score += 10
        reasons.append("최근 1년 최고가 대비 10% 이상 하락했습니다.")

    if jeonse_ratio >= 70:
        score += 15
        reasons.append("전세가율이 70% 이상입니다.")
    elif jeonse_ratio >= 60:
        score += 10
        reasons.append("전세가율이 60% 이상입니다.")

    if user_cash >= required_cash:
        score += 15
        reasons.append("현재 보유 현금으로 투자 가능합니다.")
    else:
        reasons.append("현재 보유 현금만으로는 투자할 수 없습니다.")

    return {
        "score": min(score, 100),
        "grade": classify_bargain_score(score),
        "discount_rate": discount_rate,
        "drop_from_high": drop_from_high,
        "jeonse_ratio": jeonse_ratio,
        "reasons": reasons,
    }
