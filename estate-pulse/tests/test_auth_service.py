from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock
import unittest

from modules.repositories.database import initialize_database
from modules.repositories.user_account_repository import UserAccountRepository
from modules.services.auth_service import (
    AuthService,
    AuthenticationResolutionError,
    VerifiedIdentity,
)


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)
        self.repository = UserAccountRepository(self.database_path)
        self.service = AuthService(self.repository)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_first_login_provisions_and_repeated_login_reuses_account(self) -> None:
        identity = VerifiedIdentity(
            issuer="https://tenant.example/",
            subject="google-oauth2|abc",
            provider="Google",
            email="member@example.com",
            display_name="회원",
        )

        first = self.service.resolve(identity)
        second = self.service.resolve(identity)

        self.assertEqual(first.id, second.id)
        self.assertEqual(second.provider, "Google")
        row = self.repository.get_by_identity(
            issuer=identity.issuer,
            subject=identity.subject,
        )
        self.assertIsNotNone(row["last_login_at"])

    def test_same_email_with_distinct_subjects_does_not_link_accounts(self) -> None:
        first = self.service.resolve(
            VerifiedIdentity(
                issuer="https://tenant.example/",
                subject="google-oauth2|abc",
                provider="Google",
                email="same@example.com",
                display_name="첫 사용자",
            )
        )
        second = self.service.resolve(
            VerifiedIdentity(
                issuer="https://tenant.example/",
                subject="naver|xyz",
                provider="Naver",
                email="same@example.com",
                display_name="둘째 사용자",
            )
        )

        self.assertNotEqual(first.id, second.id)

    def test_repeated_login_promotes_social_provider_without_later_downgrade(self) -> None:
        unresolved = VerifiedIdentity(
            issuer="https://tenant.example/",
            subject="oauth2|kakao-user",
            provider="Social",
            email=None,
            display_name="카카오 회원",
        )
        resolved = VerifiedIdentity(
            issuer=unresolved.issuer,
            subject=unresolved.subject,
            provider="Kakao",
            email=None,
            display_name="카카오 회원",
        )

        first = self.service.resolve(unresolved)
        promoted = self.service.resolve(resolved)
        preserved = self.service.resolve(unresolved)
        row = self.repository.get_by_identity(
            issuer=unresolved.issuer,
            subject=unresolved.subject,
        )

        self.assertEqual(first.provider, "Social")
        self.assertEqual(promoted.provider, "Kakao")
        self.assertEqual(preserved.provider, "Kakao")
        self.assertEqual(row["provider"], "Kakao")

    def test_missing_stable_claim_rejects_before_repository_mutation(self) -> None:
        repository = Mock()
        service = AuthService(repository)

        with self.assertRaises(AuthenticationResolutionError) as caught:
            service.resolve(
                VerifiedIdentity(
                    issuer="",
                    subject="google-oauth2|abc",
                    provider="Google",
                    email=None,
                    display_name=None,
                )
            )

        self.assertEqual(caught.exception.code, "invalid_identity")
        repository.get_by_identity.assert_not_called()
        repository.create_user_with_identity.assert_not_called()


if __name__ == "__main__":
    unittest.main()
