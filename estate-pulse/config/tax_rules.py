from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaxBracket:
    max_sale_price: int | None
    acquisition_tax_rate: float


@dataclass(frozen=True)
class TaxRule:
    version: str
    rule_name: str
    effective_from: str
    effective_to: str | None
    description: str
    local_education_tax_rate: float
    brackets: tuple[TaxBracket, ...]


DEFAULT_TAX_RULE_VERSION = "2026.05-estimate"


TAX_RULES: dict[str, TaxRule] = {
    DEFAULT_TAX_RULE_VERSION: TaxRule(
        version=DEFAULT_TAX_RULE_VERSION,
        rule_name="Residential Acquisition Tax Estimate",
        effective_from="2026-05-01",
        effective_to=None,
        description="Residential estimate for a single-home standard purchase.",
        local_education_tax_rate=0.10,
        brackets=(
            TaxBracket(max_sale_price=600_000_000, acquisition_tax_rate=0.010),
            TaxBracket(max_sale_price=900_000_000, acquisition_tax_rate=0.020),
            TaxBracket(max_sale_price=None, acquisition_tax_rate=0.030),
        ),
    ),
}


def get_tax_rule(version: str | None = None) -> TaxRule:
    target_version = version or DEFAULT_TAX_RULE_VERSION
    try:
        return TAX_RULES[target_version]
    except KeyError as exc:
        raise ValueError(f"Unknown tax rule version: {target_version}") from exc


def get_tax_rules() -> list[TaxRule]:
    return list(TAX_RULES.values())
