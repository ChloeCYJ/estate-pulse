from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
import re


IMPORT_TARGET_RULE_TYPES = (
    "INTEGRATED",
    "LOAN",
    "TAX",
    "BROKERAGE",
    "REGION_POLICY",
    "POLICY_EVENT",
)
CANDIDATE_TARGET_RULE_TYPES = (
    "LOAN",
    "TAX",
    "BROKERAGE",
    "REGION_POLICY",
    "POLICY_EVENT",
    "UNKNOWN",
)


@dataclass
class ParsedPolicySection:
    section_id: str
    source_text: str
    target_rule_type: str
    confidence: float | None
    warnings: list[str]
    metadata: dict | None = None


@dataclass
class ParsedRuleCandidate:
    target_rule_type: str
    rule_name: str
    rule_version: str | None
    previous_rule: dict | None
    proposed_rule: dict
    confidence: float | None
    warnings: list[str]


class PolicyParser(ABC):
    parser_name: str

    @abstractmethod
    def analyze_policy_text(
        self,
        source_text: str,
        target_rule_type: str,
    ) -> list[ParsedPolicySection]:
        """Split and classify policy text into reviewable sections."""

    @abstractmethod
    def parse_policy_text(
        self,
        source_text: str,
        target_rule_type: str,
        effective_date: str | None,
        *,
        active_rules_by_type: dict[str, list[dict]] | None = None,
        selected_sections: list[ParsedPolicySection] | None = None,
    ) -> list[ParsedRuleCandidate]:
        """Convert selected policy sections into candidate rules."""


