from __future__ import annotations

from unittest.mock import Mock
import unittest

from modules.services.auth_service import AuthenticatedUser
from modules.services.finance_profile_service import FinanceProfileValidationError
from modules.ui.commercial_auth import CommercialAuthContext
from modules.ui.commercial_finance_profile_page import handle_finance_profile_saved
from modules.ui.commercial_page_state import (
    CommercialPageState,
    load_commercial_page_state,
    save_commercial_page_state,
)


class CommercialFinanceProfilePageTests(unittest.TestCase):
    def test_anonymous_save_is_rejected_before_service_call(self) -> None:
        service = Mock()
        session_state: dict[str, object] = {}

        state = handle_finance_profile_saved(
            session_state=session_state,
            auth_context=CommercialAuthContext(user=None, error_code=None),
            finance_profile_service=service,
            form_payload={"cash_amount_eok": 2.0},
        )

        self.assertEqual(state.commercial_page, "finance_profile")
        self.assertEqual(state.page_notice["code"], "auth_required")
        service.save_current.assert_not_called()

    def test_authenticated_save_returns_to_search_and_preserves_resume(self) -> None:
        service = Mock()
        service.get_current.return_value = None
        service.save_current.return_value = {"id": 3}
        session_state: dict[str, object] = {}
        save_commercial_page_state(
            session_state,
            CommercialPageState(
                commercial_page="finance_profile",
                pending_analysis_request={
                    "request_kind": "complex_area_analysis",
                    "complex_id": 7,
                    "area_bucket": 84.9,
                    "listing_id": None,
                },
                resume_action="analysis",
            ),
        )
        auth_context = CommercialAuthContext(
            user=AuthenticatedUser(
                id=11,
                display_name="회원",
                email=None,
                provider="Google",
            ),
            error_code=None,
        )
        payload = self._form_payload()

        state = handle_finance_profile_saved(
            session_state=session_state,
            auth_context=auth_context,
            finance_profile_service=service,
            form_payload=payload,
        )

        self.assertEqual(state.commercial_page, "search_home")
        self.assertEqual(state.resume_action, "analysis")
        self.assertEqual(state.pending_analysis_request["complex_id"], 7)
        self.assertEqual(state.page_notice["code"], "finance_profile_saved")
        service.save_current.assert_called_once()
        self.assertEqual(service.save_current.call_args.kwargs["user_id"], 11)

    def test_validation_error_stays_on_profile_page(self) -> None:
        service = Mock()
        service.get_current.return_value = None
        session_state: dict[str, object] = {}
        auth_context = CommercialAuthContext(
            user=AuthenticatedUser(11, "회원", None, "Naver"),
            error_code=None,
        )

        state = handle_finance_profile_saved(
            session_state=session_state,
            auth_context=auth_context,
            finance_profile_service=service,
            form_payload={"cash_amount_eok": 0},
        )

        self.assertEqual(state.commercial_page, "finance_profile")
        self.assertEqual(state.page_notice["code"], "finance_profile_validation")
        service.save_current.assert_not_called()

    @staticmethod
    def _form_payload() -> dict[str, object]:
        return {
            "cash_amount_eok": 2.0,
            "annual_income_eok": 1.0,
            "interest_rate_percent": 4.0,
            "credit_loan_balance_eok": 0.2,
            "other_loan_balance_eok": 0.1,
            "home_count": 1,
            "owned_real_estate_value_eok": 10.0,
            "owned_real_estate_debt_eok": 3.0,
            "use_manual_ltv": False,
            "manual_ltv_rate": None,
        }


if __name__ == "__main__":
    unittest.main()
