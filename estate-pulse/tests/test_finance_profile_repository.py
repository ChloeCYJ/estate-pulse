from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.database import initialize_database
from modules.repositories.finance_profile_repository import UserFinanceProfileRepository


class UserFinanceProfileRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)
        self.repository = UserFinanceProfileRepository(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_update_extended_finance_profile_fields(self) -> None:
        profile_id = self.repository.create(
            cash_amount=300_000_000,
            annual_income=None,
            existing_debt=120_000_000,
            interest_rate=None,
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
        self.assertEqual(profile["owned_real_estate_value"], 900_000_000)
        self.assertEqual(profile["owned_real_estate_debt"], 400_000_000)
        self.assertEqual(profile["credit_loan_balance"], 50_000_000)
        self.assertEqual(profile["other_loan_balance"], 30_000_000)
        self.assertEqual(profile["use_manual_ltv"], 1)
        self.assertEqual(profile["manual_ltv_rate"], 0.45)

        self.repository.update(
            profile_id,
            cash_amount=350_000_000,
            annual_income=None,
            existing_debt=100_000_000,
            interest_rate=None,
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
        self.assertEqual(updated["home_count"], 1)
        self.assertEqual(updated["use_manual_ltv"], 0)
        self.assertIsNone(updated["manual_ltv_rate"])


if __name__ == "__main__":
    unittest.main()
