from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.complex_repository import ApartmentComplexRepository
from modules.repositories.database import initialize_database
from modules.repositories.listing_repository import ManualListingRepository
from modules.repositories.watchlist_repository import WatchlistRepository


class WatchlistRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)

        self.complex_repository = ApartmentComplexRepository(self.database_path)
        self.listing_repository = ManualListingRepository(self.database_path)
        self.watchlist_repository = WatchlistRepository(self.database_path)

        self.complex_id = self.complex_repository.create(
            name="River Park",
            sido="Seoul",
            sigungu="Seocho",
            dong="Banpo",
            address="Banpo",
            build_year=2018,
            household_count=800,
            lat=None,
            lng=None,
            memo=None,
        )
        self.listing_id = self.listing_repository.create(
            complex_id=self.complex_id,
            area_m2=84.0,
            sale_price=950_000_000,
            expected_jeonse_price=500_000_000,
            floor="10",
            direction="S",
            condition_memo="",
            source_memo="",
            checked_at="2026-05-30",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_add_list_and_delete_watchlist_targets(self) -> None:
        self.watchlist_repository.add_complex(self.complex_id)
        self.watchlist_repository.add_listing(self.listing_id)
        self.watchlist_repository.add_listing(self.listing_id)

        rows = self.watchlist_repository.list_all()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["complex_name"], "River Park")

        listing_row = next(row for row in rows if row["listing_id"] == self.listing_id)
        self.watchlist_repository.delete(int(listing_row["id"]))
        remaining_rows = self.watchlist_repository.list_all()
        self.assertEqual(len(remaining_rows), 1)
        self.assertEqual(remaining_rows[0]["complex_id"], self.complex_id)


if __name__ == "__main__":
    unittest.main()