class MockPolicyParser(PolicyParser):
    parser_name = "mock"

    def analyze_policy_text(
        self,
        source_text: str,
        target_rule_type: str,
    ) -> list[ParsedPolicySection]:
        normalized_text = source_text.strip()
        if not normalized_text:
            raise ValueError("Policy text is required.")
        if target_rule_type not in IMPORT_TARGET_RULE_TYPES:
            raise ValueError(f"Unsupported target rule type: {target_rule_type}")

        chunks = _split_policy_text(normalized_text) or [normalized_text]
        if target_rule_type != "INTEGRATED":
            return [
                ParsedPolicySection(
                    section_id=f"section-{index + 1}",
                    source_text=chunk,
                    target_rule_type=target_rule_type,
                    confidence=0.95,
                    warnings=_section_warnings(target_rule_type, chunk),
                    metadata=_section_metadata(target_rule_type, chunk),
                )
                for index, chunk in enumerate(chunks)
            ]

        sections: list[ParsedPolicySection] = []
        for index, chunk in enumerate(chunks):
            classified_type, confidence, warnings = _classify_integrated_chunk(chunk)
            sections.append(
                ParsedPolicySection(
                    section_id=f"section-{index + 1}",
                    source_text=chunk,
                    target_rule_type=classified_type,
                    confidence=confidence,
                    warnings=warnings,
                    metadata=_section_metadata(classified_type, chunk),
                )
            )
        return sections

    def parse_policy_text(
        self,
        source_text: str,
        target_rule_type: str,
        effective_date: str | None,
        *,
        active_rules_by_type: dict[str, list[dict]] | None = None,
        selected_sections: list[ParsedPolicySection] | None = None,
    ) -> list[ParsedRuleCandidate]:
        normalized_text = source_text.strip()
        if not normalized_text:
            raise ValueError("Policy text is required.")
        if target_rule_type not in IMPORT_TARGET_RULE_TYPES:
            raise ValueError(f"Unsupported target rule type: {target_rule_type}")

        active_rules_by_type = active_rules_by_type or {}
        sections = selected_sections or self.analyze_policy_text(normalized_text, target_rule_type)
        candidates: list[ParsedRuleCandidate] = []

        for section in sections:
            if section.target_rule_type == "LOAN":
                candidates.extend(
                    self._parse_loan_candidates(
                        source_text=section.source_text,
                        effective_date=effective_date,
                        active_rules=active_rules_by_type.get("LOAN", []),
                        section_warnings=section.warnings,
                        confidence=section.confidence,
                    )
                )
            elif section.target_rule_type == "TAX":
                candidates.extend(
                    self._parse_tax_candidates(
                        source_text=section.source_text,
                        effective_date=effective_date,
                        active_rules=active_rules_by_type.get("TAX", []),
                        section_warnings=section.warnings,
                        confidence=section.confidence,
                    )
                )
            elif section.target_rule_type == "BROKERAGE":
                candidates.extend(
                    self._parse_brokerage_candidates(
                        source_text=section.source_text,
                        effective_date=effective_date,
                        active_rules=active_rules_by_type.get("BROKERAGE", []),
                        section_warnings=section.warnings,
                        confidence=section.confidence,
                    )
                )
            elif section.target_rule_type == "REGION_POLICY":
                candidates.extend(
                    self._parse_region_policy_candidates(
                        source_text=section.source_text,
                        effective_date=effective_date,
                        section_warnings=section.warnings,
                        confidence=section.confidence,
                        metadata=section.metadata or {},
                    )
                )
            elif section.target_rule_type == "POLICY_EVENT":
                candidates.extend(
                    self._parse_policy_event_candidates(
                        source_text=section.source_text,
                        effective_date=effective_date,
                        section_warnings=section.warnings,
                        confidence=section.confidence,
                    )
                )
            else:
                candidates.append(
                    ParsedRuleCandidate(
                        target_rule_type="UNKNOWN",
                        rule_name="Mock Unknown Candidate",
                        rule_version=None,
                        previous_rule=None,
                        proposed_rule={
                            "raw_excerpt": section.source_text,
                            "notes": "This section could not be classified confidently.",
                        },
                        confidence=section.confidence,
                        warnings=section.warnings
                        + ["UNKNOWN candidates are review-only and cannot be applied."],
                    )
                )
        return candidates

    def _parse_policy_event_candidates(
        self,
        *,
        source_text: str,
        effective_date: str | None,
        section_warnings: list[str],
        confidence: float | None,
    ) -> list[ParsedRuleCandidate]:
        warnings = list(section_warnings)
        extracted_dates = _extract_policy_dates(source_text)
        effective_to = extracted_dates.get("effective_to")
        effective_from = _resolve_policy_event_effective_from(
            effective_date=effective_date,
            extracted_effective_from=extracted_dates.get("effective_from"),
            extracted_effective_to=effective_to,
        )
        region_scope = _extract_region_scope(source_text)
        title = _build_policy_event_title(source_text)

        proposed_rule = {
            "policy_type": _infer_policy_event_type(source_text),
            "title": title,
            "summary": _build_policy_event_summary(source_text),
            "detail": source_text,
            "effective_from": effective_from,
            "effective_to": effective_to,
            "affected_region_sido": region_scope.get("sido"),
            "affected_region_sigungu": region_scope.get("sigungu"),
            "affected_region_dong": region_scope.get("dong"),
            "affected_buyer_type": _infer_policy_event_buyer_type(source_text),
            "affected_investment_purpose": _infer_policy_event_investment_purpose(source_text),
            "impact_level": _infer_policy_event_impact_level(source_text),
            "calculation_supported": False,
            "action_required": _infer_policy_event_action_required(source_text),
            "source_text": source_text,
            "source_name": None,
        }
        if effective_to and not effective_date and not extracted_dates.get("effective_from"):
            warnings.append(
                "Effective start date was inferred from the import date or today because only an end date was found."
            )
        return [
            ParsedRuleCandidate(
                target_rule_type="POLICY_EVENT",
                rule_name=title,
                rule_version=None,
                previous_rule=None,
                proposed_rule=proposed_rule,
                confidence=confidence,
                warnings=warnings,
            )
        ]

    def _parse_loan_candidates(
        self,
        *,
        source_text: str,
        effective_date: str | None,
        active_rules: list[dict],
        section_warnings: list[str],
        confidence: float | None,
    ) -> list[ParsedRuleCandidate]:
        base_rule = _find_rule(
            active_rules,
            lambda item: item.get("region_type") == "NON_REGULATED"
            and item.get("buyer_type") == "NO_HOME"
            and item.get("purpose") == "OWNER_OCCUPIED"
            and int(item.get("house_price_min") or 0) == 900_000_000,
        ) or (active_rules[0] if active_rules else None)

        if base_rule is None:
            base_rule = {
                "rule_version": "loan-default",
                "effective_from": effective_date or str(date.today()),
                "effective_to": None,
                "region_type": "NON_REGULATED",
                "buyer_type": "NO_HOME",
                "purpose": "OWNER_OCCUPIED",
                "house_price_min": 900_000_000,
                "house_price_max": 1_499_999_999,
                "ltv_rate": 0.60,
                "dsr_rate": 0.40,
                "max_loan_amount": None,
                "description": "Mock default loan rule",
            }

        proposed_rule = dict(base_rule)
        proposed_rule["rule_version"] = _next_rule_version(str(base_rule.get("rule_version") or "loan"))
        proposed_rule["effective_from"] = effective_date or str(date.today())
        proposed_rule["description"] = "Mock parser generated loan candidate from pasted policy text."

        warnings = list(section_warnings)
        ltv_rate = _extract_ratio(source_text, ("ltv",))
        dsr_rate = _extract_ratio(source_text, ("dsr",))
        max_loan_amount = _extract_money(source_text, keywords=("최대", "한도"))

        if ltv_rate is not None:
            proposed_rule["ltv_rate"] = ltv_rate
        else:
            warnings.append("LTV ratio was not clear, so the existing value was kept.")

        if dsr_rate is not None:
            proposed_rule["dsr_rate"] = dsr_rate
        else:
            warnings.append("DSR ratio was not clear, so the existing value was kept.")

        if max_loan_amount is not None:
            proposed_rule["max_loan_amount"] = max_loan_amount
        else:
            warnings.append("Maximum loan amount was not clear, so the existing value was kept.")

        if "비규제" in source_text:
            proposed_rule["region_type"] = "NON_REGULATED"
        elif "규제" in source_text:
            proposed_rule["region_type"] = "REGULATED"

        if "1주택" in source_text:
            proposed_rule["buyer_type"] = "ONE_HOME"
        elif "다주택" in source_text:
            proposed_rule["buyer_type"] = "MULTI_HOME"
        elif "무주택" in source_text:
            proposed_rule["buyer_type"] = "NO_HOME"

        if "투자" in source_text:
            proposed_rule["purpose"] = "INVESTMENT"
        elif "실거주" in source_text:
            proposed_rule["purpose"] = "OWNER_OCCUPIED"

        return [
            ParsedRuleCandidate(
                target_rule_type="LOAN",
                rule_name="Mock Loan Candidate",
                rule_version=str(proposed_rule.get("rule_version") or ""),
                previous_rule=base_rule,
                proposed_rule=proposed_rule,
                confidence=confidence,
                warnings=warnings,
            )
        ]

    def _parse_tax_candidates(
        self,
        *,
        source_text: str,
        effective_date: str | None,
        active_rules: list[dict],
        section_warnings: list[str],
        confidence: float | None,
    ) -> list[ParsedRuleCandidate]:
        base_rule = active_rules[0] if active_rules else None
        proposed_rule = dict(base_rule or {})
        proposed_rule["version"] = _next_rule_version(str(proposed_rule.get("version") or "tax"))
        proposed_rule["rule_name"] = "Mock Tax Candidate"
        proposed_rule["effective_from"] = effective_date or str(date.today())
        proposed_rule["effective_to"] = proposed_rule.get("effective_to")
        proposed_rule["description"] = "Mock parser generated tax rule candidate."

        warnings = list(section_warnings)
        acquisition_rate = _extract_ratio(source_text, ("취득세", "acquisition"))
        education_rate = _extract_ratio(source_text, ("지방교육세", "education"))

        brackets = [dict(item) for item in proposed_rule.get("brackets", [])]
        if brackets and acquisition_rate is not None:
            brackets[0]["acquisition_tax_rate"] = acquisition_rate
        else:
            warnings.append("Acquisition tax rate was not clear, so the first bracket was kept.")
        proposed_rule["brackets"] = brackets

        if education_rate is not None:
            proposed_rule["local_education_tax_rate"] = education_rate
        else:
            warnings.append("Local education tax rate was not clear, so the existing value was kept.")

        return [
            ParsedRuleCandidate(
                target_rule_type="TAX",
                rule_name="Mock Tax Candidate",
                rule_version=str(proposed_rule.get("version") or ""),
                previous_rule=base_rule,
                proposed_rule=proposed_rule,
                confidence=confidence,
                warnings=warnings,
            )
        ]

    def _parse_brokerage_candidates(
        self,
        *,
        source_text: str,
        effective_date: str | None,
        active_rules: list[dict],
        section_warnings: list[str],
        confidence: float | None,
    ) -> list[ParsedRuleCandidate]:
        base_rule = active_rules[0] if active_rules else None
        proposed_rule = dict(base_rule or {})
        proposed_rule["version"] = _next_rule_version(str(proposed_rule.get("version") or "brokerage"))
        proposed_rule["rule_name"] = "Mock Brokerage Candidate"
        proposed_rule["effective_from"] = effective_date or str(date.today())
        proposed_rule["effective_to"] = proposed_rule.get("effective_to")
        proposed_rule["description"] = "Mock parser generated brokerage rule candidate."

        warnings = list(section_warnings)
        brokerage_rate = _extract_ratio(source_text, ("중개", "brokerage"))
        reserve_rate = _extract_ratio(source_text, ("예비비", "reserve"))
        legal_fee = _extract_money(source_text, keywords=("법무", "legal"))

        brackets = [dict(item) for item in proposed_rule.get("brackets", [])]
        if brackets and brokerage_rate is not None:
            brackets[0]["fee_rate"] = brokerage_rate
        else:
            warnings.append("Brokerage fee rate was not clear, so the first bracket was kept.")
        proposed_rule["brackets"] = brackets

        if reserve_rate is not None:
            proposed_rule["reserve_cost_rate"] = reserve_rate
        else:
            warnings.append("Reserve rate was not clear, so the existing value was kept.")

        if legal_fee is not None:
            proposed_rule["legal_fee_fixed"] = legal_fee
        else:
            warnings.append("Legal fee was not clear, so the existing value was kept.")

        return [
            ParsedRuleCandidate(
                target_rule_type="BROKERAGE",
                rule_name="Mock Brokerage Candidate",
                rule_version=str(proposed_rule.get("version") or ""),
                previous_rule=base_rule,
                proposed_rule=proposed_rule,
                confidence=confidence,
                warnings=warnings,
            )
        ]

    def _parse_region_policy_candidates(
        self,
        *,
        source_text: str,
        effective_date: str | None,
        section_warnings: list[str],
        confidence: float | None,
        metadata: dict,
    ) -> list[ParsedRuleCandidate]:
        warnings = list(section_warnings)
        policy_type = _infer_region_policy_type(source_text)
        expanded_regions = _normalize_expanded_regions(metadata.get("expanded_regions"))
        requires_region_expansion = bool(metadata.get("requires_region_expansion"))

        if policy_type is None:
            policy_type = "REGULATED_AREA"
            warnings.append("Region policy type was not clear, so REGULATED_AREA was used.")
        if requires_region_expansion and not expanded_regions:
            return []
        if not expanded_regions:
            region_scope = _extract_region_scope(source_text)
            if not region_scope["sido"]:
                warnings.append("Region scope was not identified clearly.")
            expanded_regions = [region_scope]

        candidates: list[ParsedRuleCandidate] = []
        for region_scope in expanded_regions:
            proposed_rule = {
                "region_level": region_scope["region_level"],
                "sido": region_scope["sido"],
                "sigungu": region_scope["sigungu"],
                "dong": region_scope["dong"],
                "policy_type": policy_type,
                "effective_from": effective_date or str(date.today()),
                "effective_to": None,
                "notes": "Mock parser generated region policy candidate.",
            }
            candidates.append(
                ParsedRuleCandidate(
                    target_rule_type="REGION_POLICY",
                    rule_name="Mock Region Policy Candidate",
                    rule_version=None,
                    previous_rule=None,
                    proposed_rule=proposed_rule,
                    confidence=confidence,
                    warnings=list(warnings),
                )
            )
        return candidates


