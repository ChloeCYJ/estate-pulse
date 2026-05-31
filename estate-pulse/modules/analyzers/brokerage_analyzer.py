from __future__ import annotations

from config.brokerage_rules import BrokerageRule, get_brokerage_rule


def calculate_brokerage_breakdown(
    *,
    sale_price: int,
    rule_version: str | None = None,
    rule: BrokerageRule | None = None,
    brokerage_fee_override: int | None = None,
    legal_fee_override: int | None = None,
    reserve_cost_override: int | None = None,
) -> dict:
    """Return brokerage-related cost estimates with rule-version metadata."""
    rule = rule or get_brokerage_rule(rule_version)
    default_brokerage_fee = calculate_brokerage_fee_by_rule(
        sale_price=sale_price,
        rule=rule,
    )
    brokerage_fee = (
        int(brokerage_fee_override)
        if brokerage_fee_override is not None
        else default_brokerage_fee
    )
    legal_fee = (
        int(legal_fee_override) if legal_fee_override is not None else int(rule.legal_fee_fixed)
    )
    default_reserve_cost = int(int(sale_price) * rule.reserve_cost_rate)
    reserve_cost = (
        int(reserve_cost_override)
        if reserve_cost_override is not None
        else default_reserve_cost
    )
    manual_override = any(
        value is not None
        for value in (brokerage_fee_override, legal_fee_override, reserve_cost_override)
    )

    return {
        "brokerage_fee": brokerage_fee,
        "legal_fee": legal_fee,
        "reserve_cost": reserve_cost,
        "total_brokerage_cost": brokerage_fee + legal_fee + reserve_cost,
        "applied_brokerage_rule_version": _decorate_rule_version(
            rule.version,
            manual_override=manual_override,
        ),
        "rule_description": rule.description,
        "manual_override": manual_override,
    }


def calculate_brokerage_fee_by_rule(*, sale_price: int, rule: BrokerageRule) -> int:
    """Return the brokerage fee using configured sale-price brackets."""
    target_price = int(sale_price)
    for bracket in rule.brackets:
        if bracket.max_sale_price is None or target_price <= bracket.max_sale_price:
            return int(target_price * bracket.fee_rate)
    raise ValueError("No brokerage bracket matched the sale price.")


def _decorate_rule_version(version: str, *, manual_override: bool) -> str:
    if manual_override:
        return f"{version}+manual"
    return version
