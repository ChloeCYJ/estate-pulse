import unittest

from modules.ui.finance_profile_form import (
    _build_profile_payload,
    _interest_rate_input_value,
    _interest_rate_input_warning,
)


class FinanceProfileFormTests(unittest.TestCase):
    def test_build_profile_payload_uses_detail_loan_sum_for_existing_debt(self) -> None:
        payload = _build_profile_payload(
            cash_amount_eok=2.0,
            annual_income_eok=1.2,
            interest_rate=4.0,
            credit_loan_balance_eok=0.7,
            other_loan_balance_eok=0.3,
            home_count=1,
            owned_real_estate_value_eok=14.0,
            owned_real_estate_debt_eok=4.0,
            use_manual_ltv=False,
            manual_ltv_rate=None,
            selected={"existing_debt": 9_999_999_999},
        )

        self.assertEqual(payload["existing_debt"], 500_000_000)
        self.assertEqual(payload["annual_income"], 120_000_000)
        self.assertEqual(payload["interest_rate"], 0.04)
        self.assertEqual(payload["owned_real_estate_debt"], 400_000_000)
        self.assertEqual(payload["credit_loan_balance"], 70_000_000)
        self.assertEqual(payload["other_loan_balance"], 30_000_000)

    def test_interest_rate_display_value_converts_stored_ratio_to_percent(self) -> None:
        self.assertEqual(_interest_rate_input_value(0.04), 4.0)
        self.assertEqual(_interest_rate_input_value(4.0), 4.0)
        self.assertEqual(_interest_rate_input_value(None), 0.0)

    def test_interest_rate_warning_marks_ambiguous_percent_range(self) -> None:
        self.assertIsNotNone(_interest_rate_input_warning(0.40))
        self.assertIsNone(_interest_rate_input_warning(4.0))


if __name__ == "__main__":
    unittest.main()
