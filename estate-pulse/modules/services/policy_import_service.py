from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import json

from modules.analyzers.loan_analyzer import calculate_loan_terms
from modules.services.policy_parsers import (
    CANDIDATE_TARGET_RULE_TYPES,
    IMPORT_TARGET_RULE_TYPES,
    ParsedPolicySection,
    PolicyParser,
    get_default_policy_parsers,
)
from modules.services.rule_runtime_service import RuleRuntimeService


PARSER_STATUS_COMPLETED = "COMPLETED"
PARSER_STATUS_FAILED = "FAILED"

CANDIDATE_STATUS_PENDING_REVIEW = "PENDING_REVIEW"
CANDIDATE_STATUS_APPROVED = "APPROVED"
CANDIDATE_STATUS_REJECTED = "REJECTED"
CANDIDATE_STATUS_APPLIED = "APPLIED"


@dataclass
class ValidationResult:
    normalized_rule: dict
    warnings: list[str]
    errors: list[str]


class PolicyImportService:
    def __init__(
        self,
        *,
        policy_import_repository,
        rule_candidate_repository,
        rule_runtime_service: RuleRuntimeService,
        region_policy_service=None,
        parsers: dict[str, PolicyParser] | None = None,
    ) -> None:
        self.policy_import_repository = policy_import_repository
        self.rule_candidate_repository = rule_candidate_repository
        self.rule_runtime_service = rule_runtime_service
        self.region_policy_service = region_policy_service
        self.parsers = parsers or get_default_policy_parsers()

    def list_parser_names(self) -> list[str]:
        return list(self.parsers.keys())

    def list_import_target_rule_types(self) -> list[str]:
        return list(IMPORT_TARGET_RULE_TYPES)

    def list_policy_imports(self) -> list[dict]:
        return self.policy_import_repository.list_recent()

    def preview_policy_sections(
        self,
        *,
        source_text: str,
        target_rule_type: str,
        parser_name: str,
    ) -> list[dict]:
        if target_rule_type not in IMPORT_TARGET_RULE_TYPES:
            raise ValueError(f"Unsupported target rule type: {target_rule_type}")
        if parser_name not in self.parsers:
            raise ValueError(f"Unknown parser: {parser_name}")
        if not source_text.strip():
            raise ValueError("Policy text is required.")

        sections = self.parsers[parser_name].analyze_policy_text(
            source_text=source_text,
            target_rule_type=target_rule_type,
        )
        return [self._serialize_section(section) for section in sections]

    def create_policy_import(
        self,
        *,
        source_text: str,
        source_name: str | None,
        target_rule_type: str,
        effective_date: str | None,
        parser_name: str,
    ) -> dict:
        sections = self.preview_policy_sections(
            source_text=source_text,
            target_rule_type=target_rule_type,
            parser_name=parser_name,
        )
        return self.create_policy_import_from_sections(
            source_text=source_text,
            source_name=source_name,
            target_rule_type=target_rule_type,
            effective_date=effective_date,
            parser_name=parser_name,
            selected_sections=sections,
        )

    def create_policy_import_from_sections(
        self,
        *,
        source_text: str,
        source_name: str | None,
        target_rule_type: str,
        effective_date: str | None,
        parser_name: str,
        selected_sections: list[dict],
    ) -> dict:
        if target_rule_type not in IMPORT_TARGET_RULE_TYPES:
            raise ValueError(f"Unsupported target rule type: {target_rule_type}")
        if parser_name not in self.parsers:
            raise ValueError(f"Unknown parser: {parser_name}")
        if not source_text.strip():
            raise ValueError("Policy text is required.")
        if not selected_sections:
            raise ValueError("Select at least one section before generating candidates.")

        parsed_sections = [self._deserialize_section(item) for item in selected_sections]
        self._validate_selected_sections_for_import(parsed_sections)
        policy_import_id = self.policy_import_repository.create(
            source_text=source_text,
            source_name=source_name,
            target_rule_type=target_rule_type,
            effective_date=effective_date,
            parser_name=parser_name,
            parser_status=PARSER_STATUS_COMPLETED,
        )

        try:
            parser = self.parsers[parser_name]
            parsed_candidates = parser.parse_policy_text(
                source_text=source_text,
                target_rule_type=target_rule_type,
                effective_date=effective_date,
                active_rules_by_type=self._active_rules_by_type(),
                selected_sections=parsed_sections,
            )
        except Exception:
            self.policy_import_repository.update_status(policy_import_id, PARSER_STATUS_FAILED)
            raise

        candidate_ids: list[int] = []
        for parsed_candidate in parsed_candidates:
            candidate_target_rule_type = str(parsed_candidate.target_rule_type)
            if candidate_target_rule_type not in CANDIDATE_TARGET_RULE_TYPES:
                raise ValueError(
                    f"Unsupported candidate target rule type: {candidate_target_rule_type}"
                )
            validation_result = self.validate_rule_candidate(
                target_rule_type=candidate_target_rule_type,
                proposed_rule=parsed_candidate.proposed_rule,
                previous_rule=parsed_candidate.previous_rule,
            )
            changed_fields = _changed_fields(
                parsed_candidate.previous_rule,
                validation_result.normalized_rule,
                candidate_target_rule_type,
            )
            if _skip_noop_candidate(candidate_target_rule_type, changed_fields):
                continue
            warnings = parsed_candidate.warnings + validation_result.warnings + [
                f"ERROR: {error}" for error in validation_result.errors
            ]
            candidate_ids.append(
                self.rule_candidate_repository.create(
                    policy_import_id=policy_import_id,
                    target_rule_type=candidate_target_rule_type,
                    rule_name=_rule_name_for_candidate(
                        candidate_target_rule_type,
                        validation_result.normalized_rule,
                        changed_fields,
                    ),
                    rule_version=_rule_version_for_type(
                        candidate_target_rule_type,
                        validation_result.normalized_rule,
                    ),
                    previous_rule_json=_json_or_none(parsed_candidate.previous_rule),
                    proposed_rule_json=json.dumps(
                        validation_result.normalized_rule,
                        ensure_ascii=False,
                        indent=2,
                        sort_keys=True,
                    ),
                    changed_fields_json=json.dumps(
                        changed_fields,
                        ensure_ascii=False,
                    ),
                    confidence=parsed_candidate.confidence,
                    warnings=json.dumps(warnings, ensure_ascii=False),
                    status=CANDIDATE_STATUS_PENDING_REVIEW,
                )
            )

        return {
            "policy_import_id": policy_import_id,
            "candidate_ids": candidate_ids,
            "parser_status": PARSER_STATUS_COMPLETED,
        }

    def get_policy_import_detail(self, policy_import_id: int) -> dict:
        policy_import = self.policy_import_repository.get(policy_import_id)
        if not policy_import:
            raise ValueError("Policy import not found.")
        candidates = [
            self._decorate_candidate(candidate)
            for candidate in self.rule_candidate_repository.list_by_policy_import(policy_import_id)
        ]
        return {
            "policy_import": policy_import,
            "candidates": candidates,
        }

    def update_candidate_proposed_rule(
        self,
        *,
        candidate_id: int,
        proposed_rule_json_text: str,
    ) -> dict:
        candidate = self.rule_candidate_repository.get(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found.")

        try:
            proposed_rule = json.loads(proposed_rule_json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc

        previous_rule = _load_json_or_none(candidate.get("previous_rule_json"))
        validation_result = self.validate_rule_candidate(
            target_rule_type=str(candidate["target_rule_type"]),
            proposed_rule=proposed_rule,
            previous_rule=previous_rule,
        )
        changed_fields = _changed_fields(
            previous_rule,
            validation_result.normalized_rule,
            str(candidate["target_rule_type"]),
        )
        warnings = validation_result.warnings + [
            f"ERROR: {error}" for error in validation_result.errors
        ]
        if _skip_noop_candidate(str(candidate["target_rule_type"]), changed_fields):
            warnings.append("ERROR: No actionable policy changes were detected.")
        normalized_json = json.dumps(
            validation_result.normalized_rule,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        self.rule_candidate_repository.update_candidate_payload(
            candidate_id=candidate_id,
            proposed_rule_json=normalized_json,
            changed_fields_json=json.dumps(changed_fields, ensure_ascii=False),
            warnings=json.dumps(warnings, ensure_ascii=False),
            confidence=candidate.get("confidence"),
            rule_name=_rule_name_for_candidate(
                str(candidate["target_rule_type"]),
                validation_result.normalized_rule,
                changed_fields,
            ),
            rule_version=_rule_version_for_type(
                str(candidate["target_rule_type"]),
                validation_result.normalized_rule,
            ),
        )
        return self._decorate_candidate(self.rule_candidate_repository.get(candidate_id) or candidate)

    def set_candidate_status(self, *, candidate_id: int, status: str) -> None:
        if status not in {
            CANDIDATE_STATUS_PENDING_REVIEW,
            CANDIDATE_STATUS_APPROVED,
            CANDIDATE_STATUS_REJECTED,
        }:
            raise ValueError(f"Unsupported candidate status: {status}")

        candidate = self.rule_candidate_repository.get(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found.")

        if status == CANDIDATE_STATUS_APPROVED:
            self._raise_if_candidate_invalid(candidate)
        timestamp_field = (
            "reviewed_at"
            if status in {CANDIDATE_STATUS_APPROVED, CANDIDATE_STATUS_REJECTED}
            else None
        )
        self.rule_candidate_repository.update_status(
            candidate_id=candidate_id,
            status=status,
            timestamp_field=timestamp_field,
        )

    def apply_candidates(self, *, candidate_ids: list[int]) -> list[int]:
        if not candidate_ids:
            raise ValueError("Select at least one candidate to apply.")

        working_active_loan_rules = self.rule_runtime_service.serialize_active_loan_rules()
        applied_ids: list[int] = []
        for candidate_id in candidate_ids:
            candidate = self.rule_candidate_repository.get(candidate_id)
            if not candidate:
                raise ValueError(f"Candidate not found: {candidate_id}")
            if candidate["status"] != CANDIDATE_STATUS_APPROVED:
                raise ValueError("Only approved candidates can be applied.")
            self._raise_if_candidate_invalid(candidate)

            target_rule_type = str(candidate["target_rule_type"])
            if target_rule_type == "UNKNOWN":
                raise ValueError("UNKNOWN candidates are review-only and cannot be applied.")

            if target_rule_type == "LOAN":
                proposed_rule = json.loads(candidate["proposed_rule_json"])
                validation_result = self.validate_rule_candidate(
                    target_rule_type=target_rule_type,
                    proposed_rule=proposed_rule,
                    previous_rule=_load_json_or_none(candidate.get("previous_rule_json")),
                    active_loan_rules_override=working_active_loan_rules,
                )
                if validation_result.errors:
                    raise ValueError("; ".join(validation_result.errors))
                working_active_loan_rules = _overlay_loan_rule(
                    working_active_loan_rules,
                    validation_result.normalized_rule,
                    _load_json_or_none(candidate.get("previous_rule_json")),
                )
            elif target_rule_type == "REGION_POLICY":
                if self.region_policy_service is None:
                    raise ValueError("Region policy service is unavailable.")
                proposed_rule = json.loads(candidate["proposed_rule_json"])
                validation_result = self.validate_rule_candidate(
                    target_rule_type=target_rule_type,
                    proposed_rule=proposed_rule,
                    previous_rule=_load_json_or_none(candidate.get("previous_rule_json")),
                )
                if validation_result.errors:
                    raise ValueError("; ".join(validation_result.errors))
                self.region_policy_service.create_region_policy_status(
                    region_level=str(validation_result.normalized_rule["region_level"]),
                    sido=str(validation_result.normalized_rule["sido"]),
                    sigungu=validation_result.normalized_rule.get("sigungu"),
                    dong=validation_result.normalized_rule.get("dong"),
                    policy_type=str(validation_result.normalized_rule["policy_type"]),
                    effective_from=str(validation_result.normalized_rule["effective_from"]),
                    effective_to=validation_result.normalized_rule.get("effective_to"),
                    notes=validation_result.normalized_rule.get("notes"),
                    source_policy_import_id=int(candidate["policy_import_id"]),
                )

            self.rule_candidate_repository.update_status(
                candidate_id=candidate_id,
                status=CANDIDATE_STATUS_APPLIED,
                timestamp_field="applied_at",
            )
            applied_ids.append(candidate_id)
        return applied_ids

    def preview_loan_candidate(
        self,
        *,
        candidate_id: int,
        sale_price: int,
        region_type: str,
        buyer_type: str,
        investment_purpose: str,
        annual_income: int | None = None,
        existing_debt: int = 0,
        annual_interest_rate: float | None = None,
    ) -> dict:
        candidate = self.rule_candidate_repository.get(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found.")
        if candidate["target_rule_type"] != "LOAN":
            raise ValueError("Loan preview is only available for loan candidates.")

        old_rules = self.rule_runtime_service.get_active_loan_rules()
        proposed_rule = json.loads(candidate["proposed_rule_json"])
        preview_reference_date = date.fromisoformat(str(proposed_rule["effective_from"]))
        preview_rules = [_to_loan_rule_dict(rule) for rule in old_rules]
        preview_rules = _overlay_loan_rule(
            preview_rules,
            proposed_rule,
            _load_json_or_none(candidate.get("previous_rule_json")),
        )

        old_result = calculate_loan_terms(
            sale_price=sale_price,
            region_type=region_type,
            buyer_type=buyer_type,
            purpose=investment_purpose,
            reference_date=preview_reference_date,
            annual_income=annual_income,
            existing_debt=existing_debt,
            annual_interest_rate=annual_interest_rate,
            rules=old_rules,
        )
        proposed_result = calculate_loan_terms(
            sale_price=sale_price,
            region_type=region_type,
            buyer_type=buyer_type,
            purpose=investment_purpose,
            reference_date=preview_reference_date,
            annual_income=annual_income,
            existing_debt=existing_debt,
            annual_interest_rate=annual_interest_rate,
            rules=[_to_loan_rule(item) for item in preview_rules],
        )

        return {
            "old_result": old_result,
            "proposed_result": proposed_result,
            "difference_in_estimated_loan_amount": proposed_result["final_loan_amount"]
            - old_result["final_loan_amount"],
        }

    def validate_rule_candidate(
        self,
        *,
        target_rule_type: str,
        proposed_rule: dict,
        previous_rule: dict | None,
        active_loan_rules_override: list[dict] | None = None,
    ) -> ValidationResult:
        if target_rule_type not in CANDIDATE_TARGET_RULE_TYPES:
            raise ValueError(f"Unsupported target rule type: {target_rule_type}")
        if target_rule_type == "LOAN":
            return self._validate_loan_rule(
                proposed_rule=proposed_rule,
                previous_rule=previous_rule,
                active_loan_rules_override=active_loan_rules_override,
            )
        if target_rule_type == "TAX":
            return self._validate_tax_rule(proposed_rule=proposed_rule)
        if target_rule_type == "BROKERAGE":
            return self._validate_brokerage_rule(proposed_rule=proposed_rule)
        if target_rule_type == "REGION_POLICY":
            return self._validate_region_policy_rule(proposed_rule=proposed_rule)
        return self._validate_unknown_rule(proposed_rule=proposed_rule)

    def _validate_loan_rule(
        self,
        *,
        proposed_rule: dict,
        previous_rule: dict | None,
        active_loan_rules_override: list[dict] | None,
    ) -> ValidationResult:
        warnings: list[str] = []
        errors: list[str] = []
        normalized_rule: dict = {}

        required_fields = (
            "rule_version",
            "effective_from",
            "region_type",
            "buyer_type",
            "purpose",
            "house_price_min",
            "ltv_rate",
            "dsr_rate",
            "description",
        )
        for field in required_fields:
            if field not in proposed_rule or proposed_rule[field] in (None, ""):
                errors.append(f"Missing required field: {field}")

        try:
            normalized_rule = {
                "rule_version": str(proposed_rule["rule_version"]),
                "effective_from": str(proposed_rule["effective_from"]),
                "effective_to": proposed_rule.get("effective_to"),
                "region_type": str(proposed_rule["region_type"]),
                "buyer_type": str(proposed_rule["buyer_type"]),
                "purpose": str(proposed_rule["purpose"]),
                "house_price_min": int(proposed_rule["house_price_min"]),
                "house_price_max": None
                if proposed_rule.get("house_price_max") in (None, "")
                else int(proposed_rule["house_price_max"]),
                "ltv_rate": float(proposed_rule["ltv_rate"]),
                "dsr_rate": float(proposed_rule["dsr_rate"]),
                "max_loan_amount": None
                if proposed_rule.get("max_loan_amount") in (None, "")
                else int(proposed_rule["max_loan_amount"]),
                "description": str(proposed_rule["description"]),
            }
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"Invalid numeric or typed field: {exc}")
            return ValidationResult(normalized_rule=proposed_rule, warnings=warnings, errors=errors)

        self._validate_effective_dates(normalized_rule, errors)
        if (
            normalized_rule["house_price_max"] is not None
            and normalized_rule["house_price_min"] > normalized_rule["house_price_max"]
        ):
            errors.append("house_price_min must be less than or equal to house_price_max.")
        if normalized_rule["ltv_rate"] < 0 or normalized_rule["dsr_rate"] < 0:
            errors.append("LTV and DSR rates must be zero or positive.")
        if (
            normalized_rule["max_loan_amount"] is not None
            and normalized_rule["max_loan_amount"] < 0
        ):
            errors.append("max_loan_amount must be zero or positive.")

        active_rules = (
            active_loan_rules_override
            or self.rule_runtime_service.serialize_active_loan_rules()
        )
        filtered_active_rules = []
        for item in active_rules:
            if previous_rule and _same_loan_rule_identity_dict(item, previous_rule):
                continue
            filtered_active_rules.append(item)
        if _has_overlapping_loan_rule(filtered_active_rules, normalized_rule):
            errors.append("An overlapping active loan rule already exists for the same condition.")

        if normalized_rule["max_loan_amount"] is None:
            warnings.append("max_loan_amount is empty and will be treated as unlimited.")
        if normalized_rule["house_price_max"] is None:
            warnings.append("house_price_max is empty and will be treated as no upper bound.")
        if not normalized_rule["description"].strip():
            warnings.append("Description is empty.")

        return ValidationResult(normalized_rule=normalized_rule, warnings=warnings, errors=errors)

    def _validate_tax_rule(self, *, proposed_rule: dict) -> ValidationResult:
        warnings: list[str] = []
        errors: list[str] = []
        try:
            normalized_rule = {
                "version": str(proposed_rule["version"]),
                "rule_name": str(proposed_rule["rule_name"]),
                "effective_from": str(proposed_rule["effective_from"]),
                "effective_to": proposed_rule.get("effective_to"),
                "description": str(proposed_rule["description"]),
                "local_education_tax_rate": float(proposed_rule["local_education_tax_rate"]),
                "brackets": [
                    {
                        "max_sale_price": None
                        if item.get("max_sale_price") in (None, "")
                        else int(item["max_sale_price"]),
                        "acquisition_tax_rate": float(item["acquisition_tax_rate"]),
                    }
                    for item in proposed_rule.get("brackets", [])
                ],
            }
        except (KeyError, TypeError, ValueError) as exc:
            return ValidationResult(
                normalized_rule=proposed_rule,
                warnings=warnings,
                errors=[f"Invalid tax rule: {exc}"],
            )

        if not normalized_rule["brackets"]:
            errors.append("At least one tax bracket is required.")
        if normalized_rule["local_education_tax_rate"] < 0:
            errors.append("local_education_tax_rate must be zero or positive.")
        self._validate_effective_dates(normalized_rule, errors)
        self._validate_brackets(
            normalized_rule["brackets"],
            "max_sale_price",
            "acquisition_tax_rate",
            errors,
        )
        return ValidationResult(normalized_rule=normalized_rule, warnings=warnings, errors=errors)

    def _validate_brokerage_rule(self, *, proposed_rule: dict) -> ValidationResult:
        warnings: list[str] = []
        errors: list[str] = []
        try:
            normalized_rule = {
                "version": str(proposed_rule["version"]),
                "rule_name": str(proposed_rule["rule_name"]),
                "effective_from": str(proposed_rule["effective_from"]),
                "effective_to": proposed_rule.get("effective_to"),
                "description": str(proposed_rule["description"]),
                "legal_fee_fixed": int(proposed_rule["legal_fee_fixed"]),
                "reserve_cost_rate": float(proposed_rule["reserve_cost_rate"]),
                "brackets": [
                    {
                        "max_sale_price": None
                        if item.get("max_sale_price") in (None, "")
                        else int(item["max_sale_price"]),
                        "fee_rate": float(item["fee_rate"]),
                    }
                    for item in proposed_rule.get("brackets", [])
                ],
            }
        except (KeyError, TypeError, ValueError) as exc:
            return ValidationResult(
                normalized_rule=proposed_rule,
                warnings=warnings,
                errors=[f"Invalid brokerage rule: {exc}"],
            )

        if not normalized_rule["brackets"]:
            errors.append("At least one brokerage bracket is required.")
        if (
            normalized_rule["legal_fee_fixed"] < 0
            or normalized_rule["reserve_cost_rate"] < 0
        ):
            errors.append("Legal fee and reserve rate must be zero or positive.")
        self._validate_effective_dates(normalized_rule, errors)
        self._validate_brackets(
            normalized_rule["brackets"],
            "max_sale_price",
            "fee_rate",
            errors,
        )
        return ValidationResult(normalized_rule=normalized_rule, warnings=warnings, errors=errors)

    def _validate_region_policy_rule(self, *, proposed_rule: dict) -> ValidationResult:
        warnings: list[str] = []
        errors: list[str] = []
        try:
            normalized_rule = {
                "region_level": str(proposed_rule["region_level"]).upper(),
                "sido": str(proposed_rule["sido"]).strip(),
                "sigungu": None
                if proposed_rule.get("sigungu") in (None, "")
                else str(proposed_rule["sigungu"]).strip(),
                "dong": None
                if proposed_rule.get("dong") in (None, "")
                else str(proposed_rule["dong"]).strip(),
                "policy_type": str(proposed_rule["policy_type"]).upper(),
                "effective_from": str(proposed_rule["effective_from"]),
                "effective_to": proposed_rule.get("effective_to"),
                "notes": str(proposed_rule.get("notes") or ""),
            }
        except (KeyError, TypeError, ValueError) as exc:
            return ValidationResult(
                normalized_rule=proposed_rule,
                warnings=warnings,
                errors=[f"Invalid region policy rule: {exc}"],
            )

        if normalized_rule["region_level"] not in {"SIDO", "SIGUNGU", "DONG"}:
            errors.append("region_level must be one of SIDO, SIGUNGU, or DONG.")
        if normalized_rule["policy_type"] not in {
            "REGULATED_AREA",
            "NON_REGULATED_AREA",
            "LAND_TRANSACTION_PERMISSION",
        }:
            errors.append(
                "policy_type must be REGULATED_AREA, NON_REGULATED_AREA, or LAND_TRANSACTION_PERMISSION."
            )
        if not normalized_rule["sido"]:
            errors.append("sido is required.")
        if normalized_rule["region_level"] in {"SIGUNGU", "DONG"} and not normalized_rule["sigungu"]:
            errors.append("sigungu is required for SIGUNGU and DONG.")
        if normalized_rule["region_level"] == "DONG" and not normalized_rule["dong"]:
            errors.append("dong is required for DONG.")
        if normalized_rule["region_level"] == "SIDO":
            normalized_rule["sigungu"] = None
            normalized_rule["dong"] = None
        elif normalized_rule["region_level"] == "SIGUNGU":
            normalized_rule["dong"] = None

        self._validate_effective_dates(normalized_rule, errors)

        if self.region_policy_service is not None and not errors:
            active_region_policies = self.region_policy_service.list_region_policy_statuses()
            if _has_overlapping_region_policy(active_region_policies, normalized_rule):
                errors.append("An overlapping active region policy already exists for the same scope.")

        if not normalized_rule["notes"].strip():
            warnings.append("notes is empty.")
        if normalized_rule["policy_type"] == "LAND_TRANSACTION_PERMISSION":
            warnings.append("LAND_TRANSACTION_PERMISSION affects region status review, not loan region type directly.")

        return ValidationResult(normalized_rule=normalized_rule, warnings=warnings, errors=errors)

    def _validate_unknown_rule(self, *, proposed_rule: dict) -> ValidationResult:
        warnings = [
            "UNKNOWN candidates are items that could not be classified automatically.",
            "UNKNOWN candidates are review-only and cannot be applied.",
        ]
        normalized_rule = {
            "raw_excerpt": str(proposed_rule.get("raw_excerpt") or ""),
            "notes": str(proposed_rule.get("notes") or ""),
        }
        if not normalized_rule["raw_excerpt"]:
            warnings.append("raw_excerpt is empty.")
        if not normalized_rule["notes"]:
            warnings.append("notes is empty.")
        return ValidationResult(normalized_rule=normalized_rule, warnings=warnings, errors=[])

    def _validate_effective_dates(self, proposed_rule: dict, errors: list[str]) -> None:
        try:
            effective_from = date.fromisoformat(str(proposed_rule["effective_from"]))
            effective_to_value = proposed_rule.get("effective_to")
            if effective_to_value is not None and date.fromisoformat(
                str(effective_to_value)
            ) < effective_from:
                errors.append("effective_from must be earlier than or equal to effective_to.")
        except ValueError as exc:
            errors.append(f"Invalid date field: {exc}")

    def _validate_brackets(
        self,
        brackets: list[dict],
        upper_bound_field: str,
        rate_field: str,
        errors: list[str],
    ) -> None:
        previous_max: int | None = None
        for bracket in brackets:
            max_value = bracket.get(upper_bound_field)
            if max_value is not None:
                if previous_max is not None and int(max_value) <= previous_max:
                    errors.append("Bracket upper bounds must be strictly increasing.")
                previous_max = int(max_value)
            if float(bracket[rate_field]) < 0:
                errors.append(f"{rate_field} must be zero or positive.")

    def _raise_if_candidate_invalid(self, candidate: dict) -> None:
        warnings = _load_json_list(candidate.get("warnings"))
        errors = [item for item in warnings if item.startswith("ERROR:")]
        if errors:
            raise ValueError("; ".join(errors))

    def _active_rules_by_type(self) -> dict[str, list[dict]]:
        return {
            "LOAN": self.rule_runtime_service.serialize_active_loan_rules(),
            "TAX": self.rule_runtime_service.serialize_active_tax_rules(),
            "BROKERAGE": self.rule_runtime_service.serialize_active_brokerage_rules(),
            "REGION_POLICY": (
                self.region_policy_service.list_region_policy_statuses()
                if self.region_policy_service is not None
                else []
            ),
            "UNKNOWN": [],
        }

    def _serialize_section(self, section: ParsedPolicySection) -> dict:
        return {
            "section_id": section.section_id,
            "source_text": section.source_text,
            "target_rule_type": section.target_rule_type,
            "confidence": section.confidence,
            "warnings": list(section.warnings),
            "metadata": dict(section.metadata or {}),
        }

    def _deserialize_section(self, payload: dict) -> ParsedPolicySection:
        return ParsedPolicySection(
            section_id=str(payload["section_id"]),
            source_text=str(payload["source_text"]),
            target_rule_type=str(payload["target_rule_type"]),
            confidence=None
            if payload.get("confidence") is None
            else float(payload["confidence"]),
            warnings=[str(item) for item in payload.get("warnings", [])],
            metadata=dict(payload.get("metadata") or {}),
        )

    def _decorate_candidate(self, candidate: dict) -> dict:
        decorated = dict(candidate)
        decorated["warnings_list"] = _load_json_list(candidate.get("warnings"))
        decorated["changed_fields_list"] = _load_json_list(
            candidate.get("changed_fields_json")
        )
        decorated["previous_rule"] = _load_json_or_none(candidate.get("previous_rule_json"))
        decorated["proposed_rule"] = _load_json_or_none(candidate.get("proposed_rule_json"))
        decorated["changed_field_details"] = _build_changed_field_details(
            str(candidate["target_rule_type"]),
            decorated["previous_rule"],
            decorated["proposed_rule"],
            decorated["changed_fields_list"],
        )
        decorated["change_summary"] = _build_change_summary(
            decorated["changed_field_details"]
        )
        return decorated

    def _validate_selected_sections_for_import(
        self,
        sections: list[ParsedPolicySection],
    ) -> None:
        unresolved_labels: list[str] = []
        for section in sections:
            if section.target_rule_type != "REGION_POLICY":
                continue
            metadata = dict(section.metadata or {})
            expanded_regions = metadata.get("expanded_regions") or []
            if metadata.get("requires_region_expansion") and not expanded_regions:
                unresolved_labels.append(str(section.section_id))
                metadata["review_state"] = "REVIEW_REQUIRED"
                section.metadata = metadata
        if unresolved_labels:
            labels = ", ".join(unresolved_labels)
            raise ValueError(
                "Region group expansion is unresolved for sections: "
                f"{labels}. Enter or confirm explicit regions before generating candidates."
            )


def _rule_name_for_candidate(
    target_rule_type: str,
    proposed_rule: dict,
    changed_fields: list[str] | None = None,
) -> str:
    changed_fields = changed_fields or []
    if target_rule_type == "LOAN":
        if changed_fields:
            return "대출 정책 변경"
        return (
            f"{proposed_rule.get('purpose')} / "
            f"{proposed_rule.get('region_type')} / "
            f"{proposed_rule.get('buyer_type')}"
        )
    if target_rule_type == "REGION_POLICY":
        return " / ".join(
            item
            for item in [
                str(proposed_rule.get("policy_type") or ""),
                str(proposed_rule.get("sido") or ""),
                str(proposed_rule.get("sigungu") or ""),
                str(proposed_rule.get("dong") or ""),
            ]
            if item
        )
    if target_rule_type == "TAX" and changed_fields:
        return "세금 정책 변경"
    if target_rule_type == "BROKERAGE" and changed_fields:
        return "중개보수 정책 변경"
    if target_rule_type == "UNKNOWN":
        return str(proposed_rule.get("notes") or "UNKNOWN candidate")
    return str(proposed_rule.get("rule_name") or proposed_rule.get("version") or "candidate")


def _rule_version_for_type(target_rule_type: str, proposed_rule: dict) -> str | None:
    if target_rule_type == "LOAN":
        return str(proposed_rule.get("rule_version") or "")
    if target_rule_type == "REGION_POLICY":
        return None
    if target_rule_type == "UNKNOWN":
        return None
    return str(proposed_rule.get("version") or "")


def _json_or_none(value: dict | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _load_json_or_none(value: str | None) -> dict | None:
    if not value:
        return None
    return json.loads(value)


def _load_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    data = json.loads(value)
    return [str(item) for item in data]


def _changed_fields(
    previous_rule: dict | None,
    proposed_rule: dict,
    target_rule_type: str,
) -> list[str]:
    previous_rule = previous_rule or {}
    field_paths = _meaningful_field_paths(target_rule_type, proposed_rule, previous_rule)
    changed: list[str] = []
    for field_path in field_paths:
        if _field_value(previous_rule, field_path) != _field_value(proposed_rule, field_path):
            changed.append(field_path)
    return changed


def _meaningful_field_paths(
    target_rule_type: str,
    proposed_rule: dict,
    previous_rule: dict,
) -> list[str]:
    if target_rule_type == "LOAN":
        return [
            "region_type",
            "buyer_type",
            "purpose",
            "house_price_min",
            "house_price_max",
            "ltv_rate",
            "dsr_rate",
            "max_loan_amount",
        ]
    if target_rule_type == "TAX":
        max_count = max(
            len(previous_rule.get("brackets", [])),
            len(proposed_rule.get("brackets", [])),
        )
        paths = ["local_education_tax_rate"]
        for index in range(max_count):
            paths.extend(
                [
                    f"brackets[{index}].max_sale_price",
                    f"brackets[{index}].acquisition_tax_rate",
                ]
            )
        return paths
    if target_rule_type == "BROKERAGE":
        max_count = max(
            len(previous_rule.get("brackets", [])),
            len(proposed_rule.get("brackets", [])),
        )
        paths = ["legal_fee_fixed", "reserve_cost_rate"]
        for index in range(max_count):
            paths.extend(
                [
                    f"brackets[{index}].max_sale_price",
                    f"brackets[{index}].fee_rate",
                ]
            )
        return paths
    if target_rule_type == "REGION_POLICY":
        return [
            "region_level",
            "sido",
            "sigungu",
            "dong",
            "policy_type",
            "effective_from",
            "effective_to",
        ]
    if target_rule_type == "UNKNOWN":
        return ["raw_excerpt", "notes"]
    return list(proposed_rule.keys())


def _field_value(payload: dict | None, field_path: str):
    if payload is None:
        return None
    current = payload
    for part in field_path.split("."):
        if "[" in part and part.endswith("]"):
            field_name, index_text = part[:-1].split("[", 1)
            current = current.get(field_name, []) if isinstance(current, dict) else []
            try:
                current = current[int(index_text)]
            except (IndexError, TypeError, ValueError):
                return None
            continue
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _skip_noop_candidate(target_rule_type: str, changed_fields: list[str]) -> bool:
    return target_rule_type in {"LOAN", "TAX", "BROKERAGE"} and not changed_fields


def _build_changed_field_details(
    target_rule_type: str,
    previous_rule: dict | None,
    proposed_rule: dict | None,
    changed_fields: list[str],
) -> list[dict[str, object]]:
    details: list[dict[str, object]] = []
    previous_rule = previous_rule or {}
    proposed_rule = proposed_rule or {}
    for field_path in changed_fields:
        details.append(
            {
                "field": field_path,
                "label": _changed_field_label(target_rule_type, field_path),
                "previous_value": _format_changed_value(
                    target_rule_type,
                    field_path,
                    _field_value(previous_rule, field_path),
                ),
                "proposed_value": _format_changed_value(
                    target_rule_type,
                    field_path,
                    _field_value(proposed_rule, field_path),
                ),
            }
        )
    return details


def _build_change_summary(changed_field_details: list[dict[str, object]]) -> str:
    labels = [str(item["label"]) for item in changed_field_details]
    if not labels:
        return "변경 필드 없음"
    if len(labels) <= 3:
        return ", ".join(labels)
    return ", ".join(labels[:3]) + f" 외 {len(labels) - 3}건"


def _changed_field_label(target_rule_type: str, field_path: str) -> str:
    common_labels = {
        "region_type": "지역 유형",
        "buyer_type": "매수자 유형",
        "purpose": "투자 목적",
        "house_price_min": "주택가 하한",
        "house_price_max": "주택가 상한",
        "ltv_rate": "LTV 비율",
        "dsr_rate": "DSR 비율",
        "max_loan_amount": "최대 대출 한도",
        "local_education_tax_rate": "지방교육세 비율",
        "legal_fee_fixed": "법무비",
        "reserve_cost_rate": "예비비 비율",
        "region_level": "지역 레벨",
        "sido": "시도",
        "sigungu": "시군구",
        "dong": "동",
        "policy_type": "정책 유형",
        "effective_from": "적용 시작일",
        "effective_to": "적용 종료일",
        "raw_excerpt": "원문 발췌",
        "notes": "메모",
    }
    if field_path in common_labels:
        return common_labels[field_path]
    if target_rule_type == "TAX":
        if field_path.endswith(".max_sale_price"):
            return _bracket_label(field_path, "과세 구간 상한")
        if field_path.endswith(".acquisition_tax_rate"):
            return _bracket_label(field_path, "취득세 비율")
    if target_rule_type == "BROKERAGE":
        if field_path.endswith(".max_sale_price"):
            return _bracket_label(field_path, "가격 구간 상한")
        if field_path.endswith(".fee_rate"):
            return _bracket_label(field_path, "중개보수 비율")
    return field_path


def _bracket_label(field_path: str, suffix: str) -> str:
    prefix = field_path.split(".", 1)[0]
    index_text = prefix.removeprefix("brackets[").removesuffix("]")
    try:
        bracket_number = int(index_text) + 1
    except ValueError:
        bracket_number = 1
    return f"{bracket_number}구간 {suffix}"


def _format_changed_value(target_rule_type: str, field_path: str, value):
    if value in (None, ""):
        return "-"
    if field_path in {"ltv_rate", "dsr_rate", "local_education_tax_rate", "reserve_cost_rate"}:
        return f"{float(value) * 100:.1f}%"
    if field_path.endswith(".acquisition_tax_rate") or field_path.endswith(".fee_rate"):
        return f"{float(value) * 100:.1f}%"
    if field_path in {"max_loan_amount", "house_price_min", "house_price_max", "legal_fee_fixed"}:
        return f"{int(value):,}원"
    if field_path.endswith(".max_sale_price"):
        return f"{int(value):,}원"
    if field_path == "region_type":
        return {"NON_REGULATED": "비규제지역", "REGULATED": "규제지역"}.get(str(value), str(value))
    if field_path == "buyer_type":
        return {"NO_HOME": "무주택", "ONE_HOME": "1주택", "MULTI_HOME": "다주택"}.get(
            str(value), str(value)
        )
    if field_path == "purpose":
        return {"OWNER_OCCUPIED": "실거주", "INVESTMENT": "투자"}.get(str(value), str(value))
    if field_path == "policy_type":
        return {
            "REGULATED_AREA": "규제지역",
            "NON_REGULATED_AREA": "비규제지역",
            "LAND_TRANSACTION_PERMISSION": "토지거래허가구역",
        }.get(str(value), str(value))
    if field_path == "region_level":
        return {"SIDO": "시도", "SIGUNGU": "시군구", "DONG": "동"}.get(str(value), str(value))
    return str(value)


def _has_overlapping_region_policy(active_rules: list[dict], proposed_rule: dict) -> bool:
    for item in active_rules:
        if item.get("policy_type") == "LAND_TRANSACTION_PERMISSION":
            continue
        if proposed_rule.get("policy_type") == "LAND_TRANSACTION_PERMISSION":
            continue
        if item.get("policy_type") == proposed_rule.get("policy_type"):
            continue
        if not _same_region_scope(item, proposed_rule):
            continue
        if _date_ranges_overlap(item, proposed_rule):
            return True
    return False


def _same_region_scope(left: dict, right: dict) -> bool:
    return (
        str(left.get("region_level")) == str(right.get("region_level"))
        and str(left.get("sido")) == str(right.get("sido"))
        and (left.get("sigungu") or None) == (right.get("sigungu") or None)
        and (left.get("dong") or None) == (right.get("dong") or None)
    )


def _has_overlapping_loan_rule(active_rules: list[dict], proposed_rule: dict) -> bool:
    for item in active_rules:
        if item.get("region_type") != proposed_rule.get("region_type"):
            continue
        if item.get("buyer_type") != proposed_rule.get("buyer_type"):
            continue
        if item.get("purpose") != proposed_rule.get("purpose"):
            continue
        if not _date_ranges_overlap(item, proposed_rule):
            continue
        if _price_ranges_overlap(item, proposed_rule):
            return True
    return False


def _date_ranges_overlap(left: dict, right: dict) -> bool:
    left_start = date.fromisoformat(str(left["effective_from"]))
    right_start = date.fromisoformat(str(right["effective_from"]))
    left_end = (
        date.max
        if left.get("effective_to") in (None, "")
        else date.fromisoformat(str(left["effective_to"]))
    )
    right_end = (
        date.max
        if right.get("effective_to") in (None, "")
        else date.fromisoformat(str(right["effective_to"]))
    )
    return left_start <= right_end and right_start <= left_end


def _price_ranges_overlap(left: dict, right: dict) -> bool:
    left_min = int(left["house_price_min"])
    right_min = int(right["house_price_min"])
    left_max = (
        float("inf")
        if left.get("house_price_max") in (None, "")
        else int(left["house_price_max"])
    )
    right_max = (
        float("inf")
        if right.get("house_price_max") in (None, "")
        else int(right["house_price_max"])
    )
    return left_min <= right_max and right_min <= left_max


def _same_loan_rule_identity_dict(left: dict, right: dict) -> bool:
    return (
        str(left.get("region_type")) == str(right.get("region_type"))
        and str(left.get("buyer_type")) == str(right.get("buyer_type"))
        and str(left.get("purpose")) == str(right.get("purpose"))
        and int(left.get("house_price_min") or 0) == int(right.get("house_price_min") or 0)
        and (
            None
            if left.get("house_price_max") in (None, "")
            else int(left.get("house_price_max"))
        )
        == (
            None
            if right.get("house_price_max") in (None, "")
            else int(right.get("house_price_max"))
        )
        and str(left.get("effective_from")) == str(right.get("effective_from"))
        and (left.get("effective_to") or None) == (right.get("effective_to") or None)
    )


def _overlay_loan_rule(
    active_rules: list[dict],
    proposed_rule: dict,
    previous_rule: dict | None,
) -> list[dict]:
    next_rules: list[dict] = []
    proposed_start = date.fromisoformat(str(proposed_rule["effective_from"]))
    for item in active_rules:
        if previous_rule and _same_loan_rule_identity_dict(item, previous_rule):
            previous_start = date.fromisoformat(str(item["effective_from"]))
            if proposed_start <= previous_start:
                continue
            adjusted_end = proposed_start - timedelta(days=1)
            original_end = (
                None
                if item.get("effective_to") in (None, "")
                else date.fromisoformat(str(item["effective_to"]))
            )
            if original_end is not None and adjusted_end > original_end:
                adjusted_end = original_end
            if adjusted_end >= previous_start:
                adjusted_item = dict(item)
                adjusted_item["effective_to"] = adjusted_end.isoformat()
                next_rules.append(adjusted_item)
            continue
        if _same_loan_rule_identity_dict(item, proposed_rule):
            continue
        next_rules.append(item)
    next_rules.append(proposed_rule)
    return next_rules


def _to_loan_rule_dict(rule) -> dict:
    if isinstance(rule, dict):
        return dict(rule)
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


def _to_loan_rule(payload: dict):
    from config.loan_rules import LoanRule

    return LoanRule(
        rule_version=str(payload["rule_version"]),
        effective_from=str(payload["effective_from"]),
        effective_to=payload.get("effective_to"),
        region_type=str(payload["region_type"]),
        buyer_type=str(payload["buyer_type"]),
        purpose=str(payload["purpose"]),
        house_price_min=int(payload["house_price_min"]),
        house_price_max=None
        if payload.get("house_price_max") is None
        else int(payload["house_price_max"]),
        ltv_rate=float(payload["ltv_rate"]),
        dsr_rate=float(payload["dsr_rate"]),
        max_loan_amount=None
        if payload.get("max_loan_amount") is None
        else int(payload["max_loan_amount"]),
        description=str(payload["description"]),
    )
