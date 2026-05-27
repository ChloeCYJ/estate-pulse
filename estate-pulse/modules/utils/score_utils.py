from __future__ import annotations


def classify_bargain_score(score: int) -> str:
    if score >= 80:
        return "강한 급매 후보"
    if score >= 65:
        return "검토 가치 있음"
    if score >= 50:
        return "보통"
    return "급매 아님"