class OpenAIPolicyParser(PolicyParser):
    parser_name = "openai"

    def analyze_policy_text(
        self,
        source_text: str,
        target_rule_type: str,
    ) -> list[ParsedPolicySection]:
        raise NotImplementedError("OpenAIPolicyParser is a placeholder. API integration is not enabled.")

    def parse_policy_text(
        self,
        source_text: str,
        target_rule_type: str,
        effective_date: str | None,
        *,
        active_rules_by_type: dict[str, list[dict]] | None = None,
        selected_sections: list[ParsedPolicySection] | None = None,
    ) -> list[ParsedRuleCandidate]:
        raise NotImplementedError("OpenAIPolicyParser is a placeholder. API integration is not enabled.")


class ClaudePolicyParser(PolicyParser):
    parser_name = "claude"

    def analyze_policy_text(
        self,
        source_text: str,
        target_rule_type: str,
    ) -> list[ParsedPolicySection]:
        raise NotImplementedError("ClaudePolicyParser is a placeholder. API integration is not enabled.")

    def parse_policy_text(
        self,
        source_text: str,
        target_rule_type: str,
        effective_date: str | None,
        *,
        active_rules_by_type: dict[str, list[dict]] | None = None,
        selected_sections: list[ParsedPolicySection] | None = None,
    ) -> list[ParsedRuleCandidate]:
        raise NotImplementedError("ClaudePolicyParser is a placeholder. API integration is not enabled.")


