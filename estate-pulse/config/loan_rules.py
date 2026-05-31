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


RULE_VERSION = "2026.05-v2"
RULE_EFFECTIVE_FROM = "2026-05-01"

HOUSE_PRICE_BRACKETS: tuple[tuple[int, int | None], ...] = (
    (0, 899_999_999),
    (900_000_000, 1_499_999_999),
    (1_500_000_000, 2_499_999_999),
    (2_500_000_000, None),
)

def _build_rules(
    *,
    region_type: str,
    buyer_type: str,
    purpose: str,
    ltv_rates: tuple[float, float, float, float],
    dsr_rate: float,
    max_loan_amounts: tuple[int | None, int | None, int | None, int | None],
    description_prefix: str,
) -> list[LoanRule]:
    rules: list[LoanRule] = []
    for index, (house_price_min, house_price_max) in enumerate(HOUSE_PRICE_BRACKETS):
        rules.append(
            LoanRule(
                rule_version=RULE_VERSION,
                effective_from=RULE_EFFECTIVE_FROM,
                effective_to=None,
                region_type=region_type,
                buyer_type=buyer_type,
                purpose=purpose,
                house_price_min=house_price_min,
                house_price_max=house_price_max,
                ltv_rate=ltv_rates[index],
                dsr_rate=dsr_rate,
                max_loan_amount=max_loan_amounts[index],
                description=f"{description_prefix} / {_price_band_label(house_price_min, house_price_max)}",
            )
        )
    return rules


def _price_band_label(house_price_min: int, house_price_max: int | None) -> str:
    if house_price_max is None:
        return "over 2.5B"
    if house_price_max <= 899_999_999:
        return "under 900M"
    if house_price_max <= 1_499_999_999:
        return "900M to 1.5B"
    return "1.5B to 2.5B"


LOAN_RULES: list[LoanRule] = [
    *_build_rules(
        region_type="NON_REGULATED",
        buyer_type="NO_HOME",
        purpose="OWNER_OCCUPIED",
        ltv_rates=(0.70, 0.60, 0.50, 0.40),
        dsr_rate=0.40,
        max_loan_amounts=(None, None, None, None),
        description_prefix="Non-regulated / no-home / owner-occupied",
    ),
    *_build_rules(
        region_type="NON_REGULATED",
        buyer_type="NO_HOME",
        purpose="INVESTMENT",
        ltv_rates=(0.70, 0.60, 0.50, 0.40),
        dsr_rate=0.40,
        max_loan_amounts=(None, None, 1_000_000_000, 1_200_000_000),
        description_prefix="Non-regulated / no-home / investment",
    ),
    *_build_rules(
        region_type="REGULATED",
        buyer_type="NO_HOME",
        purpose="OWNER_OCCUPIED",
        ltv_rates=(0.50, 0.40, 0.30, 0.20),
        dsr_rate=0.40,
        max_loan_amounts=(600_000_000, 600_000_000, 600_000_000, 600_000_000),
        description_prefix="Regulated / no-home / owner-occupied",
    ),
    *_build_rules(
        region_type="REGULATED",
        buyer_type="NO_HOME",
        purpose="INVESTMENT",
        ltv_rates=(0.40, 0.30, 0.20, 0.10),
        dsr_rate=0.40,
        max_loan_amounts=(500_000_000, 500_000_000, 500_000_000, 500_000_000),
        description_prefix="Regulated / no-home / investment",
    ),
    *_build_rules(
        region_type="REGULATED",
        buyer_type="ONE_HOME",
        purpose="OWNER_OCCUPIED",
        ltv_rates=(0.40, 0.30, 0.20, 0.10),
        dsr_rate=0.40,
        max_loan_amounts=(500_000_000, 500_000_000, 500_000_000, 500_000_000),
        description_prefix="Regulated / one-home / owner-occupied",
    ),
    *_build_rules(
        region_type="REGULATED",
        buyer_type="ONE_HOME",
        purpose="INVESTMENT",
        ltv_rates=(0.30, 0.20, 0.10, 0.00),
        dsr_rate=0.40,
        max_loan_amounts=(400_000_000, 400_000_000, 400_000_000, 0),
        description_prefix="Regulated / one-home / investment",
    ),
    *_build_rules(
        region_type="REGULATED",
        buyer_type="MULTI_HOME",
        purpose="INVESTMENT",
        ltv_rates=(0.00, 0.00, 0.00, 0.00),
        dsr_rate=0.40,
        max_loan_amounts=(0, 0, 0, 0),
        description_prefix="Regulated / multi-home / investment",
    ),
]


def get_loan_rules() -> list[LoanRule]:
    return LOAN_RULES.copy()
