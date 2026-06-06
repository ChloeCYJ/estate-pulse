from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from modules.utils.money_utils import format_won

LOAN_REGION_TYPE_OPTIONS = (
    "NON_REGULATED",
    "LAND_TRANSACTION_PERMISSION",
    "SPECULATION_OVERHEATED_DISTRICT",
    "ADJUSTMENT_TARGET_AREA",
)
SUPPORTED_LOAN_REGION_TYPES = (
    "NON_REGULATED",
    "REGULATED",
    "LAND_TRANSACTION_PERMISSION",
    "SPECULATION_OVERHEATED_DISTRICT",
    "ADJUSTMENT_TARGET_AREA",
)
_UNSET = object()


class RuleAdminService:
    def __init__(
        self,
        *,
        rule_runtime_service,
        region_policy_service=None,
        policy_event_service=None,
        policy_import_repository=None,
        rule_candidate_repository=None,
    ) -> None:
        self.rule_runtime_service = rule_runtime_service
        self.region_policy_service = region_policy_service
        self.policy_event_service = policy_event_service
        self.policy_import_repository = policy_import_repository
        self.rule_candidate_repository = rule_candidate_repository

    def list_loan_rules(
        self,
        *,
        reference_date: date | None = None,
        current_only: bool = True,
    ) -> list[dict[str, str]]:
        editable_candidate_ids = _editable_loan_candidate_ids(self.rule_candidate_repository)
        rows: list[dict[str, str]] = []
        rules = self.rule_runtime_service.get_active_loan_rules()
        display_rules = (
            _select_display_loan_rules(rules, reference_date=reference_date)
            if current_only
            else _sort_all_loan_rules_for_display(rules)
        )
        for rule in display_rules:
            rule_payload = _loan_rule_payload(rule)
            candidate_id = editable_candidate_ids.get(_loan_rule_identity_key(rule))
            rows.append(
                {
                    "rule_version": rule.rule_version,
                    "rule_name": _loan_rule_display_name(rule),
                    "effective_from": rule.effective_from,
                    "effective_to": rule.effective_to or "-",
                    "state": _loan_rule_state_label(rule_payload, reference_date or date.today()),
                    "investment_purpose": _purpose_label(rule.purpose),
                    "region_type": _region_type_label(rule.region_type),
                    "buyer_type": _buyer_type_label(rule.buyer_type),
                    "house_price_range": _format_price_range(rule.house_price_min, rule.house_price_max),
                    "ltv_rate": _format_ratio(rule.ltv_rate),
                    "dsr_rate": _format_ratio(rule.dsr_rate),
                    "max_loan_amount": _format_money_or_unlimited(rule.max_loan_amount),
                    "conditions": _loan_conditions(rule.purpose, rule.region_type, rule.buyer_type),
                    "description": rule.description,
                    "_candidate_id": candidate_id,
                    "_editable": candidate_id is not None,
                    "_rule_payload": rule_payload,
                }
            )
        return rows

    def list_editable_loan_rules(self) -> list[dict]:
        if self.rule_candidate_repository is None:
            return []

        rows: list[dict] = []
        for candidate in self.rule_candidate_repository.list_applied_by_type("LOAN"):
            payload = json.loads(candidate["proposed_rule_json"])
            rows.append(
                {
                    "candidate_id": int(candidate["id"]),
                    "rule_version": str(payload["rule_version"]),
                    "description": str(payload["description"]),
                    "effective_from": str(payload["effective_from"]),
                    "effective_to": payload.get("effective_to"),
                    "region_type": str(payload["region_type"]),
                    "buyer_type": str(payload["buyer_type"]),
                    "purpose": str(payload["purpose"]),
                    "house_price_min": int(payload["house_price_min"]),
                    "house_price_max": (
                        None if payload.get("house_price_max") is None else int(payload["house_price_max"])
                    ),
                    "ltv_rate": float(payload["ltv_rate"]),
                    "dsr_rate": float(payload["dsr_rate"]),
                    "max_loan_amount": (
                        None if payload.get("max_loan_amount") is None else int(payload["max_loan_amount"])
                    ),
                    "label": (
                        f"#{candidate['id']} | "
                        f"{_loan_rule_name(payload['purpose'], payload['region_type'], payload['buyer_type'])} | "
                        f"{payload['effective_from']} | {payload['description']}"
                    ),
                    "is_current": _rule_payload_is_current(payload, date.today()),
                    "state": _loan_rule_state_label(payload, date.today()),
                }
            )
        return rows

    def list_loan_region_types(self) -> list[str]:
        return list(LOAN_REGION_TYPE_OPTIONS)

    def list_loan_rule_versions(self) -> list[str]:
        versions = {str(rule.rule_version) for rule in self.rule_runtime_service.get_active_loan_rules()}
        return sorted(versions)

    def create_manual_loan_rule(
        self,
        *,
        rule_version: str,
        effective_from: str,
        effective_to: str | None,
        region_type: str,
        buyer_type: str,
        purpose: str,
        house_price_min: int,
        house_price_max: int | None,
        ltv_rate: float,
        dsr_rate: float,
        max_loan_amount: int | None,
        description: str,
    ) -> int:
        if self.policy_import_repository is None or self.rule_candidate_repository is None:
            raise ValueError("Manual loan rule registration is unavailable.")

        payload = _normalize_manual_loan_rule(
            rule_version=rule_version,
            effective_from=effective_from,
            effective_to=effective_to,
            region_type=region_type,
            buyer_type=buyer_type,
            purpose=purpose,
            house_price_min=house_price_min,
            house_price_max=house_price_max,
            ltv_rate=ltv_rate,
            dsr_rate=dsr_rate,
            max_loan_amount=max_loan_amount,
            description=description,
        )
        policy_import_id = self.policy_import_repository.create(
            source_text=f"관리자 수동 대출 규칙 등록: {payload['description']}",
            source_name="관리자 수동 입력",
            target_rule_type="LOAN",
            effective_date=payload["effective_from"],
            parser_name="manual_admin",
            parser_status="APPLIED",
        )
        return self.rule_candidate_repository.create(
            policy_import_id=policy_import_id,
            target_rule_type="LOAN",
            rule_name=_loan_rule_name(
                payload["purpose"],
                payload["region_type"],
                payload["buyer_type"],
            ),
            rule_version=payload["rule_version"],
            previous_rule_json=None,
            proposed_rule_json=json.dumps(payload, ensure_ascii=False, sort_keys=True),
            changed_fields_json=json.dumps(
                [
                    "region_type",
                    "buyer_type",
                    "purpose",
                    "house_price_min",
                    "house_price_max",
                    "ltv_rate",
                    "dsr_rate",
                    "max_loan_amount",
                ],
                ensure_ascii=False,
            ),
            confidence=1.0,
            warnings="관리자 수동 등록 규칙입니다. 기존 가격 구간과 겹치면 더 최신/구체적인 룰이 우선 적용됩니다.",
            status="APPLIED",
        )

    def update_applied_loan_rule(
        self,
        *,
        candidate_id: int,
        rule_version: str,
        effective_from: str,
        effective_to: str | None,
        region_type: str,
        buyer_type: str,
        purpose: str,
        house_price_min: int,
        house_price_max: int | None,
        ltv_rate: float,
        dsr_rate: float,
        max_loan_amount: int | None,
        description: str,
    ) -> None:
        if self.rule_candidate_repository is None:
            raise ValueError("Applied loan rule update is unavailable.")

        candidate = self.rule_candidate_repository.get(candidate_id)
        if not candidate or str(candidate.get("target_rule_type")) != "LOAN":
            raise ValueError("Editable loan rule candidate was not found.")

        previous_payload = json.loads(candidate["proposed_rule_json"])
        payload = _normalize_manual_loan_rule(
            rule_version=rule_version,
            effective_from=effective_from,
            effective_to=effective_to,
            region_type=region_type,
            buyer_type=buyer_type,
            purpose=purpose,
            house_price_min=house_price_min,
            house_price_max=house_price_max,
            ltv_rate=ltv_rate,
            dsr_rate=dsr_rate,
            max_loan_amount=max_loan_amount,
            description=description,
        )
        self.rule_candidate_repository.update_candidate_payload(
            candidate_id=candidate_id,
            proposed_rule_json=json.dumps(payload, ensure_ascii=False, sort_keys=True),
            changed_fields_json=json.dumps(
                [
                    "region_type",
                    "buyer_type",
                    "purpose",
                    "house_price_min",
                    "house_price_max",
                    "ltv_rate",
                    "dsr_rate",
                    "max_loan_amount",
                    "description",
                    "effective_from",
                    "effective_to",
                ],
                ensure_ascii=False,
            ),
            warnings=json.dumps(
                ["관리자 수정 규칙입니다. 기존 적용 규칙을 덮어씁니다."],
                ensure_ascii=False,
            ),
            confidence=1.0,
            rule_name=_loan_rule_name(
                payload["purpose"],
                payload["region_type"],
                payload["buyer_type"],
            ),
            rule_version=payload["rule_version"],
        )

    def create_loan_rule_override(
        self,
        *,
        previous_rule: dict,
        rule_version: str,
        effective_from: str,
        effective_to: str | None,
        region_type: str,
        buyer_type: str,
        purpose: str,
        house_price_min: int,
        house_price_max: int | None,
        ltv_rate: float,
        dsr_rate: float,
        max_loan_amount: int | None,
        description: str,
    ) -> int:
        if self.policy_import_repository is None or self.rule_candidate_repository is None:
            raise ValueError("Loan rule override is unavailable.")

        previous_payload = _loan_rule_payload(previous_rule)
        payload = _normalize_manual_loan_rule(
            rule_version=rule_version,
            effective_from=effective_from,
            effective_to=effective_to,
            region_type=region_type,
            buyer_type=buyer_type,
            purpose=purpose,
            house_price_min=house_price_min,
            house_price_max=house_price_max,
            ltv_rate=ltv_rate,
            dsr_rate=dsr_rate,
            max_loan_amount=max_loan_amount,
            description=description,
        )
        policy_import_id = self.policy_import_repository.create(
            source_text=f"관리자 대출 규칙 override: {payload['description']}",
            source_name="관리자 직접 수정",
            target_rule_type="LOAN",
            effective_date=payload["effective_from"],
            parser_name="manual_admin_override",
            parser_status="APPLIED",
        )
        return self.rule_candidate_repository.create(
            policy_import_id=policy_import_id,
            target_rule_type="LOAN",
            rule_name=_loan_rule_name(
                payload["purpose"],
                payload["region_type"],
                payload["buyer_type"],
            ),
            rule_version=payload["rule_version"],
            previous_rule_json=json.dumps(previous_payload, ensure_ascii=False, sort_keys=True),
            proposed_rule_json=json.dumps(payload, ensure_ascii=False, sort_keys=True),
            changed_fields_json=json.dumps(
                [
                    "region_type",
                    "buyer_type",
                    "purpose",
                    "house_price_min",
                    "house_price_max",
                    "ltv_rate",
                    "dsr_rate",
                    "max_loan_amount",
                    "description",
                    "effective_from",
                    "effective_to",
                ],
                ensure_ascii=False,
            ),
            confidence=1.0,
            warnings=json.dumps(
                ["기본 내장 대출 규칙을 대체하는 관리자 override입니다."],
                ensure_ascii=False,
            ),
            status="APPLIED",
        )

    def delete_applied_loan_rule(self, candidate_id: int) -> None:
        if self.rule_candidate_repository is None:
            raise ValueError("Applied loan rule deletion is unavailable.")

        candidate = self.rule_candidate_repository.get(candidate_id)
        if not candidate or str(candidate.get("target_rule_type")) != "LOAN":
            raise ValueError("Editable loan rule candidate was not found.")
        self.rule_candidate_repository.delete(candidate_id)

    def delete_applied_loan_rules(self, candidate_ids: list[int]) -> int:
        deleted_count = 0
        for candidate_id in dict.fromkeys(int(item) for item in candidate_ids):
            candidate = self.rule_candidate_repository.get(candidate_id) if self.rule_candidate_repository else None
            if not candidate or str(candidate.get("target_rule_type")) != "LOAN":
                continue
            self.rule_candidate_repository.delete(candidate_id)
            deleted_count += 1
        return deleted_count

    def deactivate_loan_rule(
        self,
        *,
        selected_summary: dict,
        inactive_from: str,
    ) -> None:
        inactive_end = (date.fromisoformat(inactive_from) - timedelta(days=1)).isoformat()
        candidate_id = selected_summary.get("_candidate_id")
        payload = dict(selected_summary["_rule_payload"])
        if candidate_id is None:
            self.create_loan_rule_override(
                previous_rule=payload,
                rule_version=payload["rule_version"],
                effective_from=payload["effective_from"],
                effective_to=inactive_end,
                region_type=payload["region_type"],
                buyer_type=payload["buyer_type"],
                purpose=payload["purpose"],
                house_price_min=payload["house_price_min"],
                house_price_max=payload["house_price_max"],
                ltv_rate=payload["ltv_rate"],
                dsr_rate=payload["dsr_rate"],
                max_loan_amount=payload["max_loan_amount"],
                description=payload["description"],
            )
            return

        self.update_applied_loan_rule(
            candidate_id=int(candidate_id),
            rule_version=str(payload["rule_version"]),
            effective_from=str(payload["effective_from"]),
            effective_to=inactive_end,
            region_type=str(payload["region_type"]),
            buyer_type=str(payload["buyer_type"]),
            purpose=str(payload["purpose"]),
            house_price_min=int(payload["house_price_min"]),
            house_price_max=payload["house_price_max"],
            ltv_rate=float(payload["ltv_rate"]),
            dsr_rate=float(payload["dsr_rate"]),
            max_loan_amount=payload["max_loan_amount"],
            description=str(payload["description"]),
        )

    def filter_editable_loan_rules(
        self,
        *,
        rule_version: str | None = None,
        purpose: str | None = None,
        region_type: str | None = None,
        buyer_type: str | None = None,
        current_only: bool | None = None,
        state: str | None = None,
        reference_date: date | None = None,
    ) -> list[dict]:
        target_date = reference_date or date.today()
        rows = self.list_editable_loan_rules()
        filtered: list[dict] = []
        for row in rows:
            if rule_version and str(row["rule_version"]) != rule_version:
                continue
            if purpose and str(row["purpose"]) != purpose:
                continue
            if region_type and str(row["region_type"]) != region_type:
                continue
            if buyer_type and str(row["buyer_type"]) != buyer_type:
                continue
            is_current = _rule_payload_is_current(row, target_date)
            if current_only is True and not is_current:
                continue
            if current_only is False and is_current:
                continue
            if state and _loan_rule_state_label(row, target_date) != state:
                continue
            filtered.append(row)
        return filtered

    def bulk_update_applied_loan_rules(
        self,
        *,
        candidate_ids: list[int],
        rule_version: str | None = None,
        ltv_rate: float | None = None,
        dsr_rate: float | None = None,
        max_loan_amount_changed: bool = False,
        max_loan_amount: int | None = None,
        effective_from_changed: bool = False,
        effective_from: str | None = None,
        effective_to_changed: bool = False,
        effective_to: str | None = None,
        description: str | None = None,
    ) -> int:
        updated_count = 0
        for candidate_id in dict.fromkeys(int(item) for item in candidate_ids):
            candidate = self.rule_candidate_repository.get(candidate_id) if self.rule_candidate_repository else None
            if not candidate or str(candidate.get("target_rule_type")) != "LOAN":
                continue
            payload = json.loads(candidate["proposed_rule_json"])
            self.update_applied_loan_rule(
                candidate_id=candidate_id,
                rule_version=rule_version or str(payload["rule_version"]),
                effective_from=(
                    effective_from if effective_from_changed and effective_from is not None else str(payload["effective_from"])
                ),
                effective_to=(
                    effective_to if effective_to_changed else payload.get("effective_to")
                ),
                region_type=str(payload["region_type"]),
                buyer_type=str(payload["buyer_type"]),
                purpose=str(payload["purpose"]),
                house_price_min=int(payload["house_price_min"]),
                house_price_max=(
                    None if payload.get("house_price_max") is None else int(payload["house_price_max"])
                ),
                ltv_rate=float(payload["ltv_rate"] if ltv_rate is None else ltv_rate),
                dsr_rate=float(payload["dsr_rate"] if dsr_rate is None else dsr_rate),
                max_loan_amount=(
                    max_loan_amount
                    if max_loan_amount_changed
                    else (None if payload.get("max_loan_amount") is None else int(payload["max_loan_amount"]))
                ),
                description=description or str(payload["description"]),
            )
            updated_count += 1
        return updated_count

    def list_loan_rule_conflicts(self, *, reference_date: date | None = None) -> list[dict]:
        target_date = reference_date or date.today()
        counts: dict[tuple, list] = {}
        for rule in self.rule_runtime_service.get_active_loan_rules():
            if not rule.is_effective_on(target_date):
                continue
            key = (
                rule.purpose,
                rule.region_type,
                rule.buyer_type,
                rule.house_price_min,
                rule.house_price_max,
            )
            counts.setdefault(key, []).append(rule)

        conflicts: list[dict] = []
        for rules in counts.values():
            if len(rules) < 2:
                continue
            sample = rules[0]
            conflicts.append(
                {
                    "rule_version": sample.rule_version,
                    "purpose": _purpose_label(sample.purpose),
                    "region_type": _region_type_label(sample.region_type),
                    "buyer_type": _buyer_type_label(sample.buyer_type),
                    "house_price_range": _format_price_range(sample.house_price_min, sample.house_price_max),
                    "count": len(rules),
                }
            )
        return conflicts

    def list_tax_rules(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for rule in self.rule_runtime_service.get_active_tax_rules():
            for bracket in rule.brackets:
                rows.append(
                    {
                        "rule_version": rule.version,
                        "rule_name": "취득세 추정 규칙",
                        "effective_from": rule.effective_from,
                        "effective_to": rule.effective_to or "-",
                        "conditions": _format_sale_price_condition(bracket.max_sale_price),
                        "rate_values": (
                            f"취득세 {_format_ratio(bracket.acquisition_tax_rate)}, "
                            f"지방교육세 {_format_ratio(rule.local_education_tax_rate)}"
                        ),
                        "limit_values": _tax_limit_value(bracket.max_sale_price),
                        "description": rule.description,
                    }
                )
        return rows

    def list_brokerage_rules(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for rule in self.rule_runtime_service.get_active_brokerage_rules():
            for bracket in rule.brackets:
                rows.append(
                    {
                        "rule_version": rule.version,
                        "rule_name": "중개보수/부대비용 추정 규칙",
                        "effective_from": rule.effective_from,
                        "effective_to": rule.effective_to or "-",
                        "conditions": _format_sale_price_condition(bracket.max_sale_price),
                        "rate_values": (
                            f"중개보수 {_format_ratio(bracket.fee_rate)}, "
                            f"예비비 {_format_ratio(rule.reserve_cost_rate)}"
                        ),
                        "limit_values": _brokerage_limit_value(
                            bracket.max_sale_price,
                            rule.legal_fee_fixed,
                        ),
                        "description": rule.description,
                    }
                )
        return rows

    def list_region_policy_statuses(self) -> list[dict[str, str]]:
        if self.region_policy_service is None:
            return []

        rows: list[dict[str, str]] = []
        for item in self.region_policy_service.list_region_policy_statuses():
            rows.append(
                {
                    "id": str(item["id"]),
                    "region_scope": str(item["region_scope"]),
                    "region_level": _region_level_label(str(item["region_level"])),
                    "sido": str(item["sido"]),
                    "sigungu": str(item.get("sigungu") or "-"),
                    "dong": str(item.get("dong") or "-"),
                    "policy_type": _policy_type_label(str(item["policy_type"])),
                    "loan_region_type": _region_type_label(
                        str(item["loan_region_type"] or "NON_REGULATED")
                    )
                    if item.get("loan_region_type") is not None
                    else "-",
                    "effective_from": str(item["effective_from"]),
                    "effective_to": str(item.get("effective_to") or "-"),
                    "notes": str(item.get("notes") or "-"),
                }
            )
        return rows

    def list_region_levels(self) -> list[str]:
        if self.region_policy_service is None:
            return []
        return self.region_policy_service.list_region_levels()

    def list_region_policy_types(self) -> list[str]:
        if self.region_policy_service is None:
            return []
        return self.region_policy_service.list_policy_types()

    def create_region_policy_status(self, **kwargs) -> int:
        if self.region_policy_service is None:
            raise ValueError("Region policy service is unavailable.")
        return self.region_policy_service.create_region_policy_status(**kwargs)

    def delete_region_policy_status(self, status_id: int) -> None:
        if self.region_policy_service is None:
            raise ValueError("Region policy service is unavailable.")
        self.region_policy_service.delete_region_policy_status(status_id)

    def list_policy_event_types(self) -> list[str]:
        if self.policy_event_service is None:
            return []
        return self.policy_event_service.list_policy_types()

    def list_policy_event_statuses(self) -> list[str]:
        if self.policy_event_service is None:
            return []
        return self.policy_event_service.list_statuses()

    def list_policy_event_impact_levels(self) -> list[str]:
        if self.policy_event_service is None:
            return []
        return self.policy_event_service.list_impact_levels()

    def list_policy_event_buyer_types(self) -> list[str]:
        if self.policy_event_service is None:
            return []
        return self.policy_event_service.list_buyer_types()

    def list_policy_event_investment_purposes(self) -> list[str]:
        if self.policy_event_service is None:
            return []
        return self.policy_event_service.list_investment_purposes()

    def create_policy_event(self, **kwargs) -> int:
        if self.policy_event_service is None:
            raise ValueError("Policy event service is unavailable.")
        return self.policy_event_service.create_policy_event(**kwargs)

    def update_policy_event(self, policy_event_id: int, **kwargs) -> None:
        if self.policy_event_service is None:
            raise ValueError("Policy event service is unavailable.")
        self.policy_event_service.update_policy_event(policy_event_id, **kwargs)

    def expire_policy_event(self, policy_event_id: int, *, expired_on: str | None = None) -> None:
        if self.policy_event_service is None:
            raise ValueError("Policy event service is unavailable.")
        self.policy_event_service.expire_policy_event(policy_event_id, expired_on=expired_on)

    def get_policy_event(self, policy_event_id: int) -> dict | None:
        if self.policy_event_service is None:
            return None
        return self.policy_event_service.get_policy_event(policy_event_id)

    def list_policy_events(
        self,
        *,
        policy_type: str | None = None,
        status: str | None = None,
        impact_level: str | None = None,
    ) -> list[dict]:
        if self.policy_event_service is None:
            return []
        return self.policy_event_service.list_policy_events(
            policy_type=policy_type,
            status=status,
            impact_level=impact_level,
        )


def _format_ratio(value: float) -> str:
    return f"{value * 100:.1f}%"


def _editable_loan_candidate_ids(rule_candidate_repository) -> dict[tuple, int]:
    if rule_candidate_repository is None:
        return {}

    ids: dict[tuple, int] = {}
    for candidate in rule_candidate_repository.list_applied_by_type("LOAN"):
        payload = json.loads(candidate["proposed_rule_json"])
        ids[_loan_rule_identity_key(payload)] = int(candidate["id"])
    return ids


def _select_display_loan_rules(rules, *, reference_date: date | None) -> list:
    target_date = reference_date or date.today()
    effective_rules = [rule for rule in rules if rule.is_effective_on(target_date)]
    effective_rules.sort(
        key=lambda item: (
            item.region_type,
            item.buyer_type,
            item.purpose,
            item.house_price_min,
            item.house_price_max or 10**30,
            date.fromisoformat(item.effective_from),
            date.fromisoformat(item.effective_to) if item.effective_to else date.max,
        ),
        reverse=True,
    )

    selected: list = []
    seen_band_keys: set[tuple] = set()
    for rule in effective_rules:
        band_key = (
            rule.region_type,
            rule.buyer_type,
            rule.purpose,
            rule.house_price_min,
            rule.house_price_max,
        )
        if band_key in seen_band_keys:
            continue
        seen_band_keys.add(band_key)
        selected.append(rule)

    return sorted(
        selected,
        key=lambda item: (
            item.effective_from,
            item.region_type,
            item.buyer_type,
            item.purpose,
            item.house_price_min,
        ),
    )


def _sort_all_loan_rules_for_display(rules) -> list:
    return sorted(
        rules,
        key=lambda item: (
            item.rule_version,
            item.purpose,
            item.region_type,
            item.buyer_type,
            item.house_price_min,
            item.house_price_max or 10**30,
            item.effective_from,
            item.effective_to or "9999-12-31",
        ),
    )


def _loan_rule_identity_key(rule_or_payload) -> tuple:
    return (
        str(rule_or_payload["region_type"] if isinstance(rule_or_payload, dict) else rule_or_payload.region_type),
        str(rule_or_payload["buyer_type"] if isinstance(rule_or_payload, dict) else rule_or_payload.buyer_type),
        str(rule_or_payload["purpose"] if isinstance(rule_or_payload, dict) else rule_or_payload.purpose),
        int(rule_or_payload["house_price_min"] if isinstance(rule_or_payload, dict) else rule_or_payload.house_price_min),
        (
            None
            if (rule_or_payload.get("house_price_max") if isinstance(rule_or_payload, dict) else rule_or_payload.house_price_max) is None
            else int(rule_or_payload["house_price_max"] if isinstance(rule_or_payload, dict) else rule_or_payload.house_price_max)
        ),
        str(rule_or_payload["effective_from"] if isinstance(rule_or_payload, dict) else rule_or_payload.effective_from),
        (
            None
            if (rule_or_payload.get("effective_to") if isinstance(rule_or_payload, dict) else rule_or_payload.effective_to) is None
            else str(rule_or_payload["effective_to"] if isinstance(rule_or_payload, dict) else rule_or_payload.effective_to)
        ),
    )


def _loan_rule_payload(rule_or_payload) -> dict:
    if isinstance(rule_or_payload, dict):
        return {
            "rule_version": str(rule_or_payload["rule_version"]),
            "effective_from": str(rule_or_payload["effective_from"]),
            "effective_to": (
                None if rule_or_payload.get("effective_to") is None else str(rule_or_payload["effective_to"])
            ),
            "region_type": str(rule_or_payload["region_type"]),
            "buyer_type": str(rule_or_payload["buyer_type"]),
            "purpose": str(rule_or_payload["purpose"]),
            "house_price_min": int(rule_or_payload["house_price_min"]),
            "house_price_max": (
                None if rule_or_payload.get("house_price_max") is None else int(rule_or_payload["house_price_max"])
            ),
            "ltv_rate": float(rule_or_payload["ltv_rate"]),
            "dsr_rate": float(rule_or_payload["dsr_rate"]),
            "max_loan_amount": (
                None if rule_or_payload.get("max_loan_amount") is None else int(rule_or_payload["max_loan_amount"])
            ),
            "description": str(rule_or_payload["description"]),
        }
    return {
        "rule_version": str(rule_or_payload.rule_version),
        "effective_from": str(rule_or_payload.effective_from),
        "effective_to": None if rule_or_payload.effective_to is None else str(rule_or_payload.effective_to),
        "region_type": str(rule_or_payload.region_type),
        "buyer_type": str(rule_or_payload.buyer_type),
        "purpose": str(rule_or_payload.purpose),
        "house_price_min": int(rule_or_payload.house_price_min),
        "house_price_max": None if rule_or_payload.house_price_max is None else int(rule_or_payload.house_price_max),
        "ltv_rate": float(rule_or_payload.ltv_rate),
        "dsr_rate": float(rule_or_payload.dsr_rate),
        "max_loan_amount": None if rule_or_payload.max_loan_amount is None else int(rule_or_payload.max_loan_amount),
        "description": str(rule_or_payload.description),
    }


def _rule_payload_is_current(rule_or_payload: dict, target_date: date) -> bool:
    effective_from = date.fromisoformat(str(rule_or_payload["effective_from"]))
    if target_date < effective_from:
        return False
    effective_to = rule_or_payload.get("effective_to")
    if effective_to is None:
        return True
    return target_date <= date.fromisoformat(str(effective_to))


def _loan_rule_state_label(rule_or_payload: dict, target_date: date) -> str:
    if _rule_payload_is_current(rule_or_payload, target_date):
        return "현재 적용"
    if target_date < date.fromisoformat(str(rule_or_payload["effective_from"])):
        return "예정"
    return "비활성/만료"


def _normalize_manual_loan_rule(
    *,
    rule_version: str,
    effective_from: str,
    effective_to: str | None,
    region_type: str,
    buyer_type: str,
    purpose: str,
    house_price_min: int,
    house_price_max: int | None,
    ltv_rate: float,
    dsr_rate: float,
    max_loan_amount: int | None,
    description: str,
) -> dict:
    normalized_rule_version = rule_version.strip() or _manual_rule_version()
    normalized = {
        "rule_version": normalized_rule_version,
        "effective_from": str(effective_from),
        "effective_to": effective_to or None,
        "region_type": str(region_type),
        "buyer_type": str(buyer_type),
        "purpose": str(purpose),
        "house_price_min": int(house_price_min),
        "house_price_max": None if house_price_max is None else int(house_price_max),
        "ltv_rate": float(ltv_rate),
        "dsr_rate": float(dsr_rate),
        "max_loan_amount": None if max_loan_amount is None else int(max_loan_amount),
        "description": description.strip() or "관리자 수동 대출 규칙",
    }
    _validate_manual_loan_rule(normalized)
    return normalized


def _validate_manual_loan_rule(rule: dict) -> None:
    date.fromisoformat(rule["effective_from"])
    if rule["effective_to"] is not None:
        date.fromisoformat(rule["effective_to"])
        if rule["effective_from"] > rule["effective_to"]:
            raise ValueError("적용 시작일은 종료일보다 늦을 수 없습니다.")
    if rule["region_type"] not in SUPPORTED_LOAN_REGION_TYPES:
        raise ValueError("지원하지 않는 지역 유형입니다.")
    if rule["buyer_type"] not in {"ALL", "NO_HOME", "ONE_HOME", "MULTI_HOME"}:
        raise ValueError("지원하지 않는 매수자 유형입니다.")
    if rule["purpose"] not in {"OWNER_OCCUPIED", "INVESTMENT"}:
        raise ValueError("지원하지 않는 목적입니다.")
    if rule["house_price_min"] < 0:
        raise ValueError("가격 하한은 0 이상이어야 합니다.")
    if rule["house_price_max"] is not None and rule["house_price_min"] > rule["house_price_max"]:
        raise ValueError("가격 하한은 가격 상한보다 작거나 같아야 합니다.")
    if not 0 <= rule["ltv_rate"] <= 1:
        raise ValueError("LTV는 0~1 범위여야 합니다.")
    if not 0 <= rule["dsr_rate"] <= 1:
        raise ValueError("DSR은 0~1 범위여야 합니다.")
    if rule["max_loan_amount"] is not None and rule["max_loan_amount"] < 0:
        raise ValueError("최대 대출액은 0 이상이어야 합니다.")


def _manual_rule_version() -> str:
    return f"manual-loan-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


def _format_money_or_unlimited(value: int | None) -> str:
    if value is None:
        return "제한 없음"
    return format_won(value)


def _format_price_range(min_value: int, max_value: int | None) -> str:
    if max_value is None:
        return f"{format_won(min_value)} 이상"
    return f"{format_won(min_value)} ~ {format_won(max_value)}"


def _format_sale_price_condition(max_value: int | None) -> str:
    if max_value is None:
        return "가격 상한 없음"
    return f"매매가 {format_won(max_value)} 이하"


def _tax_limit_value(max_value: int | None) -> str:
    if max_value is None:
        return "가격 상한 없음"
    return f"가격 상한 {format_won(max_value)}"


def _brokerage_limit_value(max_value: int | None, legal_fee_fixed: int) -> str:
    return f"{_tax_limit_value(max_value)}, 법무비 고정 {format_won(legal_fee_fixed)}"


def _loan_rule_name(purpose: str, region_type: str, buyer_type: str) -> str:
    return f"{_purpose_label(purpose)} / {_region_type_label(region_type)} / {_buyer_type_label(buyer_type)}"


def _loan_rule_display_name(rule) -> str:
    return (
        f"{_loan_rule_name(rule.purpose, rule.region_type, rule.buyer_type)}"
        f" / {_compact_price_range(rule.house_price_min, rule.house_price_max)}"
    )


def _loan_conditions(purpose: str, region_type: str, buyer_type: str) -> str:
    return f"{_purpose_label(purpose)}, {_region_type_label(region_type)}, {_buyer_type_label(buyer_type)} 기준"


def _compact_price_range(min_value: int, max_value: int | None) -> str:
    if max_value is None:
        return f"{_format_eok_amount(min_value)} 이상"
    upper_exclusive = max_value + 1
    if min_value == 0:
        return f"{_format_eok_amount(upper_exclusive)} 미만"
    return f"{_format_eok_amount(min_value)}~{_format_eok_amount(upper_exclusive)} 미만"


def _format_eok_amount(value: int) -> str:
    eok_value = value / 100_000_000
    if float(eok_value).is_integer():
        return f"{int(eok_value)}억"
    return f"{eok_value:.1f}".rstrip("0").rstrip(".") + "억"


def _purpose_label(value: str) -> str:
    return {
        "OWNER_OCCUPIED": "실거주",
        "INVESTMENT": "투자",
    }.get(value, value)


def _region_type_label(value: str) -> str:
    return {
        "NON_REGULATED": "비규제지역",
        "REGULATED": "공통 규제 규칙",
        "LAND_TRANSACTION_PERMISSION": "토지거래허가구역",
        "LAND_TRANSACTION_PERMISSION_AREA": "토지거래허가구역",
        "SPECULATION_OVERHEATED": "투기과열지구",
        "SPECULATION_OVERHEATED_DISTRICT": "투기과열지구",
        "ADJUSTMENT_TARGET": "조정대상지역",
        "ADJUSTMENT_TARGET_AREA": "조정대상지역",
    }.get(value, value)


def _buyer_type_label(value: str) -> str:
    return {
        "ALL": "전체",
        "NO_HOME": "무주택",
        "ONE_HOME": "1주택",
        "MULTI_HOME": "다주택",
    }.get(value, value)


def _region_level_label(value: str) -> str:
    return {
        "SIDO": "시도",
        "SIGUNGU": "시군구",
        "DONG": "동",
    }.get(value, value)


def _policy_type_label(value: str) -> str:
    return {
        "REGULATED_AREA": "규제지역(기존 상위개념)",
        "NON_REGULATED_AREA": "비규제지역",
        "LAND_TRANSACTION_PERMISSION": "토지거래허가구역",
        "SPECULATION_OVERHEATED_DISTRICT": "투기과열지구",
        "ADJUSTMENT_TARGET_AREA": "조정대상지역",
    }.get(value, value)
