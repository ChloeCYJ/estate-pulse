from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.analyzers.loan_analyzer import calculate_loan_terms
from modules.repositories.database import initialize_database
from modules.repositories.policy_import_repository import PolicyImportRepository
from modules.repositories.region_policy_repository import RegionPolicyRepository
from modules.repositories.rule_candidate_repository import RuleCandidateRepository
from modules.services.region_policy_service import RegionPolicyService
from modules.services.rule_admin_service import RuleAdminService
from modules.services.rule_runtime_service import RuleRuntimeService


class RuleAdminServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)
        self.policy_import_repository = PolicyImportRepository(self.database_path)
        self.rule_candidate_repository = RuleCandidateRepository(self.database_path)
        self.rule_runtime_service = RuleRuntimeService(
            rule_candidate_repository=self.rule_candidate_repository,
        )
        self.region_policy_repository = RegionPolicyRepository(self.database_path)
        self.region_policy_service = RegionPolicyService(
            region_policy_repository=self.region_policy_repository,
        )
        self.service = RuleAdminService(
            rule_runtime_service=self.rule_runtime_service,
            region_policy_service=self.region_policy_service,
            policy_import_repository=self.policy_import_repository,
            rule_candidate_repository=self.rule_candidate_repository,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_loan_rules_are_normalized_for_display(self) -> None:
        rows = self.service.list_loan_rules()

        self.assertGreater(len(rows), 0)
        self.assertEqual(
            set(rows[0].keys()),
            {
                "rule_version",
                "rule_name",
                "effective_from",
                "effective_to",
                "investment_purpose",
                "region_type",
                "buyer_type",
                "house_price_range",
                "ltv_rate",
                "dsr_rate",
                "max_loan_amount",
                "conditions",
                "description",
            },
        )
        self.assertEqual(rows[0]["rule_version"], "2026.05-v2")

    def test_manual_loan_rule_registration_is_applied_to_runtime_rules(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="LAND_TRANSACTION_PERMISSION",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            house_price_min=2_000_000_000,
            house_price_max=None,
            ltv_rate=0.60,
            dsr_rate=0.40,
            max_loan_amount=200_000_000,
            description="20억 이상 2억 대출 제한",
        )

        rows = self.service.list_loan_rules()
        manual_rows = [row for row in rows if row["description"] == "20억 이상 2억 대출 제한"]
        self.assertEqual(len(manual_rows), 1)
        self.assertTrue(manual_rows[0]["rule_version"].startswith("manual-loan-"))
        self.assertEqual(manual_rows[0]["region_type"], "토지거래허가구역")

        loan_terms = calculate_loan_terms(
            sale_price=2_100_000_000,
            region_type="LAND_TRANSACTION_PERMISSION",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            reference_date=date(2026, 6, 3),
            rules=self.rule_runtime_service.get_active_loan_rules(),
        )

        self.assertTrue(loan_terms["rule_version"].startswith("manual-loan-"))
        self.assertEqual(loan_terms["max_loan_amount"], 200_000_000)
        self.assertEqual(loan_terms["final_loan_amount"], 200_000_000)

    def test_manual_loan_rule_supports_price_upper_bound(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="manual-15-to-under-20b",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="REGULATED",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            house_price_min=1_500_000_000,
            house_price_max=1_999_999_999,
            ltv_rate=0.60,
            dsr_rate=0.40,
            max_loan_amount=400_000_000,
            description="15억 이상 20억 미만 4억 대출 제한",
        )

        loan_terms = calculate_loan_terms(
            sale_price=1_800_000_000,
            region_type="REGULATED",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            reference_date=date(2026, 6, 3),
            rules=self.rule_runtime_service.get_active_loan_rules(),
        )

        self.assertEqual(loan_terms["rule_version"], "manual-15-to-under-20b")
        self.assertEqual(loan_terms["max_loan_amount"], 400_000_000)
        self.assertEqual(loan_terms["final_loan_amount"], 400_000_000)

    def test_tax_rules_expand_brackets_for_display(self) -> None:
        rows = self.service.list_tax_rules()

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["rule_version"], "2026.05-estimate")
        self.assertIn("취득세", rows[0]["rate_values"])

    def test_brokerage_rules_expand_brackets_for_display(self) -> None:
        rows = self.service.list_brokerage_rules()

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["rule_version"], "2026.05-estimate")
        self.assertIn("중개보수", rows[0]["rate_values"])

    def test_region_policy_statuses_are_normalized_for_display(self) -> None:
        self.region_policy_service.create_region_policy_status(
            region_level="SIGUNGU",
            sido="서울",
            sigungu="강남구",
            dong=None,
            policy_type="REGULATED_AREA",
            effective_from="2026-05-01",
            effective_to=None,
            notes="test",
        )

        rows = self.service.list_region_policy_statuses()

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            set(rows[0].keys()),
            {
                "id",
                "region_scope",
                "region_level",
                "sido",
                "sigungu",
                "dong",
                "policy_type",
                "loan_region_type",
                "effective_from",
                "effective_to",
                "notes",
            },
        )
        self.assertEqual(rows[0]["policy_type"], "규제지역(기존 상위개념)")
        self.assertEqual(rows[0]["loan_region_type"], "규제지역")


if __name__ == "__main__":
    unittest.main()
