from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.database import initialize_database
from modules.repositories.region_policy_repository import RegionPolicyRepository
from modules.services.region_policy_service import RegionPolicyService


class RegionPolicyServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)
        self.repository = RegionPolicyRepository(self.database_path)
        self.service = RegionPolicyService(region_policy_repository=self.repository)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_resolve_region_context_uses_most_specific_loan_policy(self) -> None:
        self.service.create_region_policy_status(
            region_level="SIDO",
            sido="서울",
            sigungu=None,
            dong=None,
            policy_type="NON_REGULATED_AREA",
            effective_from="2026-01-01",
            effective_to=None,
            notes=None,
        )
        self.service.create_region_policy_status(
            region_level="SIGUNGU",
            sido="서울",
            sigungu="강남구",
            dong=None,
            policy_type="REGULATED_AREA",
            effective_from="2026-05-01",
            effective_to=None,
            notes=None,
        )
        self.service.create_region_policy_status(
            region_level="DONG",
            sido="서울",
            sigungu="강남구",
            dong="삼성동",
            policy_type="LAND_TRANSACTION_PERMISSION",
            effective_from="2026-05-01",
            effective_to=None,
            notes=None,
        )

        result = self.service.resolve_region_context(
            sido="서울",
            sigungu="강남구",
            dong="삼성동",
            reference_date=date(2026, 5, 30),
        )

        self.assertEqual(result["region_type"], "REGULATED")
        self.assertEqual(result["source"], "region_policy_status")
        self.assertEqual(result["matched_loan_policy"]["policy_type"], "REGULATED_AREA")
        self.assertEqual(len(result["active_policies"]), 3)

    def test_list_policy_types_excludes_legacy_generic_regulated_area(self) -> None:
        self.assertEqual(
            self.service.list_policy_types(),
            [
                "NON_REGULATED_AREA",
                "LAND_TRANSACTION_PERMISSION",
                "SPECULATION_OVERHEATED_DISTRICT",
                "ADJUSTMENT_TARGET_AREA",
            ],
        )
        self.assertNotIn("REGULATED_AREA", self.service.list_policy_types())

    def test_conflicting_region_policies_are_rejected(self) -> None:
        self.service.create_region_policy_status(
            region_level="SIGUNGU",
            sido="서울",
            sigungu="강동구",
            dong=None,
            policy_type="REGULATED_AREA",
            effective_from="2026-05-01",
            effective_to=None,
            notes=None,
        )

        with self.assertRaisesRegex(
            ValueError,
            "non-regulated status cannot overlap",
        ):
            self.service.create_region_policy_status(
                region_level="SIGUNGU",
                sido="서울",
                sigungu="강동구",
                dong=None,
                policy_type="NON_REGULATED_AREA",
                effective_from="2026-06-01",
                effective_to=None,
                notes=None,
            )

    def test_create_region_policy_infers_sigungu_level_when_sigungu_is_entered(self) -> None:
        self.service.create_region_policy_status(
            region_level="SIDO",
            sido="\uc11c\uc6b8",
            sigungu="\uc131\ubd81\uad6c",
            dong=None,
            policy_type="LAND_TRANSACTION_PERMISSION",
            effective_from="2026-05-01",
            effective_to=None,
            notes=None,
        )

        rows = self.service.list_region_policy_statuses()

        self.assertEqual(rows[0]["region_level"], "SIGUNGU")
        self.assertEqual(rows[0]["region_scope"], "\uc11c\uc6b8 \uc131\ubd81\uad6c")
        self.assertEqual(rows[0]["sigungu"], "\uc131\ubd81\uad6c")

    def test_multiple_region_regulations_can_overlap_for_same_scope(self) -> None:
        for policy_type in (
            "LAND_TRANSACTION_PERMISSION",
            "SPECULATION_OVERHEATED_DISTRICT",
            "ADJUSTMENT_TARGET_AREA",
        ):
            self.service.create_region_policy_status(
                region_level="SIGUNGU",
                sido="\uc11c\uc6b8",
                sigungu="\uc131\ubd81\uad6c",
                dong=None,
                policy_type=policy_type,
                effective_from="2026-05-01",
                effective_to=None,
                notes=None,
            )

        result = self.service.resolve_region_context(
            sido="\uc11c\uc6b8",
            sigungu="\uc131\ubd81\uad6c",
            dong=None,
            reference_date=date(2026, 5, 30),
        )

        policy_types = {item["policy_type"] for item in result["active_policies"]}
        self.assertEqual(result["region_type"], "REGULATED")
        self.assertEqual(
            policy_types,
            {
                "LAND_TRANSACTION_PERMISSION",
                "SPECULATION_OVERHEATED_DISTRICT",
                "ADJUSTMENT_TARGET_AREA",
            },
        )

    def test_non_regulated_status_cannot_overlap_regulated_status(self) -> None:
        self.service.create_region_policy_status(
            region_level="SIGUNGU",
            sido="\uc11c\uc6b8",
            sigungu="\uc131\ubd81\uad6c",
            dong=None,
            policy_type="ADJUSTMENT_TARGET_AREA",
            effective_from="2026-05-01",
            effective_to=None,
            notes=None,
        )

        with self.assertRaisesRegex(ValueError, "non-regulated status cannot overlap"):
            self.service.create_region_policy_status(
                region_level="SIGUNGU",
                sido="\uc11c\uc6b8",
                sigungu="\uc131\ubd81\uad6c",
                dong=None,
                policy_type="NON_REGULATED_AREA",
                effective_from="2026-05-01",
                effective_to=None,
                notes=None,
            )


if __name__ == "__main__":
    unittest.main()
