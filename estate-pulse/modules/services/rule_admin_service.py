from __future__ import annotations

import json
from datetime import date, datetime

from modules.utils.money_utils import format_won

LOAN_REGION_TYPE_OPTIONS = (
    "NON_REGULATED",
    "REGULATED",
    "LAND_TRANSACTION_PERMISSION",
    "SPECULATION_OVERHEATED_DISTRICT",
    "ADJUSTMENT_TARGET_AREA",
)


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

    def list_loan_rules(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for rule in self.rule_runtime_service.get_active_loan_rules():
            rows.append(
                {
                    "rule_version": rule.rule_version,
                    "rule_name": _loan_rule_name(rule.purpose, rule.region_type, rule.buyer_type),
                    "effective_from": rule.effective_from,
                    "effective_to": rule.effective_to or "-",
                    "investment_purpose": _purpose_label(rule.purpose),
                    "region_type": _region_type_label(rule.region_type),
                    "buyer_type": _buyer_type_label(rule.buyer_type),
                    "house_price_range": _format_price_range(rule.house_price_min, rule.house_price_max),
                    "ltv_rate": _format_ratio(rule.ltv_rate),
                    "dsr_rate": _format_ratio(rule.dsr_rate),
                    "max_loan_amount": _format_money_or_unlimited(rule.max_loan_amount),
                    "conditions": _loan_conditions(rule.purpose, rule.region_type, rule.buyer_type),
                    "description": rule.description,
                }
            )
        return rows

    def list_loan_region_types(self) -> list[str]:
        return list(LOAN_REGION_TYPE_OPTIONS)

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
    if rule["region_type"] not in LOAN_REGION_TYPE_OPTIONS:
        raise ValueError("지원하지 않는 지역 유형입니다.")
    if rule["buyer_type"] not in {"NO_HOME", "ONE_HOME", "MULTI_HOME"}:
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


def _loan_conditions(purpose: str, region_type: str, buyer_type: str) -> str:
    return f"{_purpose_label(purpose)}, {_region_type_label(region_type)}, {_buyer_type_label(buyer_type)} 기준"


def _purpose_label(value: str) -> str:
    return {
        "OWNER_OCCUPIED": "실거주",
        "INVESTMENT": "투자",
    }.get(value, value)


def _region_type_label(value: str) -> str:
    return {
        "NON_REGULATED": "비규제지역",
        "REGULATED": "규제지역",
        "LAND_TRANSACTION_PERMISSION": "토지거래허가구역",
        "LAND_TRANSACTION_PERMISSION_AREA": "토지거래허가구역",
        "SPECULATION_OVERHEATED": "투기과열지구",
        "SPECULATION_OVERHEATED_DISTRICT": "투기과열지구",
        "ADJUSTMENT_TARGET": "조정대상지역",
        "ADJUSTMENT_TARGET_AREA": "조정대상지역",
    }.get(value, value)


def _buyer_type_label(value: str) -> str:
    return {
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
