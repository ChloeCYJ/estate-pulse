from __future__ import annotations

from dataclasses import asdict
import json
from unittest.mock import Mock, patch
import unittest

from modules.services.auth_service import AuthenticatedUser
from modules.ui.commercial_auth import (
    CommercialAuthContext,
    build_commercial_auth_view_model,
    clear_commercial_sensitive_state,
    login_commercial_user,
    logout_commercial_user,
    resolve_commercial_auth_context,
)
from modules.ui.search_home_page import SEARCH_HOME_QUERY_KEY


class CommercialAuthTests(unittest.TestCase):
    def test_anonymous_context_does_not_call_auth_service(self) -> None:
        auth_service = Mock()

        context = resolve_commercial_auth_context(
            user_claims={"is_logged_in": False},
            auth_service=auth_service,
        )

        self.assertIsNone(context.user)
        self.assertIsNone(context.error_code)
        auth_service.resolve.assert_not_called()

    def test_authenticated_context_normalizes_only_safe_claims(self) -> None:
        auth_service = Mock()
        auth_service.resolve.return_value = AuthenticatedUser(
            id=7,
            display_name="회원",
            email="member@example.com",
            provider="Kakao",
        )

        context = resolve_commercial_auth_context(
            user_claims={
                "is_logged_in": True,
                "iss": "https://tenant.example/",
                "sub": "kakao|abc",
                "email": "member@example.com",
                "name": "회원",
                "access_token": "must-not-leak",
            },
            auth_service=auth_service,
        )
        view_model = build_commercial_auth_view_model(
            context=context,
            has_finance_profile=True,
        )

        identity = auth_service.resolve.call_args.args[0]
        self.assertEqual(identity.provider, "Kakao")
        serialized = json.dumps(view_model, ensure_ascii=False)
        self.assertNotIn("must-not-leak", serialized)
        self.assertNotIn("kakao|abc", serialized)
        self.assertNotIn("tenant.example", serialized)
        self.assertEqual(view_model["status"], "authenticated")
        self.assertTrue(view_model["finance_profile_exists"])

    def test_malformed_identity_returns_sanitized_error(self) -> None:
        auth_service = Mock()

        context = resolve_commercial_auth_context(
            user_claims={"is_logged_in": True, "iss": "", "sub": ""},
            auth_service=auth_service,
        )
        view_model = build_commercial_auth_view_model(
            context=context,
            has_finance_profile=False,
        )

        self.assertEqual(context.error_code, "invalid_identity")
        self.assertEqual(view_model["status"], "error")
        self.assertEqual(view_model["error"]["code"], "invalid_identity")
        auth_service.resolve.assert_not_called()

    def test_logout_clears_sensitive_commercial_state_but_keeps_query(self) -> None:
        session_state = {
            SEARCH_HOME_QUERY_KEY: "마포 래미안",
            "commercial_page_state": {
                "active_analysis_id": 9,
                "pending_analysis_request": {"complex_id": 1},
                "page_notice": {"code": "secret"},
            },
            "commercial_search_home_results": [{"id": 1}],
            "unrelated": "keep",
        }

        clear_commercial_sensitive_state(session_state)

        self.assertEqual(session_state[SEARCH_HOME_QUERY_KEY], "마포 래미안")
        self.assertEqual(session_state["unrelated"], "keep")
        self.assertNotIn("commercial_page_state", session_state)
        self.assertNotIn("commercial_search_home_results", session_state)

    def test_login_and_logout_delegate_to_streamlit(self) -> None:
        streamlit_mock = Mock()
        streamlit_mock.session_state = {SEARCH_HOME_QUERY_KEY: "검색어", "commercial_x": 1}

        with patch("modules.ui.commercial_auth.st", streamlit_mock):
            login_commercial_user()
            logout_commercial_user()

        streamlit_mock.login.assert_called_once_with("auth0")
        streamlit_mock.logout.assert_called_once_with()
        self.assertEqual(streamlit_mock.session_state, {SEARCH_HOME_QUERY_KEY: "검색어"})


if __name__ == "__main__":
    unittest.main()
