from __future__ import annotations

import unittest

from argon2 import PasswordHasher

from scripts.hash_local_admin_password import generate_password_hash


class HashLocalAdminPasswordTests(unittest.TestCase):
    def test_matching_strong_password_generates_verifiable_hash(self) -> None:
        password = "strong-admin-password"
        password_hash = generate_password_hash(password, password)

        self.assertTrue(password_hash.startswith("$argon2"))
        self.assertTrue(PasswordHasher().verify(password_hash, password))

    def test_mismatch_and_short_password_are_rejected(self) -> None:
        cases = [
            (("strong-admin-password", "different-password"), "password_confirmation_mismatch"),
            (("too-short", "too-short"), "password_too_short"),
        ]
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(ValueError, expected):
                    generate_password_hash(*arguments)


if __name__ == "__main__":
    unittest.main()
