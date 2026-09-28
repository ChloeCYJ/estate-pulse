from __future__ import annotations

from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.database import initialize_database
from modules.repositories.finance_profile_repository import UserFinanceProfileRepository
from modules.repositories.user_account_repository import UserAccountRepository


class UserFinanceProfileRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)
        self.repository = UserFinanceProfileRepository(self.database_path)
        self.user_repository = UserAccountRepository(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_update_extended_finance_profile_fields(self) -> None:
        profile_id = self.repository.create(
            cash_amount=300_000_000,
            annual_income=120_000_000,
            existing_debt=120_000_000,
            interest_rate=0.04,
            ltv_limit=None,
            dsr_limit=None,
            home_count=2,
            owned_real_estate_value=900_000_000,
            owned_real_estate_debt=400_000_000,
            credit_loan_balance=50_000_000,
            other_loan_balance=30_000_000,
            use_manual_ltv=True,
            manual_ltv_rate=0.45,
        )

        profile = self.repository.get(profile_id)

        self.assertEqual(profile["home_count"], 2)
        self.assertEqual(profile["annual_income"], 120_000_000)
        self.assertEqual(profile["interest_rate"], 0.04)
        self.assertEqual(profile["owned_real_estate_value"], 900_000_000)
        self.assertEqual(profile["owned_real_estate_debt"], 400_000_000)
        self.assertEqual(profile["credit_loan_balance"], 50_000_000)
        self.assertEqual(profile["other_loan_balance"], 30_000_000)
        self.assertEqual(profile["use_manual_ltv"], 1)
        self.assertEqual(profile["manual_ltv_rate"], 0.45)

        self.repository.update(
            profile_id,
            cash_amount=350_000_000,
            annual_income=80_000_000,
            existing_debt=100_000_000,
            interest_rate=0.035,
            ltv_limit=None,
            dsr_limit=None,
            home_count=1,
            owned_real_estate_value=700_000_000,
            owned_real_estate_debt=250_000_000,
            credit_loan_balance=20_000_000,
            other_loan_balance=10_000_000,
            use_manual_ltv=False,
            manual_ltv_rate=None,
        )
        updated = self.repository.get(profile_id)

        self.assertEqual(updated["cash_amount"], 350_000_000)
        self.assertEqual(updated["annual_income"], 80_000_000)
        self.assertEqual(updated["interest_rate"], 0.035)
        self.assertEqual(updated["home_count"], 1)
        self.assertEqual(updated["use_manual_ltv"], 0)
        self.assertIsNone(updated["manual_ltv_rate"])

    def test_profiles_are_created_updated_and_read_by_owner(self) -> None:
        first_user_id = self._create_user("first-user", "first@example.com")
        second_user_id = self._create_user("second-user", "second@example.com")

        first_profile_id = self.repository.create_for_user(
            user_id=first_user_id,
            payload=self._profile_payload(cash_amount=300_000_000),
        )
        second_profile_id = self.repository.create_for_user(
            user_id=second_user_id,
            payload=self._profile_payload(cash_amount=500_000_000),
        )

        first_profile = self.repository.get_for_user(first_user_id)
        second_profile = self.repository.get_for_user(second_user_id)
        self.assertEqual(first_profile["id"], first_profile_id)
        self.assertEqual(first_profile["cash_amount"], 300_000_000)
        self.assertEqual(second_profile["id"], second_profile_id)
        self.assertEqual(second_profile["cash_amount"], 500_000_000)

        with self.assertRaises(sqlite3.IntegrityError):
            self.repository.create_for_user(
                user_id=first_user_id,
                payload=self._profile_payload(cash_amount=900_000_000),
            )

        self.assertTrue(
            self.repository.update_for_user(
                user_id=first_user_id,
                payload=self._profile_payload(cash_amount=350_000_000),
            )
        )
        updated = self.repository.get_for_user(first_user_id)
        self.assertEqual(updated["id"], first_profile_id)
        self.assertEqual(updated["cash_amount"], 350_000_000)
        self.assertEqual(
            self.repository.get_for_user(second_user_id)["cash_amount"],
            500_000_000,
        )
        self.assertFalse(
            self.repository.update_for_user(
                user_id=999_999,
                payload=self._profile_payload(cash_amount=100_000_000),
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

    @staticmethod
    def _profile_payload(*, cash_amount: int) -> dict[str, object]:
        return {
            "cash_amount": cash_amount,
            "annual_income": 120_000_000,
            "existing_debt": 20_000_000,
            "interest_rate": 0.04,
            "ltv_limit": None,
            "dsr_limit": None,
            "home_count": 1,
            "owned_real_estate_value": 700_000_000,
            "owned_real_estate_debt": 250_000_000,
            "credit_loan_balance": 20_000_000,
            "other_loan_balance": 10_000_000,
            "use_manual_ltv": False,
            "manual_ltv_rate": None,
        }


if __name__ == "__main__":
    unittest.main()