class OllamaPolicyParser(PolicyParser):
    parser_name = "ollama"

    def analyze_policy_text(
        self,
        source_text: str,
        target_rule_type: str,
    ) -> list[ParsedPolicySection]:
        raise NotImplementedError("OllamaPolicyParser is a placeholder. API integration is not enabled.")

    def parse_policy_text(
        self,
        source_text: str,
        target_rule_type: str,
        effective_date: str | None,
        *,
        active_rules_by_type: dict[str, list[dict]] | None = None,
        selected_sections: list[ParsedPolicySection] | None = None,
    ) -> list[ParsedRuleCandidate]:
        raise NotImplementedError("OllamaPolicyParser is a placeholder. API integration is not enabled.")


def get_default_policy_parsers() -> dict[str, PolicyParser]:
    parsers: list[PolicyParser] = [
        MockPolicyParser(),
        OpenAIPolicyParser(),
        ClaudePolicyParser(),
        OllamaPolicyParser(),
    ]
    return {parser.parser_name: parser for parser in parsers}


def _split_policy_text(source_text: str) -> list[str]:
    parts = re.split(r"(?:\n{2,}|[.;]\s+|\r\n)", source_text)
    return [item.strip() for item in parts if item and item.strip()]


def _classify_integrated_chunk(source_text: str) -> tuple[str, float, list[str]]:
    normalized = source_text.lower()
    warnings: list[str] = []

    if _is_policy_event_text(source_text):
        warnings.extend(_section_warnings("POLICY_EVENT", source_text))
        return "POLICY_EVENT", 0.82, warnings

    loan_keywords = ("ltv", "dsr", "대출", "실거주", "무주택")
    tax_keywords = ("취득세", "지방교육세", "tax")
    brokerage_keywords = ("중개", "법무", "예비비", "brokerage", "legal")
    region_policy_keywords = (
        "규제지역",
        "비규제지역",
        "토지거래허가구역",
        "\ud22c\uae30\uacfc\uc5f4\uc9c0\uad6c",
        "\uc870\uc815\ub300\uc0c1\uc9c0\uc5ed",
        "서울",
        "경기",
        "지역",
    )

    loan_score = sum(keyword in normalized or keyword in source_text for keyword in loan_keywords)
    tax_score = sum(keyword in normalized or keyword in source_text for keyword in tax_keywords)
    brokerage_score = sum(keyword in normalized or keyword in source_text for keyword in brokerage_keywords)
    region_policy_score = sum(
        keyword in normalized or keyword in source_text for keyword in region_policy_keywords
    )

    top_score = max(loan_score, tax_score, brokerage_score, region_policy_score)
    if top_score == 0:
        warnings.append("No clear rule keywords were found in this section.")
        return "UNKNOWN", 0.28, warnings

    if (
        region_policy_score == top_score
        and region_policy_score > loan_score
        and region_policy_score > tax_score
        and region_policy_score > brokerage_score
    ):
        warnings.extend(_section_warnings("REGION_POLICY", source_text))
        return "REGION_POLICY", 0.76, warnings
    if loan_score == top_score and loan_score > tax_score and loan_score > brokerage_score:
        warnings.extend(_section_warnings("LOAN", source_text))
        return "LOAN", 0.78, warnings
    if tax_score == top_score and tax_score > loan_score and tax_score > brokerage_score:
        warnings.extend(_section_warnings("TAX", source_text))
        return "TAX", 0.74, warnings
    if brokerage_score == top_score and brokerage_score > loan_score and brokerage_score > tax_score:
        warnings.extend(_section_warnings("BROKERAGE", source_text))
        return "BROKERAGE", 0.73, warnings

    warnings.append("This section contains mixed keywords and needs manual review.")
    return "UNKNOWN", 0.42, warnings


