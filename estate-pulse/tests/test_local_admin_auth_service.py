from __future__ import annotations

import unittest

from argon2 import PasswordHasher

from modules.services.local_admin_auth_service import (
    LocalAdminAuthenticationError,
    LocalAdminAuthService,
    LocalAdminConfig,
)


class LocalAdminAuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.password = "strong-admin-password"
        self.password_hash = PasswordHasher(
            time_cost=1,
            memory_cost=1024,
            parallelism=1,
        ).hash(self.password)

    def service(self, **overrides: object) -> LocalAdminAuthService:
        values = {
            "enabled": True,
            "username": "operator",
            "password_hash": self.password_hash,
        }
        values.update(overrides)
        return LocalAdminAuthService(LocalAdminConfig(**values))

    def test_correct_credentials_return_fixed_admin_principal(self) -> None:
        with self.assertLogs(
            "modules.services.local_admin_auth_service", level="INFO"
        ) as captured:
            principal = self.service().authenticate(
                username="operator",
                password=self.password,
            )

        self.assertEqual(principal.username, "operator")
        self.assertEqual(principal.role, "admin")
        log_text = " ".join(captured.output)
        self.assertNotIn(self.password, log_text)
        self.assertNotIn(self.password_hash, log_text)

    def test_wrong_username_or_password_uses_generic_error(self) -> None:
        attempts = [
            ("wrong", self.password),
            ("operator", "wrong-password"),
        ]
        for username, password in attempts:
            with self.subTest(username=username, password=password):
                with self.assertRaises(LocalAdminAuthenticationError) as raised:
                    self.service().authenticate(username=username, password=password)
                self.assertEqual(raised.exception.code, "invalid_credentials")

    def test_disabled_and_unconfigured_accounts_fail_closed(self) -> None:
        cases = [
            ({"enabled": False}, "admin_disabled"),
            ({"username": None}, "admin_not_configured"),
            ({"username": "REPLACE_WITH_ADMIN_USERNAME"}, "admin_not_configured"),
            ({"password_hash": "not-an-argon2-hash"}, "admin_not_configured"),
        ]
        for overrides, expected_code in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(LocalAdminAuthenticationError) as raised:
                    self.service(**overrides).authenticate(
                        username="operator",
                        password=self.password,
                    )
                self.assertEqual(raised.exception.code, expected_code)


if __name__ == "__main__":
    unittest.main()
