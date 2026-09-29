from __future__ import annotations

import json
import unittest

from modules.ui.viewmodels.finance_profile import build_finance_profile_view_model


class FinanceProfileViewModelTests(unittest.TestCase):
    def test_empty_profile_has_zero_form_values_and_empty_status(self) -> None:
        view_model = build_finance_profile_view_model(profile=None)

        self.assertEqual(view_model["page_status"], "empty")
        self.assertEqual(view_model["form"]["cash_amount_eok"], 0.0)
        self.assertEqual(view_model["form"]["interest_rate_percent"], 0.0)
        self.assertEqual(view_model["summary"]["total_assets"], 0)
        json.dumps(view_model)

    def test_populated_profile_preserves_zero_and_builds_summary(self) -> None:
        view_model = build_finance_profile_view_model(
            profile={
                "id": 3,
                "cash_amount": 200_000_000,
                "annual_income": None,
                "interest_rate": None,
                "home_count": 0,
                "owned_real_estate_value": 1_000_000_000,
                "owned_real_estate_debt": 300_000_000,
                "credit_loan_balance": 20_000_000,
                "other_loan_balance": 0,
                "use_manual_ltv": 0,
                "manual_ltv_rate": None,
            }
        )

        self.assertEqual(view_model["page_status"], "ready")
        self.assertEqual(view_model["form"]["home_count"], 0)
        self.assertEqual(view_model["summary"]["total_assets"], 1_200_000_000)
        self.assertEqual(view_model["summary"]["total_debt"], 320_000_000)
        self.assertEqual(view_model["summary"]["net_worth"], 880_000_000)

    def test_error_state_exposes_field_errors_without_exception_text(self) -> None:
        view_model = build_finance_profile_view_model(
            profile=None,
            status="validation_error",
            field_errors={"cash_amount_eok": "보유 현금을 입력해 주세요."},
            notice={"level": "error", "code": "validation", "message": "확인 필요"},
        )

        serialized = json.dumps(view_model, ensure_ascii=False)
        self.assertEqual(view_model["page_status"], "validation_error")
        self.assertNotIn("Traceback", serialized)


if __name__ == "__main__":
    unittest.main()