def _section_warnings(target_rule_type: str, source_text: str) -> list[str]:
    warnings: list[str] = []
    if target_rule_type == "LOAN":
        if _extract_ratio(source_text, ("ltv",)) is None:
            warnings.append("LTV ratio may be missing.")
        if _extract_ratio(source_text, ("dsr",)) is None:
            warnings.append("DSR ratio may be missing.")
    elif target_rule_type == "TAX":
        if _extract_ratio(source_text, ("취득세", "acquisition")) is None:
            warnings.append("Acquisition tax rate may be missing.")
    elif target_rule_type == "BROKERAGE":
        if _extract_ratio(source_text, ("중개", "brokerage")) is None:
            warnings.append("Brokerage rate may be missing.")
    elif target_rule_type == "REGION_POLICY":
        if _infer_region_policy_type(source_text) is None:
            warnings.append("Region policy type may be missing.")
        metadata = _section_metadata(target_rule_type, source_text)
        if metadata.get("requires_region_expansion"):
            warnings.append("Region group phrase needs manual expansion before candidate generation.")
        elif not _extract_region_scope(source_text)["sido"]:
            warnings.append("Region scope may be missing.")
    elif target_rule_type == "POLICY_EVENT":
        if not _contains_explicit_policy_date(source_text):
            warnings.append("Effective date may require manual confirmation.")
    return warnings


