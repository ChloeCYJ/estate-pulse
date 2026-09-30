from __future__ import annotations

from contextlib import closing
from importlib import import_module
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from modules.repositories.database import initialize_database


class UserAccountRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_user_with_identity_returns_joined_account(self) -> None:
        repository = self._repository()
        account = repository.create_user_with_identity(
            issuer="https://tenant.example.com/",
            subject="google-oauth2|abc",
            provider="google-oauth2",
            email="person@example.com",
            display_name="홍길동",
        )

        self.assertGreater(account["user_id"], 0)
        self.assertGreater(account["identity_id"], 0)
        self.assertEqual(account["issuer"], "https://tenant.example.com/")
        self.assertEqual(account["subject"], "google-oauth2|abc")
        self.assertEqual(account["provider"], "google-oauth2")
        self.assertEqual(account["email"], "person@example.com")
        self.assertEqual(account["display_name"], "홍길동")
        self.assertEqual(account["is_active"], 1)

    def test_create_user_with_identity_is_idempotent_for_same_identity(self) -> None:
        repository = self._repository()
        first = repository.create_user_with_identity(
            issuer="https://tenant.example.com/",
            subject="oauth2|same",
            provider="oauth2",
            email="same@example.com",
            display_name="첫 이름",
        )
        second = repository.create_user_with_identity(
            issuer="https://tenant.example.com/",
            subject="oauth2|same",
            provider="oauth2",
            email="same@example.com",
            display_name="두 번째 이름",
        )

        self.assertEqual(second["user_id"], first["user_id"])
        self.assertEqual(second["identity_id"], first["identity_id"])
        self.assertEqual(self._count_rows("app_user"), 1)
        self.assertEqual(self._count_rows("auth_identity"), 1)

    def test_same_email_with_different_subjects_creates_separate_users(self) -> None:
        repository = self._repository()
        google = repository.create_user_with_identity(
            issuer="https://tenant.example.com/",
            subject="google-oauth2|one",
            provider="google-oauth2",
            email="shared@example.com",
            display_name="공유 이메일",
        )
        naver = repository.create_user_with_identity(
            issuer="https://tenant.example.com/",
            subject="oauth2|two",
            provider="naver",
            email="shared@example.com",
            display_name="공유 이메일",
        )

        self.assertNotEqual(google["user_id"], naver["user_id"])
        self.assertEqual(self._count_rows("app_user"), 2)
        self.assertEqual(self._count_rows("auth_identity"), 2)

    def test_touch_identity_updates_provider_and_last_login(self) -> None:
        repository = self._repository()
        account = repository.create_user_with_identity(
            issuer="https://tenant.example.com/",
            subject="oauth2|kakao-user",
            provider="Social",
            email=None,
            display_name="카카오 회원",
        )

        repository.touch_identity(
            identity_id=int(account["identity_id"]),
            provider="Kakao",
        )
        updated = repository.get_by_identity(
            issuer="https://tenant.example.com/",
            subject="oauth2|kakao-user",
        )

        self.assertEqual(updated["provider"], "Kakao")
        self.assertIsNotNone(updated["last_login_at"])

    def test_unique_identity_race_rolls_back_orphan_user_and_returns_existing(self) -> None:
        repository = self._repository()
        existing = repository.create_user_with_identity(
            issuer="https://tenant.example.com/",
            subject="oauth2|race",
            provider="naver",
            email="race@example.com",
            display_name="기존 사용자",
        )

        with patch.object(repository, "get_by_identity", side_effect=[None, existing]):
            resolved = repository.create_user_with_identity(
                issuer="https://tenant.example.com/",
                subject="oauth2|race",
                provider="naver",
                email="race@example.com",
                display_name="동시 사용자",
            )

        self.assertEqual(resolved["user_id"], existing["user_id"])
        self.assertEqual(self._count_rows("app_user"), 1)
        self.assertEqual(self._count_rows("auth_identity"), 1)

    def _repository(self):
        try:
            repository_class = import_module(
                "modules.repositories.user_account_repository"
            ).UserAccountRepository
        except (ModuleNotFoundError, AttributeError) as exc:
            self.fail(f"UserAccountRepository must exist: {exc}")
        return repository_class(self.database_path)

    def _count_rows(self, table_name: str) -> int:
        self.assertIn(table_name, {"app_user", "auth_identity"})
        with closing(sqlite3.connect(self.database_path)) as connection:
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        assert row is not None
        return int(row[0])


if __name__ == "__main__":
    unittest.main()
