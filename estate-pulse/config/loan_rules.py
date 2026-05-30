from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class LoanRule:
    rule_version: str
    effective_from: str
    effective_to: str | None
    region_type: str
    buyer_type: str
    purpose: str
    house_price_min: int
    house_price_max: int | None
    ltv_rate: float
    dsr_rate: float
    max_loan_amount: int | None
    description: str

    def is_effective_on(self, target_date: date) -> bool:
        effective_from = date.fromisoformat(self.effective_from)
        if target_date < effective_from:
            return False
        if self.effective_to is None:
            return True
        return target_date <= date.fromisoformat(self.effective_to)

    def matches_price(self, sale_price: int) -> bool:
        if sale_price < self.house_price_min:
            return False
        if self.house_price_max is None:
            return True
        return sale_price <= self.house_price_max


LOAN_RULES: list[LoanRule] = [
    LoanRule(
        rule_version="2026.05-v1",
        effective_from="2026-01-01",
        effective_to=None,
        region_type="NON_REGULATED",
        buyer_type="NO_HOME",
        purpose="OWNER_OCCUPIED",
        house_price_min=0,
        house_price_max=900_000_000,
        ltv_rate=0.70,
        dsr_rate=0.40,
        max_loan_amount=None,
        description="비규제지역 무주택 실거주, 9억 이하",
    ),
    LoanRule(
        rule_version="2026.05-v1",
        effective_from="2026-01-01",
        effective_to=None,
        region_type="NON_REGULATED",
        buyer_type="NO_HOME",
        purpose="OWNER_OCCUPIED",
        house_price_min=900_000_001,
        house_price_max=None,
        ltv_rate=0.60,
        dsr_rate=0.40,
        max_loan_amount=None,
        description="비규제지역 무주택 실거주, 9억 초과",
    ),
    LoanRule(
        rule_version="2026.05-v1",
        effective_from="2026-01-01",
        effective_to=None,
        region_type="NON_REGULATED",
        buyer_type="NO_HOME",
        purpose="INVESTMENT",
        house_price_min=0,
        house_price_max=900_000_000,
        ltv_rate=0.70,
        dsr_rate=0.40,
        max_loan_amount=None,
        description="비규제지역 무주택 투자, 9억 이하",
    ),
    LoanRule(
        rule_version="2026.05-v1",
        effective_from="2026-01-01",
        effective_to=None,
        region_type="NON_REGULATED",
        buyer_type="NO_HOME",
        purpose="INVESTMENT",
        house_price_min=900_000_001,
        house_price_max=None,
        ltv_rate=0.60,
        dsr_rate=0.40,
        max_loan_amount=None,
        description="비규제지역 무주택 투자, 9억 초과",
    ),
    LoanRule(
        rule_version="2026.05-v1",
        effective_from="2026-01-01",
        effective_to=None,
        region_type="REGULATED",
        buyer_type="NO_HOME",
        purpose="OWNER_OCCUPIED",
        house_price_min=0,
        house_price_max=None,
        ltv_rate=0.50,
        dsr_rate=0.40,
        max_loan_amount=600_000_000,
        description="규제지역 무주택 실거주",
    ),
    LoanRule(
        rule_version="2026.05-v1",
        effective_from="2026-01-01",
        effective_to=None,
        region_type="REGULATED",
        buyer_type="NO_HOME",
        purpose="INVESTMENT",
        house_price_min=0,
        house_price_max=None,
        ltv_rate=0.40,
        dsr_rate=0.40,
        max_loan_amount=500_000_000,
        description="규제지역 무주택 투자",
    ),
    LoanRule(
        rule_version="2026.05-v1",
        effective_from="2026-01-01",
        effective_to=None,
        region_type="REGULATED",
        buyer_type="ONE_HOME",
        purpose="OWNER_OCCUPIED",
        house_price_min=0,
        house_price_max=None,
        ltv_rate=0.40,
        dsr_rate=0.40,
        max_loan_amount=500_000_000,
        description="규제지역 1주택 실거주",
    ),
    LoanRule(
        rule_version="2026.05-v1",
        effective_from="2026-01-01",
        effective_to=None,
        region_type="REGULATED",
        buyer_type="ONE_HOME",
        purpose="INVESTMENT",
        house_price_min=0,
        house_price_max=None,
        ltv_rate=0.30,
        dsr_rate=0.40,
        max_loan_amount=400_000_000,
        description="규제지역 1주택 투자",
    ),
    LoanRule(
        rule_version="2026.05-v1",
        effective_from="2026-01-01",
        effective_to=None,
        region_type="REGULATED",
        buyer_type="MULTI_HOME",
        purpose="INVESTMENT",
        house_price_min=0,
        house_price_max=None,
        ltv_rate=0.00,
        dsr_rate=0.40,
        max_loan_amount=0,
        description="규제지역 다주택 투자",
    ),
]


def get_loan_rules() -> list[LoanRule]:
    return LOAN_RULES.copy()