def _section_metadata(target_rule_type: str, source_text: str) -> dict:
    if target_rule_type != "REGION_POLICY":
        return {}
    expansion = _extract_region_group_expansion(source_text)
    return {
        "requires_region_expansion": expansion["requires_manual_expansion"],
        "region_group_label": expansion["group_label"],
        "expanded_regions": expansion["expanded_regions"],
        "review_state": "REVIEW_REQUIRED" if expansion["requires_manual_expansion"] else "READY",
    }


def _infer_region_policy_type(source_text: str) -> str | None:
    if "\ud1a0\uc9c0\uac70\ub798\ud5c8\uac00\uad6c\uc5ed" in source_text:
        return "LAND_TRANSACTION_PERMISSION"
    if "\ud22c\uae30\uacfc\uc5f4\uc9c0\uad6c" in source_text:
        return "SPECULATION_OVERHEATED_DISTRICT"
    if "\uc870\uc815\ub300\uc0c1\uc9c0\uc5ed" in source_text:
        return "ADJUSTMENT_TARGET_AREA"
    if "\ube44\uaddc\uc81c\uc9c0\uc5ed" in source_text:
        return "NON_REGULATED_AREA"
    if "\uaddc\uc81c\uc9c0\uc5ed" in source_text:
        return "REGULATED_AREA"
    return None


def _extract_region_scope(source_text: str) -> dict[str, str | None]:
    sido = None
    sigungu = None
    dong = None
    region_level = "SIDO"

    if "\uc11c\uc6b8" in source_text:
        sido = "\uc11c\uc6b8"
    elif "\uacbd\uae30" in source_text:
        sido = "\uacbd\uae30"

    if "서울" in source_text:
        sido = "서울"
    elif "경기" in source_text:
        sido = "경기"

    sigungu_match = re.search(
        r"(강남구|서초구|송파구|용산구|영등포구|양천구|강동구|성남시 분당구|수원시 영통구)",
        source_text,
    )
    if sigungu_match:
        sigungu = sigungu_match.group(1)
        region_level = "SIGUNGU"
    if sigungu is None:
        sigungu_match = re.search(
            (
                r"(\uc885\ub85c\uad6c|\uc911\uad6c|\uc6a9\uc0b0\uad6c|\uc131\ub3d9\uad6c|"
                r"\uad11\uc9c4\uad6c|\ub3d9\ub300\ubb38\uad6c|\uc911\ub791\uad6c|\uc131\ubd81\uad6c|"
                r"\uac15\ubd81\uad6c|\ub3c4\ubd09\uad6c|\ub178\uc6d0\uad6c|\uc740\ud3c9\uad6c|"
                r"\uc11c\ub300\ubb38\uad6c|\ub9c8\ud3ec\uad6c|\uc591\ucc9c\uad6c|\uac15\uc11c\uad6c|"
                r"\uad6c\ub85c\uad6c|\uae08\ucc9c\uad6c|\uc601\ub4f1\ud3ec\uad6c|\ub3d9\uc791\uad6c|"
                r"\uad00\uc545\uad6c|\uc11c\ucd08\uad6c|\uac15\ub0a8\uad6c|\uc1a1\ud30c\uad6c|"
                r"\uac15\ub3d9\uad6c|\uc218\uc6d0\uc2dc|\uc131\ub0a8\uc2dc|\uace0\uc591\uc2dc|"
                r"\uc6a9\uc778\uc2dc|\ubd80\ucc9c\uc2dc|\uc548\uc0b0\uc2dc|\uc548\uc591\uc2dc|"
                r"\ub0a8\uc591\uc8fc\uc2dc|\ud654\uc131\uc2dc|\ud3c9\ud0dd\uc2dc|\uc758\uc815\ubd80\uc2dc|"
                r"\uc2dc\ud765\uc2dc|\ud30c\uc8fc\uc2dc|\uae40\ud3ec\uc2dc|\uad11\uba85\uc2dc|"
                r"\uad70\ud3ec\uc2dc|\uad11\uc8fc\uc2dc|\uc774\ucc9c\uc2dc|\uc624\uc0b0\uc2dc|"
                r"\ud558\ub0a8\uc2dc|\uc758\uc655\uc2dc|\uc591\uc8fc\uc2dc|\uad6c\ub9ac\uc2dc|"
                r"\uc548\uc131\uc2dc|\ud3ec\ucc9c\uc2dc|\uc591\ud3c9\uad70|\uc5ec\uc8fc\uc2dc|"
                r"\ub3d9\ub450\ucc9c\uc2dc|\uacfc\ucc9c\uc2dc)"
            ),
            source_text,
        )
        if sigungu_match:
            sigungu = sigungu_match.group(1)
            region_level = "SIGUNGU"

    dong_match = re.search(r"([가-힣]+동)", source_text)
    if dong_match and sigungu is not None:
        dong = dong_match.group(1)
        region_level = "DONG"

    return {
        "region_level": region_level,
        "sido": sido,
        "sigungu": sigungu,
        "dong": dong,
    }


