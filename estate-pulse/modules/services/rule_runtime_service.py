from __future__ import annotations

import json
from datetime import date, timedelta

from config.brokerage_rules import BrokerageBracket, BrokerageRule, get_brokerage_rules
from config.loan_rules import LoanRule, get_loan_rules
from config.tax_rules import TaxBracket, TaxRule, get_tax_rules


class RuleRuntimeService:
    def __init__(self, *, rule_candidate_repository) -> None:
        self.rule_candidate_repository = rule_candidate_repository

    def get_active_loan_rules(self) -> list[LoanRule]:
        active_rules = list(get_loan_rules())
        for candidate in self.rule_candidate_repository.list_applied_by_type("LOAN"):
            proposed_rule = _deserialize_loan_rule(json.loads(candidate["proposed_rule_json"]))
            previous_rule_json = candidate.get("previous_rule_json")
            if previous_rule_json:
                previous_rule = _deserialize_loan_rule(json.loads(previous_rule_json))
                active_rules = _overlay_previous_loan_rule(
                    active_rules=active_rules,
                    previous_rule=previous_rule,
                    proposed_rule=proposed_rule,
                )
            else:
                active_rules = [item for item in active_rules if not _same_loan_identity(item, proposed_rule)]
            active_rules = [item for item in active_rules if not _same_loan_identity(item, proposed_rule)]
            active_rules.append(proposed_rule)
        return sorted(
            active_rules,
            key=lambda item: (
                item.effective_from,
                item.region_type,
                item.buyer_type,
                item.purpose,
                item.house_price_min,
            ),
        )

    def get_active_tax_rules(self) -> list[TaxRule]:
        rules = {rule.version: rule for rule in get_tax_rules()}
        for candidate in self.rule_candidate_repository.list_applied_by_type("TAX"):
            rule = _deserialize_tax_rule(json.loads(candidate["proposed_rule_json"]))
            rules[rule.version] = rule
        return list(rules.values())

    def get_active_brokerage_rules(self) -> list[BrokerageRule]:
        rules = {rule.version: rule for rule in get_brokerage_rules()}
        for candidate in self.rule_candidate_repository.list_applied_by_type("BROKERAGE"):
            rule = _deserialize_brokerage_rule(json.loads(candidate["proposed_rule_json"]))
            rules[rule.version] = rule
        return list(rules.values())

    def get_active_tax_rule(
        self,
        *,
        rule_version: str | None = None,
        reference_date: date | None = None,
    ) -> TaxRule:
        rules = self.get_active_tax_rules()
        if rule_version:
            for rule in rules:
                if rule.version == rule_version:
                    return rule
            raise ValueError(f"Unknown tax rule version: {rule_version}")
        return _select_active_versioned_rule(rules, reference_date)

    def get_active_brokerage_rule(
        self,
        *,
        rule_version: str | None = None,
        reference_date: date | None = None,
    ) -> BrokerageRule:
        rules = self.get_active_brokerage_rules()
        if rule_version:
            for rule in rules:
                if rule.version == rule_version:
                    return rule
            raise ValueError(f"Unknown brokerage rule version: {rule_version}")
        return _select_active_versioned_rule(rules, reference_date)

    def serialize_active_loan_rules(self) -> list[dict]:
        return [_serialize_loan_rule(rule) for rule in self.get_active_loan_rules()]

    def serialize_active_tax_rules(self) -> list[dict]:
        return [_serialize_tax_rule(rule) for rule in self.get_active_tax_rules()]

    def serialize_active_brokerage_rules(self) -> list[dict]:
        return [_serialize_brokerage_rule(rule) for rule in self.get_active_brokerage_rules()]


def _select_active_versioned_rule(rules: list, reference_date: date | None):
    target_date = reference_date or date.today()
    matching_rules = [rule for rule in rules if _rule_effective(rule, target_date)]
    if not matching_rules:
        raise ValueError("No active rule matched the reference date.")
    matching_rules.sort(key=lambda item: item.effective_from, reverse=True)
    return matching_rules[0]


def _rule_effective(rule, target_date: date) -> bool:
    effective_from = date.fromisoformat(rule.effective_from)
    if target_date < effective_from:
        return False
    if rule.effective_to is None:
        return True
    return target_date <= date.fromisoformat(rule.effective_to)


def _same_loan_identity(left: LoanRule, right: LoanRule) -> bool:
    return (
        left.region_type == right.region_type
        and left.buyer_type == right.buyer_type
        and left.purpose == right.purpose
        and left.house_price_min == right.house_price_min
        and left.house_price_max == right.house_price_max
        and left.effective_from == right.effective_from
        and left.effective_to == right.effective_to
    )


