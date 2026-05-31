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
            "An overlapping region loan policy already exists for the same scope.",
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


if __name__ == "__main__":
    unittest.main()
