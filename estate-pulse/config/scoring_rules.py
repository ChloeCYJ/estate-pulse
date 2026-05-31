from __future__ import annotations


LIQUIDITY_RULE_VERSION = "2026.05-liquidity"
LIQUIDITY_SCORE_RULES = {
    "recent_window_months": 12,
    "sale_count_full_score": 12,
    "rent_count_full_score": 12,
    "active_months_full_score": 8,
    "weights": {
        "sale_count": 40,
        "rent_count": 30,
        "active_months": 30,
    },
    "bands": (
        (80, "HIGH", "high liquidity"),
        (60, "NORMAL", "normal liquidity"),
        (0, "CAUTION", "liquidity caution"),
    ),
}

COMPLEX_GRADE_RULE_VERSION = "2026.05-complex-grade"
COMPLEX_GRADE_LABELS = {
    "LEADER": "대장",
    "SUB_LEADER": "준대장",
    "NORMAL": "일반",
    "SMALL": "나홀로",
    "RISKY": "유동성주의",
}
COMPLEX_GRADE_TO_SCORE = {
    "LEADER": 100,
    "SUB_LEADER": 85,
    "NORMAL": 65,
    "SMALL": 45,
    "RISKY": 20,
}

OVERALL_INVESTMENT_SCORE_RULE_VERSION = "2026.05-investment-score"
OVERALL_INVESTMENT_WEIGHTS = {
    "bargain_score": 0.35,
    "liquidity_score": 0.25,
    "complex_grade": 0.20,
    "required_cash_efficiency": 0.20,
}

RANKING_TYPES = {
    "bargain_score": {
        "label": "최고 급매 점수",
        "field": "bargain_score",
        "ascending": False,
    },
    "required_cash": {
        "label": "최저 필요 현금",
        "field": "required_cash",
        "ascending": True,
    },
    "shortage_cash": {
        "label": "최저 부족 현금",
        "field": "shortage_cash",
        "ascending": True,
    },
    "jeonse_ratio": {
        "label": "최고 전세가율",
        "field": "jeonse_ratio",
        "ascending": False,
    },
    "liquidity_score": {
        "label": "최고 유동성",
        "field": "liquidity_score",
        "ascending": False,
    },
    "investment_score": {
        "label": "최고 종합 투자 점수",
        "field": "investment_score",
        "ascending": False,
    },
}
