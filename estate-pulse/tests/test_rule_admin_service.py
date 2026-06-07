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
                "state",
                "investment_purpose",
                "region_type",
                "buyer_type",
                "house_price_range",
                "ltv_rate",
                "dsr_rate",
                "max_loan_amount",
                "conditions",
                "description",
                "_candidate_id",
                "_editable",
                "_rule_payload",
            },
        )
        self.assertEqual(rows[0]["rule_version"], "2026.05-v2")
        self.assertIn("미만", rows[0]["rule_name"])
        self.assertNotIn("원", rows[0]["rule_name"])

    def test_loan_region_type_options_hide_legacy_generic_regulated_choice(self) -> None:
        options = self.service.list_loan_region_types()

        self.assertEqual(
            options,
            [
                "NON_REGULATED",
                "LAND_TRANSACTION_PERMISSION",
                "SPECULATION_OVERHEATED_DISTRICT",
                "ADJUSTMENT_TARGET_AREA",
            ],
        )
        self.assertNotIn("REGULATED", options)

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

    def test_manual_loan_rule_accepts_all_buyer_type(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="manual-all-buyer-type",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.65,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="전체 공통 룰",
        )

        rows = self.service.list_loan_rules()
        manual_rows = [row for row in rows if row["rule_version"] == "manual-all-buyer-type"]
        self.assertEqual(len(manual_rows), 1)
        self.assertEqual(manual_rows[0]["buyer_type"], "전체")

    def test_loan_rule_versions_include_existing_manual_versions(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="2026.06-비규제-실거주-보완",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.65,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="shared version",
        )

        versions = self.service.list_loan_rule_versions()

        self.assertIn("2026.06-비규제-실거주-보완", versions)
        self.assertIn("2026.05-v2", versions)

    def test_applied_loan_rule_can_be_updated(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="manual-update-target",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.65,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="update before",
        )
        editable_rule = next(
            item
            for item in self.service.list_editable_loan_rules()
            if item["rule_version"] == "manual-update-target"
        )

        self.service.update_applied_loan_rule(
            candidate_id=int(editable_rule["candidate_id"]),
            rule_version="manual-update-target-v2",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.55,
            dsr_rate=0.40,
            max_loan_amount=300_000_000,
            description="update after",
        )

        updated_rule = next(
            item
            for item in self.service.list_editable_loan_rules()
            if item["candidate_id"] == editable_rule["candidate_id"]
        )
        self.assertEqual(updated_rule["rule_version"], "manual-update-target-v2")
        self.assertEqual(updated_rule["description"], "update after")
        self.assertEqual(updated_rule["ltv_rate"], 0.55)
        self.assertEqual(updated_rule["max_loan_amount"], 300_000_000)

    def test_applied_loan_rule_can_be_deleted(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="manual-delete-target",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.65,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="delete target",
        )
        editable_rule = next(
            item
            for item in self.service.list_editable_loan_rules()
            if item["rule_version"] == "manual-delete-target"
        )

        self.service.delete_applied_loan_rule(int(editable_rule["candidate_id"]))

        remaining_versions = {
            item["rule_version"] for item in self.service.list_editable_loan_rules()
        }
        self.assertNotIn("manual-delete-target", remaining_versions)

    def test_applied_loan_rules_can_be_deleted_in_bulk(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="manual-bulk-delete-1",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.65,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="bulk delete 1",
        )
        self.service.create_manual_loan_rule(
            rule_version="manual-bulk-delete-2",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="INVESTMENT",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.55,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="bulk delete 2",
        )
        editable_rules = [
            item
            for item in self.service.list_editable_loan_rules()
            if item["rule_version"] in {"manual-bulk-delete-1", "manual-bulk-delete-2"}
        ]

        deleted_count = self.service.delete_applied_loan_rules(
            [int(item["candidate_id"]) for item in editable_rules]
        )

        self.assertEqual(deleted_count, 2)
        remaining_versions = {
            item["rule_version"] for item in self.service.list_editable_loan_rules()
        }
        self.assertNotIn("manual-bulk-delete-1", remaining_versions)
        self.assertNotIn("manual-bulk-delete-2", remaining_versions)

    def test_builtin_loan_rule_can_be_overridden(self) -> None:
        builtin_rule = next(
            row["_rule_payload"]
            for row in self.service.list_loan_rules()
            if row["_candidate_id"] is None
        )

        self.service.create_loan_rule_override(
            previous_rule=builtin_rule,
            rule_version="manual-override-rule",
            effective_from=builtin_rule["effective_from"],
            effective_to=builtin_rule["effective_to"],
            region_type=builtin_rule["region_type"],
            buyer_type=builtin_rule["buyer_type"],
            purpose=builtin_rule["purpose"],
            house_price_min=builtin_rule["house_price_min"],
            house_price_max=builtin_rule["house_price_max"],
            ltv_rate=0.99,
            dsr_rate=builtin_rule["dsr_rate"],
            max_loan_amount=builtin_rule["max_loan_amount"],
            description="override after builtin",
        )

        rows = self.service.list_loan_rules()
        overridden_row = next(row for row in rows if row["description"] == "override after builtin")
        self.assertTrue(overridden_row["_editable"])
        self.assertIsNotNone(overridden_row["_candidate_id"])

        loan_terms = calculate_loan_terms(
            sale_price=builtin_rule["house_price_min"],
            region_type=builtin_rule["region_type"],
            buyer_type=builtin_rule["buyer_type"],
            purpose=builtin_rule["purpose"],
            reference_date=date.fromisoformat(builtin_rule["effective_from"]),
            rules=self.rule_runtime_service.get_active_loan_rules(),
        )

        self.assertEqual(loan_terms["applied_ltv_rate"], 0.99)
        self.assertEqual(loan_terms["rule_version"], "manual-override-rule")

    def test_loan_rule_can_be_deactivated_and_removed_from_current_list(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="manual-deactivate-target",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.65,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="deactivate target",
        )
        target_row = next(
            row for row in self.service.list_loan_rules(reference_date=date(2026, 6, 6))
            if row["description"] == "deactivate target"
        )

        self.service.deactivate_loan_rule(
            selected_summary=target_row,
            inactive_from="2026-06-06",
        )

        current_rows = self.service.list_loan_rules(reference_date=date(2026, 6, 6), current_only=True)
        all_rows = self.service.list_loan_rules(reference_date=date(2026, 6, 6), current_only=False)
        self.assertFalse(any(row["description"] == "deactivate target" for row in current_rows))
        deactivated_row = next(row for row in all_rows if row["description"] == "deactivate target")
        self.assertEqual(deactivated_row["state"], "비활성/만료")

    def test_loan_rule_display_keeps_only_latest_current_rule_per_band(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="manual-current-overlap",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.65,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="current overlap winner",
        )

        rows = self.service.list_loan_rules(reference_date=date(2026, 6, 5))
        matching_rows = [
            row
            for row in rows
            if row["_rule_payload"]["region_type"] == "NON_REGULATED"
            and row["_rule_payload"]["buyer_type"] == "NO_HOME"
            and row["_rule_payload"]["purpose"] == "OWNER_OCCUPIED"
            and row["_rule_payload"]["house_price_min"] == 0
            and row["_rule_payload"]["house_price_max"] == 899_999_999
        ]

        self.assertEqual(len(matching_rows), 1)
        self.assertEqual(matching_rows[0]["description"], "current overlap winner")
        self.assertTrue(matching_rows[0]["_editable"])

    def test_current_only_filter_hides_future_rule_but_all_view_keeps_it(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="manual-future-rule",
            effective_from="2026-07-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.61,
            dsr_rate=0.40,
            max_loan_amount=500_000_000,
            description="future rule",
        )

        current_rows = self.service.list_loan_rules(reference_date=date(2026, 6, 6), current_only=True)
        all_rows = self.service.list_loan_rules(reference_date=date(2026, 6, 6), current_only=False)

        self.assertFalse(any(row["description"] == "future rule" for row in current_rows))
        self.assertTrue(any(row["description"] == "future rule" for row in all_rows))
        future_row = next(row for row in all_rows if row["description"] == "future rule")
        self.assertEqual(future_row["state"], "예정")

    def test_bulk_update_filters_and_updates_matching_rules(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="bulk-update-v1",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.65,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="bulk update 1",
        )
        self.service.create_manual_loan_rule(
            rule_version="bulk-update-v1",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=900_000_000,
            house_price_max=1_499_999_999,
            ltv_rate=0.60,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="bulk update 2",
        )
        targets = self.service.filter_editable_loan_rules(
            rule_version="bulk-update-v1",
            purpose="OWNER_OCCUPIED",
            region_type="NON_REGULATED",
            buyer_type="ALL",
            current_only=True,
            reference_date=date(2026, 6, 6),
        )

        updated_count = self.service.bulk_update_applied_loan_rules(
            candidate_ids=[int(item["candidate_id"]) for item in targets],
            ltv_rate=0.50,
            description="bulk updated",
        )

        self.assertEqual(updated_count, 2)
        refreshed = self.service.filter_editable_loan_rules(rule_version="bulk-update-v1")
        self.assertTrue(all(item["ltv_rate"] == 0.50 for item in refreshed))
        self.assertTrue(all(item["description"] == "bulk updated" for item in refreshed))

    def test_current_conflicts_are_detected(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="conflict-a",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="INVESTMENT",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.60,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="conflict a",
        )
        self.service.create_manual_loan_rule(
            rule_version="conflict-b",
            effective_from="2026-06-02",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="INVESTMENT",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.55,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="conflict b",
        )

        conflicts = self.service.list_loan_rule_conflicts(reference_date=date(2026, 6, 6))

        self.assertTrue(any(item["buyer_type"] == "전체" and item["count"] >= 2 for item in conflicts))

    def test_loan_rule_display_name_uses_consistent_eok_units(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="manual-open-ended-band",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="INVESTMENT",
            house_price_min=1_500_000_000,
            house_price_max=None,
            ltv_rate=0.50,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="open ended band",
        )

        rows = self.service.list_loan_rules(reference_date=date(2026, 6, 5))
        target_row = next(row for row in rows if row["description"] == "open ended band")

        self.assertIn("15억 이상", target_row["rule_name"])
        self.assertNotIn("원", target_row["rule_name"])

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
        self.assertEqual(rows[0]["loan_region_type"], "공통 규제 규칙")

    def test_wizard_preview_builds_rows_for_each_matrix_entry(self) -> None:
        preview = self.service.preview_manual_loan_rule_batch(
            rule_version="wizard-preview-v1",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            description="wizard preview",
            matrix_rows=[
                {
                    "house_price_min": 0,
                    "house_price_max": 899_999_999,
                    "ltv_rate": 0.60,
                    "dsr_rate": 0.40,
                    "max_loan_amount": None,
                },
                {
                    "house_price_min": 900_000_000,
                    "house_price_max": 1_499_999_999,
                    "ltv_rate": 0.50,
                    "dsr_rate": 0.40,
                    "max_loan_amount": 500_000_000,
                },
            ],
        )

        self.assertEqual(preview["row_count"], 2)
        self.assertEqual({row["rule_version"] for row in preview["rows"]}, {"wizard-preview-v1"})
        self.assertEqual(len(preview["preview_rows"]), 2)

    def test_wizard_rows_can_be_created_with_same_rule_version(self) -> None:
        preview = self.service.preview_manual_loan_rule_batch(
            rule_version="wizard-create-v1",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            description="wizard create",
            matrix_rows=[
                {
                    "house_price_min": 0,
                    "house_price_max": 899_999_999,
                    "ltv_rate": 0.60,
                    "dsr_rate": 0.40,
                    "max_loan_amount": None,
                },
                {
                    "house_price_min": 900_000_000,
                    "house_price_max": 1_499_999_999,
                    "ltv_rate": 0.50,
                    "dsr_rate": 0.40,
                    "max_loan_amount": 500_000_000,
                },
            ],
        )

        created_ids = self.service.create_manual_loan_rule_rows(preview["rows"])

        self.assertEqual(len(created_ids), 2)
        rows = self.service.filter_editable_loan_rules(
            rule_version="wizard-create-v1",
            buyer_type="ALL",
        )
        self.assertEqual(len(rows), 2)

    def test_editable_loan_rule_filters_support_effective_dates(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="date-filter-v1",
            effective_from="2026-06-10",
            effective_to="2026-06-30",
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.65,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="date filter target",
        )

        rows = self.service.filter_editable_loan_rules(
            rule_version="date-filter-v1",
            effective_from="2026-06-10",
            effective_to="2026-06-30",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["description"], "date filter target")

    def test_bulk_update_preview_shows_before_and_after_values(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="bulk-preview-v1",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.65,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="bulk preview",
        )
        target = self.service.filter_editable_loan_rules(rule_version="bulk-preview-v1")[0]

        preview = self.service.preview_bulk_update_applied_loan_rules(
            candidate_ids=[int(target["candidate_id"])],
            ltv_rate=0.55,
            description="bulk preview updated",
        )

        self.assertEqual(preview["row_count"], 1)
        self.assertEqual(preview["rows"][0]["before_ltv_rate"], "65.0%")
        self.assertEqual(preview["rows"][0]["after_ltv_rate"], "55.0%")
        self.assertEqual(preview["rows"][0]["after_description"], "bulk preview updated")

    def test_bulk_deactivate_sets_effective_to_for_selected_rules(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="bulk-deactivate-v1",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.65,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="bulk deactivate 1",
        )
        self.service.create_manual_loan_rule(
            rule_version="bulk-deactivate-v1",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="NON_REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=900_000_000,
            house_price_max=1_499_999_999,
            ltv_rate=0.60,
            dsr_rate=0.40,
            max_loan_amount=None,
            description="bulk deactivate 2",
        )
        targets = self.service.filter_editable_loan_rules(rule_version="bulk-deactivate-v1")

        updated_count = self.service.deactivate_applied_loan_rules(
            candidate_ids=[int(item["candidate_id"]) for item in targets],
            inactive_from="2026-06-06",
        )

        self.assertEqual(updated_count, 2)
        refreshed = self.service.filter_editable_loan_rules(rule_version="bulk-deactivate-v1")
        self.assertTrue(all(item["effective_to"] == "2026-06-05" for item in refreshed))

    def test_query_current_loan_rules_filters_by_condition(self) -> None:
        rows = self.service.query_current_loan_rules(
            purpose="OWNER_OCCUPIED",
            region_type="NON_REGULATED",
            buyer_type="NO_HOME",
            reference_date=date(2026, 6, 7),
        )

        self.assertTrue(rows)
        self.assertTrue(all(row["investment_purpose"] == "실거주" for row in rows))
        self.assertTrue(all(row["region_type"] == "비규제지역" for row in rows))
        self.assertTrue(all(row["buyer_type"] == "무주택" for row in rows))

    def test_query_current_loan_rules_filters_by_house_price_band(self) -> None:
        rows = self.service.query_current_loan_rules(
            purpose="INVESTMENT",
            region_type="NON_REGULATED",
            buyer_type="NO_HOME",
            house_price=1_900_000_000,
            reference_date=date(2026, 6, 7),
        )

        self.assertEqual(len(rows), 1)
        self.assertIn("1,500,000,000원 ~ 2,499,999,999원", rows[0]["house_price_range"])

    def test_query_current_loan_rules_includes_common_fallback_rules(self) -> None:
        self.service.create_manual_loan_rule(
            rule_version="query-fallback-v1",
            effective_from="2026-06-01",
            effective_to=None,
            region_type="REGULATED",
            buyer_type="ALL",
            purpose="OWNER_OCCUPIED",
            house_price_min=0,
            house_price_max=899_999_999,
            ltv_rate=0.45,
            dsr_rate=0.40,
            max_loan_amount=300_000_000,
            description="query fallback",
        )

        rows = self.service.query_current_loan_rules(
            purpose="OWNER_OCCUPIED",
            region_type="LAND_TRANSACTION_PERMISSION",
            buyer_type="ONE_HOME",
            house_price=800_000_000,
            rule_version="query-fallback-v1",
            reference_date=date(2026, 6, 7),
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["region_type"], "공통 규제 규칙")
        self.assertEqual(rows[0]["buyer_type"], "전체")


if __name__ == "__main__":
    unittest.main()
