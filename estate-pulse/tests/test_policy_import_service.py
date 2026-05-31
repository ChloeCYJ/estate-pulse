from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.database import initialize_database
from modules.repositories.policy_event_candidate_repository import PolicyEventCandidateRepository
from modules.repositories.policy_event_repository import PolicyEventRepository
from modules.repositories.policy_import_repository import PolicyImportRepository
from modules.repositories.region_policy_repository import RegionPolicyRepository
from modules.repositories.rule_candidate_repository import RuleCandidateRepository
from modules.services.policy_event_service import PolicyEventService
from modules.services.policy_import_service import (
    CANDIDATE_STATUS_APPROVED,
    PolicyImportService,
)
from modules.services.region_policy_service import RegionPolicyService
from modules.services.rule_runtime_service import RuleRuntimeService


class PolicyImportServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)
        self.policy_import_repository = PolicyImportRepository(self.database_path)
        self.rule_candidate_repository = RuleCandidateRepository(self.database_path)
        self.policy_event_repository = PolicyEventRepository(self.database_path)
        self.policy_event_candidate_repository = PolicyEventCandidateRepository(self.database_path)
        self.region_policy_repository = RegionPolicyRepository(self.database_path)
        self.rule_runtime_service = RuleRuntimeService(
            rule_candidate_repository=self.rule_candidate_repository,
        )
        self.region_policy_service = RegionPolicyService(
            region_policy_repository=self.region_policy_repository,
        )
        self.policy_event_service = PolicyEventService(
            policy_event_repository=self.policy_event_repository,
        )
        self.service = PolicyImportService(
            policy_import_repository=self.policy_import_repository,
            rule_candidate_repository=self.rule_candidate_repository,
            policy_event_candidate_repository=self.policy_event_candidate_repository,
            rule_runtime_service=self.rule_runtime_service,
            region_policy_service=self.region_policy_service,
            policy_event_service=self.policy_event_service,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_preview_policy_sections_for_integrated_document(self) -> None:
        sections = self.service.preview_policy_sections(
            source_text=(
                "서울 전역은 규제지역입니다. "
                "무주택 실거주자는 9억~15억 구간 LTV 55% DSR 40% 최대 7억 적용. "
                "취득세 1.5%, 지방교육세 0.1 적용. "
                "중개보수 0.4%, 법무비 30만원. "
                "기타 부칙은 추후 고시."
            ),
            target_rule_type="INTEGRATED",
            parser_name="mock",
        )

        self.assertEqual(len(sections), 5)
        self.assertEqual(
            [section["target_rule_type"] for section in sections],
            ["REGION_POLICY", "LOAN", "TAX", "BROKERAGE", "UNKNOWN"],
        )

    def test_mock_parser_creates_loan_candidate(self) -> None:
        result = self.service.create_policy_import(
            source_text="비규제지역 무주택 실거주자 9억~15억 구간 LTV 55% DSR 40% 최대 7억 적용",
            source_name="샘플 정책",
            target_rule_type="LOAN",
            effective_date="2026-06-01",
            parser_name="mock",
        )

        self.assertEqual(result["parser_status"], "COMPLETED")
        detail = self.service.get_policy_import_detail(result["policy_import_id"])
        candidate = detail["candidates"][0]
        self.assertEqual(candidate["target_rule_type"], "LOAN")
        self.assertEqual(candidate["proposed_rule"]["ltv_rate"], 0.55)
        self.assertEqual(candidate["proposed_rule"]["dsr_rate"], 0.40)
        self.assertEqual(candidate["proposed_rule"]["max_loan_amount"], 700_000_000)

    def test_partial_loan_change_keeps_existing_values_and_marks_changed_field_only(self) -> None:
        result = self.service.create_policy_import(
            source_text="비규제지역 무주택 실거주자 DSR 35% 적용",
            source_name="부분 변경 정책",
            target_rule_type="LOAN",
            effective_date="2026-06-01",
            parser_name="mock",
        )

        detail = self.service.get_policy_import_detail(result["policy_import_id"])
        self.assertEqual(len(detail["candidates"]), 1)
        candidate = detail["candidates"][0]
        self.assertEqual(candidate["target_rule_type"], "LOAN")
        self.assertEqual(candidate["proposed_rule"]["ltv_rate"], 0.60)
        self.assertEqual(candidate["proposed_rule"]["dsr_rate"], 0.35)
        self.assertIsNone(candidate["proposed_rule"]["max_loan_amount"])
        self.assertEqual(candidate["changed_fields_list"], ["dsr_rate"])
        self.assertEqual(candidate["change_summary"], "DSR 비율")

    def test_noop_loan_section_does_not_create_candidate(self) -> None:
        result = self.service.create_policy_import(
            source_text="비규제지역 무주택 실거주자 대출 기준 유지",
            source_name="변경 없음 정책",
            target_rule_type="LOAN",
            effective_date="2026-06-01",
            parser_name="mock",
        )

        self.assertEqual(result["candidate_ids"], [])
        detail = self.service.get_policy_import_detail(result["policy_import_id"])
        self.assertEqual(detail["candidates"], [])

    def test_region_group_phrase_requires_manual_expansion(self) -> None:
        sections = self.service.preview_policy_sections(
            source_text="경기 주요 12개 지역은 규제지역입니다.",
            target_rule_type="REGION_POLICY",
            parser_name="mock",
        )

        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["target_rule_type"], "REGION_POLICY")
        self.assertTrue(sections[0]["metadata"]["requires_region_expansion"])
        self.assertEqual(sections[0]["metadata"]["expanded_regions"], [])
        self.assertEqual(sections[0]["metadata"]["review_state"], "REVIEW_REQUIRED")

    def test_unresolved_region_group_cannot_generate_candidates(self) -> None:
        sections = self.service.preview_policy_sections(
            source_text="경기 주요 12개 지역은 규제지역입니다.",
            target_rule_type="REGION_POLICY",
            parser_name="mock",
        )

        with self.assertRaisesRegex(ValueError, "Region group expansion is unresolved"):
            self.service.create_policy_import_from_sections(
                source_text="경기 주요 12개 지역은 규제지역입니다.",
                source_name="지역 그룹 정책",
                target_rule_type="REGION_POLICY",
                effective_date="2026-06-01",
                parser_name="mock",
                selected_sections=sections,
            )

    def test_integrated_parser_returns_grouped_candidates(self) -> None:
        result = self.service.create_policy_import(
            source_text=(
                "서울 전역은 규제지역입니다. "
                "무주택 실거주자는 9억~15억 구간 LTV 55% DSR 40% 최대 7억 적용. "
                "취득세 1.5%, 지방교육세 0.1 적용. "
                "중개보수 0.4%, 법무비 30만원. "
                "기타 부칙은 추후 고시."
            ),
            source_name="통합 정책",
            target_rule_type="INTEGRATED",
            effective_date="2026-06-01",
            parser_name="mock",
        )

        detail = self.service.get_policy_import_detail(result["policy_import_id"])
        candidate_types = {item["target_rule_type"] for item in detail["candidates"]}
        self.assertEqual(
            candidate_types,
            {"REGION_POLICY", "LOAN", "TAX", "UNKNOWN"},
        )

    def test_selected_sections_only_generate_candidates(self) -> None:
        sections = self.service.preview_policy_sections(
            source_text=(
                "서울 전역은 규제지역입니다. "
                "취득세 1.5%, 지방교육세 0.1 적용. "
                "중개보수 0.4%, 법무비 30만원."
            ),
            target_rule_type="INTEGRATED",
            parser_name="mock",
        )
        selected_sections = [
            section
            for section in sections
            if section["target_rule_type"] in {"REGION_POLICY", "TAX"}
        ]

        result = self.service.create_policy_import_from_sections(
            source_text="통합 정책",
            source_name="선택 테스트",
            target_rule_type="INTEGRATED",
            effective_date="2026-06-01",
            parser_name="mock",
            selected_sections=selected_sections,
        )

        detail = self.service.get_policy_import_detail(result["policy_import_id"])
        candidate_types = {item["target_rule_type"] for item in detail["candidates"]}
        self.assertEqual(candidate_types, {"REGION_POLICY", "TAX"})

    def test_region_group_expansion_creates_multiple_region_candidates(self) -> None:
        sections = self.service.preview_policy_sections(
            source_text="경기 주요 12개 지역은 규제지역입니다.",
            target_rule_type="REGION_POLICY",
            parser_name="mock",
        )
        sections[0]["metadata"]["expanded_regions"] = [
            {
                "region_level": "SIGUNGU",
                "sido": "경기",
                "sigungu": "수원시 영통구",
                "dong": None,
            },
            {
                "region_level": "SIGUNGU",
                "sido": "경기",
                "sigungu": "성남시 분당구",
                "dong": None,
            },
        ]
        sections[0]["metadata"]["requires_region_expansion"] = False

        result = self.service.create_policy_import_from_sections(
            source_text="경기 주요 12개 지역은 규제지역입니다.",
            source_name="지역 그룹 정책",
            target_rule_type="REGION_POLICY",
            effective_date="2026-06-01",
            parser_name="mock",
            selected_sections=sections,
        )

        detail = self.service.get_policy_import_detail(result["policy_import_id"])
        candidates = detail["candidates"]
        self.assertEqual(len(candidates), 2)
        self.assertTrue(all(item["target_rule_type"] == "REGION_POLICY" for item in candidates))
        self.assertEqual(
            {item["proposed_rule"]["sigungu"] for item in candidates},
            {"수원시 영통구", "성남시 분당구"},
        )

    def test_selected_candidates_can_be_approved_independently(self) -> None:
        result = self.service.create_policy_import(
            source_text=(
                "서울 전역은 규제지역입니다. "
                "무주택 실거주자는 9억~15억 구간 LTV 55% DSR 40% 최대 7억 적용."
            ),
            source_name="통합 정책",
            target_rule_type="INTEGRATED",
            effective_date="2026-06-01",
            parser_name="mock",
        )
        detail = self.service.get_policy_import_detail(result["policy_import_id"])
        region_candidate = next(
            item for item in detail["candidates"] if item["target_rule_type"] == "REGION_POLICY"
        )
        loan_candidate = next(
            item for item in detail["candidates"] if item["target_rule_type"] == "LOAN"
        )

        self.service.set_candidate_status(
            candidate_id=int(region_candidate["id"]),
            status=CANDIDATE_STATUS_APPROVED,
        )

        refreshed = self.service.get_policy_import_detail(result["policy_import_id"])
        refreshed_region = next(item for item in refreshed["candidates"] if item["id"] == region_candidate["id"])
        refreshed_loan = next(item for item in refreshed["candidates"] if item["id"] == loan_candidate["id"])

        self.assertEqual(refreshed_region["status"], CANDIDATE_STATUS_APPROVED)
        self.assertNotEqual(refreshed_loan["status"], CANDIDATE_STATUS_APPROVED)

    def test_unknown_candidates_cannot_be_applied(self) -> None:
        result = self.service.create_policy_import(
            source_text="기타 부칙은 추후 고시.",
            source_name="통합 정책",
            target_rule_type="INTEGRATED",
            effective_date="2026-06-01",
            parser_name="mock",
        )
        detail = self.service.get_policy_import_detail(result["policy_import_id"])
        unknown_candidate = next(item for item in detail["candidates"] if item["target_rule_type"] == "UNKNOWN")

        self.service.set_candidate_status(
            candidate_id=int(unknown_candidate["id"]),
            status=CANDIDATE_STATUS_APPROVED,
        )

        with self.assertRaisesRegex(ValueError, "UNKNOWN candidates are review-only"):
            self.service.apply_candidates(candidate_ids=[int(unknown_candidate["id"])])

    def test_non_rule_policy_text_creates_policy_event_candidate(self) -> None:
        result = self.service.create_policy_import(
            source_text="다주택자 양도세 중과 유예는 2026년 5월 9일 종료",
            source_name="Tax guidance",
            target_rule_type="INTEGRATED",
            effective_date="2026-05-31",
            parser_name="mock",
        )

        self.assertEqual(result["candidate_ids"], [])
        self.assertEqual(len(result["policy_event_candidate_ids"]), 1)

        detail = self.service.get_policy_import_detail(
            result["policy_import_id"],
            include_policy_event_candidates=True,
        )
        policy_event_candidate = next(
            item for item in detail["candidates"] if item["target_rule_type"] == "POLICY_EVENT"
        )
        self.assertEqual(policy_event_candidate["proposed_rule"]["policy_type"], "TAX")
        self.assertEqual(policy_event_candidate["proposed_rule"]["impact_level"], "HIGH")
        self.assertEqual(policy_event_candidate["proposed_rule"]["effective_from"], "2026-05-09")
        self.assertEqual(policy_event_candidate["proposed_rule"]["effective_to"], "2026-05-09")
        self.assertFalse(policy_event_candidate["proposed_rule"]["calculation_supported"])

    def test_apply_approved_loan_candidate_updates_active_rules(self) -> None:
        result = self.service.create_policy_import(
            source_text="비규제지역 무주택 실거주자 9억~15억 구간 LTV 55% DSR 40% 최대 7억 적용",
            source_name="샘플 정책",
            target_rule_type="LOAN",
            effective_date="2026-06-01",
            parser_name="mock",
        )
        candidate_id = int(result["candidate_ids"][0])
        self.service.set_candidate_status(
            candidate_id=candidate_id,
            status=CANDIDATE_STATUS_APPROVED,
        )

        preview = self.service.preview_loan_candidate(
            candidate_id=candidate_id,
            sale_price=1_200_000_000,
            region_type="NON_REGULATED",
            buyer_type="NO_HOME",
            investment_purpose="OWNER_OCCUPIED",
        )
        self.assertEqual(preview["old_result"]["final_loan_amount"], 720_000_000)
        self.assertEqual(preview["proposed_result"]["final_loan_amount"], 660_000_000)

        self.service.apply_candidates(candidate_ids=[candidate_id])
        active_rules = self.rule_runtime_service.serialize_active_loan_rules()
        matching_rules = [
            item
            for item in active_rules
            if item["region_type"] == "NON_REGULATED"
            and item["buyer_type"] == "NO_HOME"
            and item["purpose"] == "OWNER_OCCUPIED"
            and item["house_price_min"] == 900_000_000
            and item["effective_from"] == "2026-06-01"
        ]
        self.assertEqual(len(matching_rules), 1)
        self.assertEqual(matching_rules[0]["ltv_rate"], 0.55)

    def test_apply_approved_region_policy_candidate_creates_region_status(self) -> None:
        result = self.service.create_policy_import(
            source_text="서울 전역은 규제지역입니다.",
            source_name="지역 정책",
            target_rule_type="REGION_POLICY",
            effective_date="2026-06-01",
            parser_name="mock",
        )
        candidate_id = int(result["candidate_ids"][0])
        self.service.set_candidate_status(
            candidate_id=candidate_id,
            status=CANDIDATE_STATUS_APPROVED,
        )

        self.service.apply_candidates(candidate_ids=[candidate_id])
        rows = self.region_policy_service.list_region_policy_statuses()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["policy_type"], "REGULATED_AREA")
        self.assertEqual(rows[0]["sido"], "서울")

    def test_region_policy_import_supports_adjustment_target_area(self) -> None:
        result = self.service.create_policy_import(
            source_text="\uc11c\uc6b8 \uc131\ubd81\uad6c\ub294 \uc870\uc815\ub300\uc0c1\uc9c0\uc5ed\uc785\ub2c8\ub2e4.",
            source_name="\uc9c0\uc5ed \uaddc\uc81c",
            target_rule_type="REGION_POLICY",
            effective_date="2026-06-01",
            parser_name="mock",
        )
        candidate_id = int(result["candidate_ids"][0])
        detail = self.service.get_policy_import_detail(result["policy_import_id"])
        candidate = detail["candidates"][0]

        self.assertEqual(candidate["proposed_rule"]["policy_type"], "ADJUSTMENT_TARGET_AREA")
        self.assertEqual(candidate["proposed_rule"]["sido"], "\uc11c\uc6b8")
        self.assertEqual(candidate["proposed_rule"]["sigungu"], "\uc131\ubd81\uad6c")

        self.service.set_candidate_status(
            candidate_id=candidate_id,
            status=CANDIDATE_STATUS_APPROVED,
        )
        self.service.apply_candidates(candidate_ids=[candidate_id])
        rows = self.region_policy_service.list_region_policy_statuses()

        self.assertEqual(rows[0]["policy_type"], "ADJUSTMENT_TARGET_AREA")

    def test_validation_detects_overlapping_loan_rule(self) -> None:
        validation = self.service.validate_rule_candidate(
            target_rule_type="LOAN",
            previous_rule=None,
            proposed_rule={
                "rule_version": "overlap-test",
                "effective_from": "2026-05-01",
                "effective_to": None,
                "region_type": "NON_REGULATED",
                "buyer_type": "NO_HOME",
                "purpose": "OWNER_OCCUPIED",
                "house_price_min": 1_000_000_000,
                "house_price_max": 1_400_000_000,
                "ltv_rate": 0.55,
                "dsr_rate": 0.40,
                "max_loan_amount": 700_000_000,
                "description": "overlap",
            },
        )

        self.assertIn(
            "An overlapping active loan rule already exists for the same condition.",
            validation.errors,
        )


if __name__ == "__main__":
    unittest.main()