def _extract_region_group_expansion(source_text: str) -> dict:
    if "서울 전역" in source_text:
        return {
            "group_label": "서울 전역",
            "requires_manual_expansion": False,
            "expanded_regions": [
                {
                    "region_level": "SIDO",
                    "sido": "서울",
                    "sigungu": None,
                    "dong": None,
                }
            ],
        }
    if "경기 주요 12개 지역" in source_text:
        return {
            "group_label": "경기 주요 12개 지역",
            "requires_manual_expansion": True,
            "expanded_regions": [],
        }

    explicit_regions = _extract_explicit_region_list(source_text)
    if explicit_regions:
        return {
            "group_label": None,
            "requires_manual_expansion": False,
            "expanded_regions": explicit_regions,
        }
    return {
        "group_label": None,
        "requires_manual_expansion": False,
        "expanded_regions": [],
    }


def _extract_explicit_region_list(source_text: str) -> list[dict]:
    matches = re.findall(
        r"(서울\s*[가-힣]+구|경기\s*[가-힣]+시\s*[가-힣]+구|경기\s*[가-힣]+시|[가-힣]+시\s*[가-힣]+구)",
        source_text,
    )
    expanded: list[dict] = []
    for match in matches:
        normalized = " ".join(match.split())
        parts = normalized.split()
        if not parts:
            continue
        if parts[0] == "서울" and len(parts) >= 2:
            expanded.append(
                {
                    "region_level": "SIGUNGU",
                    "sido": "서울",
                    "sigungu": parts[1],
                    "dong": None,
                }
            )
        elif parts[0] == "경기" and len(parts) >= 3:
            expanded.append(
                {
                    "region_level": "SIGUNGU",
                    "sido": "경기",
                    "sigungu": f"{parts[1]} {parts[2]}",
                    "dong": None,
                }
            )
        elif len(parts) >= 2 and parts[0].endswith("시") and parts[1].endswith("구"):
            expanded.append(
                {
                    "region_level": "SIGUNGU",
                    "sido": "경기",
                    "sigungu": f"{parts[0]} {parts[1]}",
                    "dong": None,
                }
            )
    return expanded


def _normalize_expanded_regions(value) -> list[dict]:
    expanded_regions: list[dict] = []
    if not isinstance(value, list):
        return expanded_regions
    for item in value:
        if not isinstance(item, dict):
            continue
        expanded_regions.append(
            {
                "region_level": str(item.get("region_level") or "SIDO"),
                "sido": item.get("sido"),
                "sigungu": item.get("sigungu"),
                "dong": item.get("dong"),
            }
        )
    return expanded_regions


def _is_policy_event_text(source_text: str) -> bool:
    strong_keywords = (
        "유예",
        "종료",
        "종료일",
        "시행일",
        "잔금기한",
        "실거주 의무",
        "보유",
        "매도",
        "리스크",
        "안내",
        "연장",
    )
    return any(keyword in source_text for keyword in strong_keywords)


def _contains_explicit_policy_date(source_text: str) -> bool:
    return bool(re.search(r"20\d{2}[.\-/년]\s*\d{1,2}[.\-/월]\s*\d{1,2}", source_text))


def _extract_policy_dates(source_text: str) -> dict[str, str | None]:
    matches = re.findall(r"(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})", source_text)
    parsed_dates = [
        f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        for year, month, day in matches
    ]
    if not parsed_dates:
        return {"effective_from": None, "effective_to": None}
    if any(keyword in source_text for keyword in ("종료", "종료일", "만료")):
        return {"effective_from": None, "effective_to": parsed_dates[0]}
    return {
        "effective_from": parsed_dates[0],
        "effective_to": parsed_dates[1] if len(parsed_dates) > 1 else None,
    }


