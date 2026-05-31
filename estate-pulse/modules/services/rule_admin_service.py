from __future__ import annotations

from modules.utils.money_utils import format_won


class RuleAdminService:
    def __init__(
        self,
        *,
        rule_runtime_service,
        region_policy_service=None,
        policy_event_service=None,
    ) -> None:
        self.rule_runtime_service = rule_runtime_service
        self.region_policy_service = region_policy_service
        self.policy_event_service = policy_event_service

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