def _overlay_previous_loan_rule(
    *,
    active_rules: list[LoanRule],
    previous_rule: LoanRule,
    proposed_rule: LoanRule,
) -> list[LoanRule]:
    next_rules: list[LoanRule] = []
    proposed_start = date.fromisoformat(proposed_rule.effective_from)
    for item in active_rules:
        if not _same_loan_identity(item, previous_rule):
            next_rules.append(item)
            continue

        previous_start = date.fromisoformat(item.effective_from)
        if proposed_start <= previous_start:
            continue

        adjusted_end = proposed_start - timedelta(days=1)
        if item.effective_to is not None:
            original_end = date.fromisoformat(item.effective_to)
            if adjusted_end > original_end:
                adjusted_end = original_end
        if adjusted_end < previous_start:
            continue
        next_rules.append(
            LoanRule(
                rule_version=item.rule_version,
                effective_from=item.effective_from,
                effective_to=adjusted_end.isoformat(),
                region_type=item.region_type,
                buyer_type=item.buyer_type,
                purpose=item.purpose,
                house_price_min=item.house_price_min,
                house_price_max=item.house_price_max,
                ltv_rate=item.ltv_rate,
                dsr_rate=item.dsr_rate,
                max_loan_amount=item.max_loan_amount,
                description=item.description,
            )
        )
    return next_rules


def _serialize_loan_rule(rule: LoanRule) -> dict:
    return {
        "rule_version": rule.rule_version,
        "effective_from": rule.effective_from,
        "effective_to": rule.effective_to,
        "region_type": rule.region_type,
        "buyer_type": rule.buyer_type,
        "purpose": rule.purpose,
        "house_price_min": rule.house_price_min,
        "house_price_max": rule.house_price_max,
        "ltv_rate": rule.ltv_rate,
        "dsr_rate": rule.dsr_rate,
        "max_loan_amount": rule.max_loan_amount,
        "description": rule.description,
    }


def _deserialize_loan_rule(payload: dict) -> LoanRule:
    return LoanRule(
        rule_version=str(payload["rule_version"]),
        effective_from=str(payload["effective_from"]),
        effective_to=payload.get("effective_to"),
        region_type=str(payload["region_type"]),
        buyer_type=str(payload["buyer_type"]),
        purpose=str(payload["purpose"]),
        house_price_min=int(payload["house_price_min"]),
        house_price_max=None if payload.get("house_price_max") is None else int(payload["house_price_max"]),
        ltv_rate=float(payload["ltv_rate"]),
        dsr_rate=float(payload["dsr_rate"]),
        max_loan_amount=None if payload.get("max_loan_amount") is None else int(payload["max_loan_amount"]),
        description=str(payload["description"]),
    )


def _serialize_tax_rule(rule: TaxRule) -> dict:
    return {
        "version": rule.version,
        "rule_name": rule.rule_name,
        "effective_from": rule.effective_from,
        "effective_to": rule.effective_to,
        "description": rule.description,
        "local_education_tax_rate": rule.local_education_tax_rate,
        "brackets": [
            {
                "max_sale_price": item.max_sale_price,
                "acquisition_tax_rate": item.acquisition_tax_rate,
            }
            for item in rule.brackets
        ],
    }


def _deserialize_tax_rule(payload: dict) -> TaxRule:
    return TaxRule(
        version=str(payload["version"]),
        rule_name=str(payload["rule_name"]),
        effective_from=str(payload["effective_from"]),
        effective_to=payload.get("effective_to"),
        description=str(payload["description"]),
        local_education_tax_rate=float(payload["local_education_tax_rate"]),
        brackets=tuple(
            TaxBracket(
                max_sale_price=None if item.get("max_sale_price") is None else int(item["max_sale_price"]),
                acquisition_tax_rate=float(item["acquisition_tax_rate"]),
            )
            for item in payload.get("brackets", [])
        ),
    )


def _serialize_brokerage_rule(rule: BrokerageRule) -> dict:
    return {
        "version": rule.version,
        "rule_name": rule.rule_name,
        "effective_from": rule.effective_from,
        "effective_to": rule.effective_to,
        "description": rule.description,
        "legal_fee_fixed": rule.legal_fee_fixed,
        "reserve_cost_rate": rule.reserve_cost_rate,
        "brackets": [
            {
                "max_sale_price": item.max_sale_price,
                "fee_rate": item.fee_rate,
            }
            for item in rule.brackets
        ],
    }


def _deserialize_brokerage_rule(payload: dict) -> BrokerageRule:
    return BrokerageRule(
        version=str(payload["version"]),
        rule_name=str(payload["rule_name"]),
        effective_from=str(payload["effective_from"]),
        effective_to=payload.get("effective_to"),
        description=str(payload["description"]),
        legal_fee_fixed=int(payload["legal_fee_fixed"]),
        reserve_cost_rate=float(payload["reserve_cost_rate"]),
        brackets=tuple(
            BrokerageBracket(
                max_sale_price=None if item.get("max_sale_price") is None else int(item["max_sale_price"]),
                fee_rate=float(item["fee_rate"]),
            )
            for item in payload.get("brackets", [])
        ),
    )
