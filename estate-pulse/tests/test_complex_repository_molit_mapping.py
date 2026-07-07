from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.complex_repository import ApartmentComplexRepository
from modules.repositories.database import initialize_database


class ApartmentComplexRepositoryMolitMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)
        self.repository = ApartmentComplexRepository(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_update_persist_molit_mapping_fields(self) -> None:
        complex_id = self.repository.create(
            name="Mapped Complex",
            sido="Seoul",
            sigungu="Seongdong-gu",
            dong="Geumho-dong 4(sa)-ga",
            address="Seoul Seongdong-gu Geumho-dong 4(sa)-ga 100",
            build_year=2020,
            household_count=800,
            lat=None,
            lng=None,
            molit_lawd_cd="11200",
            molit_apt_name="Seoul Forest 1 Prugio",
            molit_umd_name="Geumho-dong 4(sa)-ga",
            memo=None,
        )

        created = self.repository.get(complex_id)
        self.assertIsNotNone(created)
        assert created is not None
        self.assertEqual(created["molit_lawd_cd"], "11200")
        self.assertEqual(created["molit_apt_name"], "Seoul Forest 1 Prugio")
        self.assertEqual(created["molit_umd_name"], "Geumho-dong 4(sa)-ga")

        self.repository.update(
            complex_id,
            name="Mapped Complex",
            sido="Seoul",
            sigungu="Seongdong-gu",
            dong="Geumho-dong 4(sa)-ga",
            address="Seoul Seongdong-gu Geumho-dong 4(sa)-ga 100",
            build_year=2021,
            household_count=900,
            lat=None,
            lng=None,
            molit_lawd_cd="11215",
            molit_apt_name="Seoul Forest Phase 1 Prugio",
            molit_umd_name="Geumho-dong 4(sa)-ga",
            memo="updated",
        )

        updated = self.repository.get(complex_id)
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["molit_lawd_cd"], "11215")
        self.assertEqual(updated["molit_apt_name"], "Seoul Forest Phase 1 Prugio")
        self.assertEqual(updated["molit_umd_name"], "Geumho-dong 4(sa)-ga")
        self.assertEqual(updated["build_year"], 2021)
        self.assertEqual(updated["memo"], "updated")


if __name__ == "__main__":
    unittest.main()
