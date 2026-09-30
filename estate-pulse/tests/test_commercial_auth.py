from __future__ import annotations

from dataclasses import asdict
import json
from unittest.mock import Mock, patch
import unittest

from modules.services.auth_service import AuthenticatedUser
from modules.ui.commercial_auth import (
    AUTH_CONNECTION_CLAIM,
    AUTH_ERROR_SESSION_KEY,
    CommercialAuthContext,
    apply_commercial_auth_session_error,
    build_commercial_auth_view_model,
    clear_commercial_sensitive_state,
    login_commercial_user,
    logout_commercial_user,
    resolve_commercial_auth_context,
    validate_commercial_auth_configuration,
)
from modules.ui.search_home_page import SEARCH_HOME_QUERY_KEY


class CommercialAuthTests(unittest.TestCase):
    @staticmethod
    def _valid_secrets() -> dict[str, object]:
        return {
            "auth": {
                "redirect_uri": "http://localhost:8501/oauth2callback",
                "cookie_secret": "random-cookie-secret-at-least-32-chars",
                "auth0": {
                    "client_id": "client-id",
                    "client_secret": "client-secret",
                    "server_metadata_url": (
                        "https://tenant.example/.well-known/openid-configuration"
                    ),
                },
            }
        }

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

    def test_provider_label_accepts_auth0_social_connection_variants(self) -> None:
        for subject, connection_name, expected_provider in (
            ("google-oauth2|google-user", None, "Google"),
            ("oauth2|kakao-user", "kakao", "Kakao"),
            ("oauth2|naver-user", "naver-oauth2", "Naver"),
            ("custom-oauth2|social-user", None, "Social"),
        ):
            with self.subTest(subject=subject):
                auth_service = Mock()
                auth_service.resolve.return_value = AuthenticatedUser(
                    id=7,
                    display_name="회원",
                    email=None,
                    provider=expected_provider,
                )

                resolve_commercial_auth_context(
                    user_claims={
                        "is_logged_in": True,
                        "iss": "https://tenant.example/",
                        "sub": subject,
                        AUTH_CONNECTION_CLAIM: connection_name,
                    },
                    auth_service=auth_service,
                )

                identity = auth_service.resolve.call_args.args[0]
                self.assertEqual(identity.provider, expected_provider)

    def test_configuration_validation_rejects_placeholders_and_invalid_urls(self) -> None:
        placeholder_secrets = self._valid_secrets()
        placeholder_secrets["auth"]["auth0"]["client_id"] = (  # type: ignore[index]
            "REPLACE_WITH_AUTH0_CLIENT_ID"
        )
        invalid_redirect_secrets = self._valid_secrets()
        invalid_redirect_secrets["auth"]["redirect_uri"] = (  # type: ignore[index]
            "http://production.example/oauth2callback"
        )

        self.assertEqual(
            validate_commercial_auth_configuration(placeholder_secrets),
            "auth_not_configured",
        )
        self.assertEqual(
            validate_commercial_auth_configuration(invalid_redirect_secrets),
            "auth_not_configured",
        )
        self.assertIsNone(
            validate_commercial_auth_configuration(self._valid_secrets())
        )

    def test_pending_login_error_is_exposed_until_authentication_succeeds(self) -> None:
        session_state = {AUTH_ERROR_SESSION_KEY: "login_start_failed"}

        error_context = apply_commercial_auth_session_error(
            context=CommercialAuthContext(user=None, error_code=None),
            session_state=session_state,
        )
        authenticated_context = apply_commercial_auth_session_error(
            context=CommercialAuthContext(
                user=AuthenticatedUser(
                    id=7,
                    display_name="회원",
                    email=None,
                    provider="Google",
                ),
                error_code=None,
            ),
            session_state=session_state,
        )

        self.assertEqual(error_context.error_code, "login_start_failed")
        self.assertIsNotNone(authenticated_context.user)
        self.assertNotIn(AUTH_ERROR_SESSION_KEY, session_state)

    def test_login_configuration_error_is_sanitized_and_persisted(self) -> None:
        streamlit_mock = Mock()
        streamlit_mock.secrets = {}
        streamlit_mock.session_state = {}

        with patch("modules.ui.commercial_auth.st", streamlit_mock):
            error_code = login_commercial_user()

        self.assertEqual(error_code, "auth_not_configured")
        self.assertEqual(
            streamlit_mock.session_state[AUTH_ERROR_SESSION_KEY],
            "auth_not_configured",
        )
        streamlit_mock.login.assert_not_called()
        streamlit_mock.error.assert_called_once()
        streamlit_mock.rerun.assert_called_once_with()

    def test_login_start_failure_does_not_expose_exception_text(self) -> None:
        streamlit_mock = Mock()
        streamlit_mock.secrets = self._valid_secrets()
        streamlit_mock.session_state = {}
        streamlit_mock.login.side_effect = RuntimeError("client_secret=must-not-leak")

        with patch("modules.ui.commercial_auth.st", streamlit_mock):
            error_code = login_commercial_user()

        self.assertEqual(error_code, "login_start_failed")
        rendered_message = streamlit_mock.error.call_args.args[0]
        self.assertNotIn("must-not-leak", rendered_message)
        self.assertEqual(
            streamlit_mock.session_state[AUTH_ERROR_SESSION_KEY],
            "login_start_failed",
        )
        streamlit_mock.rerun.assert_called_once_with()

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
        streamlit_mock.secrets = self._valid_secrets()
        streamlit_mock.session_state = {SEARCH_HOME_QUERY_KEY: "검색어", "commercial_x": 1}

        with patch("modules.ui.commercial_auth.st", streamlit_mock):
            login_commercial_user()
            logout_commercial_user()

        streamlit_mock.login.assert_called_once_with("auth0")
        streamlit_mock.logout.assert_called_once_with()
        self.assertEqual(streamlit_mock.session_state, {SEARCH_HOME_QUERY_KEY: "검색어"})


if __name__ == "__main__":
    unittest.main()
