from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from modules.repositories.complex_repository import ApartmentComplexRepository
from modules.repositories.database import initialize_database
from modules.repositories.listing_repository import ManualListingRepository


class ManualListingRepositoryFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)
        self.complex_repository = ApartmentComplexRepository(self.database_path)
        self.listing_repository = ManualListingRepository(self.database_path)
        self.complex_id = self.complex_repository.create(
            name="테스트단지",
            sido="서울",
            sigungu="서초구",
            dong="반포동",
            address="서울 서초구 반포동",
            build_year=2020,
            household_count=None,
            lat=None,
            lng=None,
            memo=None,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_investment_type_defaults_to_owner_occupied_without_jeonse(self) -> None:
        listing_id = self.listing_repository.create(
            complex_id=self.complex_id,
            area_m2=84.9,
            sale_price=900_000_000,
            expected_jeonse_price=0,
            floor="10",
            direction="남향",
            condition_memo="",
            source_memo="",
            checked_at="2026-05-28",
        )

        listing = self.listing_repository.get(listing_id)
        self.assertEqual(listing["effective_investment_type"], "OWNER_OCCUPIED")

    def test_missing_investment_type_defaults_to_gap_investment_with_jeonse(self) -> None:
        listing_id = self.listing_repository.create(
            complex_id=self.complex_id,
            area_m2=84.9,
            sale_price=900_000_000,
            expected_jeonse_price=500_000_000,
            floor="10",
            direction="남향",
            condition_memo="",
            source_memo="",
            checked_at="2026-05-28",
        )

        listing = self.listing_repository.get(listing_id)
        self.assertEqual(listing["effective_investment_type"], "GAP_INVESTMENT")


if __name__ == "__main__":
    unittest.main()
