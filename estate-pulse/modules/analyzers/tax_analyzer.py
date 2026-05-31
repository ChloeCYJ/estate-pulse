from __future__ import annotations

from config.tax_rules import TaxRule, get_tax_rule


def calculate_acquisition_tax(sale_price: int, tax_rate: float) -> int:
    """Return a simple acquisition-tax amount using the provided rate."""
    return int(int(sale_price) * float(tax_rate))


def calculate_tax_breakdown(
    *,
    sale_price: int,
    rule_version: str | None = None,
    rule: TaxRule | None = None,
    acquisition_tax_override: int | None = None,
    local_education_tax_override: int | None = None,
) -> dict:
    """Return acquisition and local education tax estimates with rule tracking."""
    rule = rule or get_tax_rule(rule_version)
    default_acquisition_tax = calculate_acquisition_tax_by_rule(
        sale_price=sale_price,
        rule=rule,
    )
    acquisition_tax = (
        int(acquisition_tax_override)
        if acquisition_tax_override is not None
        else default_acquisition_tax
    )
    default_local_education_tax = int(acquisition_tax * rule.local_education_tax_rate)
    local_education_tax = (
        int(local_education_tax_override)
        if local_education_tax_override is not None
        else default_local_education_tax
    )
    manual_override = (
        acquisition_tax_override is not None or local_education_tax_override is not None
    )

    return {
        "acquisition_tax": acquisition_tax,
        "local_education_tax": local_education_tax,
        "total_tax": acquisition_tax + local_education_tax,
        "applied_tax_rule_version": _decorate_rule_version(
            rule.version,
            manual_override=manual_override,
        ),
        "rule_description": rule.description,
        "manual_override": manual_override,
    }


def calculate_acquisition_tax_by_rule(*, sale_price: int, rule: TaxRule) -> int:
    """Return the acquisition tax based on configured sale-price brackets."""
    target_price = int(sale_price)
    for bracket in rule.brackets:
        if bracket.max_sale_price is None or target_price <= bracket.max_sale_price:
            return int(target_price * bracket.acquisition_tax_rate)
    raise ValueError("No acquisition tax bracket matched the sale price.")


def _decorate_rule_version(version: str, *, manual_override: bool) -> str:
    if manual_override:
        return f"{version}+manual"
    return version
