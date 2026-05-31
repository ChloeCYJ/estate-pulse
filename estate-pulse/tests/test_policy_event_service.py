from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.database import initialize_database
from modules.repositories.policy_event_repository import PolicyEventRepository
from modules.services.policy_event_service import PolicyEventService


class PolicyEventServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)
        self.repository = PolicyEventRepository(self.database_path)
        self.service = PolicyEventService(policy_event_repository=self.repository)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_repository_create_list_update_and_expire(self) -> None:
        event_id = self.repository.create(
            policy_type="TAX",
            title="Capital gains relief sunset",
            summary="Multi-home relief ends soon.",
            detail="Detailed guidance text.",
            effective_from="2026-05-01",
            effective_to=None,
            affected_region_sido=None,
            affected_region_sigungu=None,
            affected_region_dong=None,
            affected_buyer_type="MULTI_HOME",
            affected_investment_purpose="INVESTMENT",
            impact_level="HIGH",
            calculation_supported=False,
            action_required=True,
            source_text="Raw source text",
            source_name="Policy Memo",
            status="ACTIVE",
        )

        created = self.repository.get(event_id)
        self.assertIsNotNone(created)
        self.assertEqual(created["title"], "Capital gains relief sunset")

        rows = self.repository.list_all()
        self.assertEqual(len(rows), 1)

        self.repository.update(
            event_id,
            policy_type="TAX",
            title="Capital gains relief updated",
            summary="Updated summary",
            detail="Updated detail",
            effective_from="2026-05-01",
            effective_to=None,
            affected_region_sido="Seoul",
            affected_region_sigungu="Gangnam",
            affected_region_dong=None,
            affected_buyer_type="MULTI_HOME",
            affected_investment_purpose="INVESTMENT",
            impact_level="HIGH",
            calculation_supported=False,
            action_required=True,
            source_text="Updated raw source text",
            source_name="Policy Memo",
            status="ACTIVE",
        )
        updated = self.repository.get(event_id)
        self.assertEqual(updated["title"], "Capital gains relief updated")
        self.assertEqual(updated["affected_region_sido"], "Seoul")

        self.repository.expire(
            event_id,
            effective_to="2026-05-08",
            status="EXPIRED",
        )
        expired = self.repository.get(event_id)
        self.assertEqual(expired["status"], "EXPIRED")
        self.assertEqual(expired["effective_to"], "2026-05-08")

    def test_status_calculation_supports_active_future_and_expired(self) -> None:
        self.assertEqual(
            self.service.calculate_status(
                effective_from="2026-05-01",
                effective_to=None,
                reference_date=date(2026, 5, 31),
            ),
            "ACTIVE",
        )
        self.assertEqual(
            self.service.calculate_status(
                effective_from="2026-06-10",
                effective_to=None,
                reference_date=date(2026, 5, 31),
            ),
            "FUTURE",
        )
        self.assertEqual(
            self.service.calculate_status(
                effective_from="2026-05-01",
                effective_to="2026-05-09",
                reference_date=date(2026, 5, 31),
            ),
            "EXPIRED",
        )

    def test_matching_by_region(self) -> None:
        self.service.create_policy_event(
            policy_type="REGULATION",
            title="Gangnam contract deadline extended",
            summary="Gangnam contract deadline extended to six months.",
            detail="Detailed guidance",
            effective_from="2026-05-01",
            effective_to=None,
            affected_region_sido="Seoul",
            affected_region_sigungu="Gangnam",
            affected_region_dong=None,
            affected_buyer_type="ANY",
            affected_investment_purpose="ANY",
            impact_level="HIGH",
            calculation_supported=False,
            action_required=True,
            source_text="Source text",
            source_name="Policy Memo",
        )

        matched = self.service.find_relevant_policy_events(
            reference_date=date(2026, 5, 31),
            region_sido="Seoul",
            region_sigungu="Gangnam",
            region_dong="Yeoksam",
            buyer_type="NO_HOME",
            investment_purpose="INVESTMENT",
        )
        unmatched = self.service.find_relevant_policy_events(
            reference_date=date(2026, 5, 31),
            region_sido="Busan",
            region_sigungu="Suyeong",
            region_dong=None,
            buyer_type="NO_HOME",
            investment_purpose="INVESTMENT",
        )

        self.assertEqual(len(matched), 1)
        self.assertEqual(unmatched, [])

    def test_matching_by_buyer_type(self) -> None:
        self.service.create_policy_event(
            policy_type="TAX",
            title="Multi-home tax relief sunset",
            summary="Multi-home seller relief will end.",
            detail="Detailed guidance",
            effective_from="2026-05-01",
            effective_to=None,
            affected_region_sido=None,
            affected_region_sigungu=None,
            affected_region_dong=None,
            affected_buyer_type="MULTI_HOME",
            affected_investment_purpose="INVESTMENT",
            impact_level="HIGH",
            calculation_supported=False,
            action_required=True,
            source_text="Source text",
            source_name="Policy Memo",
        )

        matched = self.service.find_relevant_policy_events(
            reference_date=date(2026, 5, 31),
            region_sido=None,
            region_sigungu=None,
            region_dong=None,
            buyer_type="MULTI_HOME",
            investment_purpose="INVESTMENT",
        )
        unmatched = self.service.find_relevant_policy_events(
            reference_date=date(2026, 5, 31),
            region_sido=None,
            region_sigungu=None,
            region_dong=None,
            buyer_type="NO_HOME",
            investment_purpose="INVESTMENT",
        )

        self.assertEqual(len(matched), 1)
        self.assertEqual(unmatched, [])

    def test_matching_by_investment_purpose(self) -> None:
        self.service.create_policy_event(
            policy_type="PERMISSION",
            title="Owner occupied occupancy grace period",
            summary="Grace period for occupancy requirement.",
            detail="Detailed guidance",
            effective_from="2026-05-01",
            effective_to=None,
            affected_region_sido=None,
            affected_region_sigungu=None,
            affected_region_dong=None,
            affected_buyer_type="ANY",
            affected_investment_purpose="OWNER_OCCUPIED",
            impact_level="MEDIUM",
            calculation_supported=False,
            action_required=False,
            source_text="Source text",
            source_name="Policy Memo",
        )

        matched = self.service.find_relevant_policy_events(
            reference_date=date(2026, 5, 31),
            region_sido=None,
            region_sigungu=None,
            region_dong=None,
            buyer_type="NO_HOME",
            investment_purpose="OWNER_OCCUPIED",
        )
        unmatched = self.service.find_relevant_policy_events(
            reference_date=date(2026, 5, 31),
            region_sido=None,
            region_sigungu=None,
            region_dong=None,
            buyer_type="NO_HOME",
            investment_purpose="INVESTMENT",
        )

        self.assertEqual(len(matched), 1)
        self.assertEqual(unmatched, [])


if __name__ == "__main__":
    unittest.main()
