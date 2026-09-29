from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.database import initialize_database
from modules.repositories.finance_profile_repository import UserFinanceProfileRepository
from modules.repositories.user_account_repository import UserAccountRepository
from modules.services.finance_profile_service import (
    FinanceProfileService,
    FinanceProfileValidationError,
    build_finance_profile_payload,
)


class FinanceProfileServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)
        self.repository = UserFinanceProfileRepository(self.database_path)
        self.user_repository = UserAccountRepository(self.database_path)
        self.service = FinanceProfileService(self.repository)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_payload_converts_units_and_derives_total_debt(self) -> None:
        payload = build_finance_profile_payload(
            cash_amount_eok=2.0,
            annual_income_eok=1.2,
            interest_rate_percent=4.0,
            credit_loan_balance_eok=0.7,
            other_loan_balance_eok=0.3,
            home_count=1,
            owned_real_estate_value_eok=14.0,
            owned_real_estate_debt_eok=4.0,
            use_manual_ltv=True,
            manual_ltv_rate=0.5,
            existing_profile={"ltv_limit": 0.4, "dsr_limit": 0.35},
        )

        self.assertEqual(payload["cash_amount"], 200_000_000)
        self.assertEqual(payload["annual_income"], 120_000_000)
        self.assertEqual(payload["existing_debt"], 500_000_000)
        self.assertEqual(payload["interest_rate"], 0.04)
        self.assertEqual(payload["ltv_limit"], 0.4)
        self.assertEqual(payload["dsr_limit"], 0.35)

    def test_payload_rejects_invalid_cash_ambiguous_rate_and_manual_ltv(self) -> None:
        with self.assertRaises(FinanceProfileValidationError) as caught:
            build_finance_profile_payload(
                cash_amount_eok=0,
                annual_income_eok=0,
                interest_rate_percent=0.4,
                credit_loan_balance_eok=0,
                other_loan_balance_eok=0,
                home_count=0,
                owned_real_estate_value_eok=0,
                owned_real_estate_debt_eok=0,
                use_manual_ltv=True,
                manual_ltv_rate=1.2,
            )

        self.assertEqual(
            set(caught.exception.field_errors),
            {"cash_amount_eok", "interest_rate_percent", "manual_ltv_rate"},
        )

    def test_save_current_creates_then_updates_same_owned_row(self) -> None:
        first_user_id = self._create_user("first")
        second_user_id = self._create_user("second")
        second = self.service.save_current(
            user_id=second_user_id,
            payload=self._payload(5.0),
        )

        created = self.service.save_current(
            user_id=first_user_id,
            payload=self._payload(2.0),
        )
        updated = self.service.save_current(
            user_id=first_user_id,
            payload=self._payload(3.0),
        )

        self.assertEqual(created["id"], updated["id"])
        self.assertEqual(updated["cash_amount"], 300_000_000)
        self.assertEqual(
            self.service.get_current(second_user_id)["id"],
            second["id"],
        )
        self.assertEqual(
            self.service.get_current(second_user_id)["cash_amount"],
            500_000_000,
        )

    def _create_user(self, subject: str) -> int:
        account = self.user_repository.create_user_with_identity(
            issuer="https://issuer.example/",
            subject=subject,
            provider="test",
            email=f"{subject}@example.com",
            display_name=subject,
        )
        return int(account["user_id"])

    @staticmethod
    def _payload(cash_amount_eok: float) -> dict[str, object]:
        return build_finance_profile_payload(
            cash_amount_eok=cash_amount_eok,
            annual_income_eok=1.0,
            interest_rate_percent=4.0,
            credit_loan_balance_eok=0.2,
            other_loan_balance_eok=0.1,
            home_count=1,
            owned_real_estate_value_eok=10.0,
            owned_real_estate_debt_eok=3.0,
            use_manual_ltv=False,
            manual_ltv_rate=None,
        )


if __name__ == "__main__":
    unittest.main()
