from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrokerageBracket:
    max_sale_price: int | None
    fee_rate: float


@dataclass(frozen=True)
class BrokerageRule:
    version: str
    rule_name: str
    effective_from: str
    effective_to: str | None
    description: str
    legal_fee_fixed: int
    reserve_cost_rate: float
    brackets: tuple[BrokerageBracket, ...]


DEFAULT_BROKERAGE_RULE_VERSION = "2026.05-estimate"


BROKERAGE_RULES: dict[str, BrokerageRule] = {
    DEFAULT_BROKERAGE_RULE_VERSION: BrokerageRule(
        version=DEFAULT_BROKERAGE_RULE_VERSION,
        rule_name="Residential Brokerage and Closing Cost Estimate",
        effective_from="2026-05-01",
        effective_to=None,
        description="Residential brokerage and closing-cost estimate.",
        legal_fee_fixed=300_000,
        reserve_cost_rate=0.005,
        brackets=(
            BrokerageBracket(max_sale_price=500_000_000, fee_rate=0.004),
            BrokerageBracket(max_sale_price=900_000_000, fee_rate=0.005),
            BrokerageBracket(max_sale_price=None, fee_rate=0.007),
        ),
    ),
}


def get_brokerage_rule(version: str | None = None) -> BrokerageRule:
    target_version = version or DEFAULT_BROKERAGE_RULE_VERSION
    try:
        return BROKERAGE_RULES[target_version]
    except KeyError as exc:
        raise ValueError(f"Unknown brokerage rule version: {target_version}") from exc


def get_brokerage_rules() -> list[BrokerageRule]:
    return list(BROKERAGE_RULES.values())