def _resolve_policy_event_effective_from(
    *,
    effective_date: str | None,
    extracted_effective_from: str | None,
    extracted_effective_to: str | None,
) -> str:
    if extracted_effective_from:
        return extracted_effective_from
    if extracted_effective_to and effective_date:
        try:
            import_date = date.fromisoformat(effective_date)
            end_date = date.fromisoformat(extracted_effective_to)
        except ValueError:
            return extracted_effective_to
        return min(import_date, end_date).isoformat()
    if effective_date:
        return effective_date
    return extracted_effective_to or str(date.today())


def _infer_policy_event_type(source_text: str) -> str:
    if any(keyword in source_text for keyword in ("LTV", "DSR", "대출")):
        return "LOAN"
    if any(keyword in source_text for keyword in ("양도세", "취득세", "보유세", "세금")):
        return "TAX"
    if any(keyword in source_text for keyword in ("토지거래허가", "허가구역")):
        return "PERMISSION"
    if any(keyword in source_text for keyword in ("잔금", "계약")):
        return "CONTRACT"
    if any(keyword in source_text for keyword in ("매도", "거래", "보유")):
        return "TRANSACTION"
    if any(keyword in source_text for keyword in ("조정대상지역", "규제지역")):
        return "REGULATION"
    return "INFO"


def _build_policy_event_title(source_text: str) -> str:
    compact = " ".join(source_text.split())
    if len(compact) <= 60:
        return compact
    return compact[:57].rstrip() + "..."


def _build_policy_event_summary(source_text: str) -> str:
    compact = " ".join(source_text.split())
    if len(compact) <= 140:
        return compact
    return compact[:137].rstrip() + "..."


def _infer_policy_event_buyer_type(source_text: str) -> str:
    if "다주택" in source_text:
        return "MULTI_HOME"
    if "1주택" in source_text or "일주택" in source_text:
        return "ONE_HOME"
    if "무주택" in source_text:
        return "NO_HOME"
    return "ANY"


def _infer_policy_event_investment_purpose(source_text: str) -> str:
    if any(keyword in source_text for keyword in ("실거주", "거주")):
        return "OWNER_OCCUPIED"
    if any(keyword in source_text for keyword in ("투자", "임대", "매도")):
        return "INVESTMENT"
    return "ANY"


def _infer_policy_event_impact_level(source_text: str) -> str:
    if any(
        keyword in source_text
        for keyword in ("양도세", "종료", "토지거래허가", "실거주 의무", "잔금기한", "리스크")
    ):
        return "HIGH"
    if any(keyword in source_text for keyword in ("유예", "연장", "시행", "조정대상지역")):
        return "MEDIUM"
    return "LOW"


def _infer_policy_event_action_required(source_text: str) -> bool:
    return any(
        keyword in source_text
        for keyword in ("종료", "잔금기한", "실거주 의무", "허가", "리스크", "기한", "매도", "계약")
    )


def _find_rule(items: list[dict], predicate) -> dict | None:
    for item in items:
        if predicate(item):
            return item
    return None


def _next_rule_version(current_version: str) -> str:
    return f"{current_version}-candidate"


def _extract_ratio(source_text: str, keywords: tuple[str, ...]) -> float | None:
    for keyword in keywords:
        patterns = [
            rf"{re.escape(keyword)}[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%",
            rf"([0-9]+(?:\.[0-9]+)?)\s*%[^a-zA-Z0-9가-힣]*{re.escape(keyword)}",
        ]
        for pattern in patterns:
            match = re.search(pattern, source_text, flags=re.IGNORECASE)
            if match:
                return float(match.group(1)) / 100
    return None


def _extract_money(source_text: str, keywords: tuple[str, ...] = ()) -> int | None:
    for keyword in keywords:
        eok_match = re.search(
            rf"{re.escape(keyword)}[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*억",
            source_text,
            flags=re.IGNORECASE,
        )
        if eok_match:
            return int(float(eok_match.group(1)) * 100_000_000)
        money_match = re.search(
            rf"{re.escape(keyword)}[^0-9]*([0-9][0-9,]{{5,}})",
            source_text,
            flags=re.IGNORECASE,
        )
        if money_match:
            return int(money_match.group(1).replace(",", ""))

    eok_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*억", source_text)
    if eok_match:
        return int(float(eok_match.group(1)) * 100_000_000)

    money_match = re.search(r"([0-9][0-9,]{5,})", source_text)
    if money_match:
        return int(money_match.group(1).replace(",", ""))
    return None
