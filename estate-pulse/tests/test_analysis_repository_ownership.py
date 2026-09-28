from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.analysis_repository import AnalysisRepository
from modules.repositories.database import initialize_database
from modules.repositories.user_account_repository import UserAccountRepository


class AnalysisRepositoryOwnershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)
        self.repository = AnalysisRepository(self.database_path)
        self.user_repository = UserAccountRepository(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_recent_and_detail_queries_are_scoped_to_owner(self) -> None:
        first_user_id = self._create_user("first-user", "first@example.com")
        second_user_id = self._create_user("second-user", "second@example.com")

        first_analysis_id = self.repository.create(
            {"user_id": first_user_id, "summary": "first result"}
        )
        second_analysis_id = self.repository.create(
            {"user_id": second_user_id, "summary": "second result"}
        )
        legacy_analysis_id = self.repository.create({"summary": "legacy result"})

        recent = self.repository.list_recent_for_user(user_id=first_user_id)
        self.assertEqual([row["id"] for row in recent], [first_analysis_id])
        self.assertEqual(recent[0]["summary"], "first result")

        owned = self.repository.get_by_id_for_user(
            analysis_id=first_analysis_id,
            user_id=first_user_id,
        )
        self.assertEqual(owned["summary"], "first result")
        self.assertIsNone(
            self.repository.get_by_id_for_user(
                analysis_id=second_analysis_id,
                user_id=first_user_id,
            )
        )
        self.assertIsNone(
            self.repository.get_by_id_for_user(
                analysis_id=legacy_analysis_id,
                user_id=first_user_id,
            )
        )

    def _create_user(self, subject: str, email: str) -> int:
        user = self.user_repository.create_user_with_identity(
            issuer="https://issuer.example/",
            subject=subject,
            provider="test",
            email=email,
            display_name=subject,
        )
        return int(user["user_id"])


if __name__ == "__main__":
    unittest.main()
