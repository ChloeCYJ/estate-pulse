from __future__ import annotations

from unittest.mock import Mock, patch
import unittest

from argon2 import PasswordHasher

from modules.services.local_admin_auth_service import (
    LocalAdminAuthService,
    LocalAdminConfig,
)
from modules.ui import local_admin_auth
from modules.ui.local_admin_auth import (
    LOCAL_ADMIN_ERROR_KEY,
    LOCAL_ADMIN_SESSION_KEY,
    authenticate_local_admin,
    is_admin_portal_requested,
    load_local_admin_config,
    load_local_admin_principal,
    logout_local_admin,
    render_local_admin_gate,
)


class LocalAdminAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.password = "strong-admin-password"
        password_hash = PasswordHasher(
            time_cost=1,
            memory_cost=1024,
            parallelism=1,
        ).hash(self.password)
        self.service = LocalAdminAuthService(
            LocalAdminConfig(
                enabled=True,
                username="operator",
                password_hash=password_hash,
            )
        )

    def test_load_config_and_admin_query_parameter(self) -> None:
        config = load_local_admin_config(
            {
                "local_admin": {
                    "enabled": True,
                    "username": "operator",
                    "password_hash": "encoded",
                }
            }
        )

        self.assertTrue(config.enabled)
        self.assertEqual(config.username, "operator")
        self.assertTrue(is_admin_portal_requested({"admin": "1"}))
        self.assertTrue(is_admin_portal_requested({"admin": ["0", "1"]}))
        self.assertFalse(is_admin_portal_requested({"admin": "true"}))

    def test_missing_or_broken_secrets_fail_closed(self) -> None:
        broken = Mock()
        broken.get.side_effect = FileNotFoundError("missing")

        self.assertFalse(load_local_admin_config({}).enabled)
        self.assertFalse(load_local_admin_config(broken).enabled)

    def test_authenticate_and_logout_preserve_unrelated_state(self) -> None:
        session_state: dict[str, object] = {"commercial_search_home_query": "마포"}

        principal = authenticate_local_admin(
            session_state=session_state,
            auth_service=self.service,
            username="operator",
            password=self.password,
        )

        self.assertIsNotNone(principal)
        self.assertEqual(load_local_admin_principal(session_state).role, "admin")
        logout_local_admin(session_state)
        self.assertNotIn(LOCAL_ADMIN_SESSION_KEY, session_state)
        self.assertEqual(session_state["commercial_search_home_query"], "마포")

    def test_invalid_credentials_store_only_sanitized_error(self) -> None:
        session_state: dict[str, object] = {}

        principal = authenticate_local_admin(
            session_state=session_state,
            auth_service=self.service,
            username="operator",
            password="wrong-password",
        )

        self.assertIsNone(principal)
        self.assertEqual(session_state[LOCAL_ADMIN_ERROR_KEY], "invalid_credentials")
        self.assertNotIn("wrong-password", str(session_state))

    def test_malformed_session_is_rejected(self) -> None:
        self.assertIsNone(
            load_local_admin_principal(
                {LOCAL_ADMIN_SESSION_KEY: {"username": "operator", "role": "user"}}
            )
        )

    def test_gate_calls_renderer_only_for_local_admin_session(self) -> None:
        renderer = Mock()
        streamlit_mock = Mock()
        streamlit_mock.session_state = {
            LOCAL_ADMIN_SESSION_KEY: {"username": "operator", "role": "admin"}
        }
        streamlit_mock.button.return_value = False

        with patch.object(local_admin_auth, "st", streamlit_mock):
            render_local_admin_gate(
                auth_service=self.service,
                admin_renderer=renderer,
            )

        renderer.assert_called_once_with()

        renderer.reset_mock()
        streamlit_mock.session_state = {}
        disabled_service = LocalAdminAuthService(
            LocalAdminConfig(enabled=False, username=None, password_hash=None)
        )
        with patch.object(local_admin_auth, "st", streamlit_mock):
            render_local_admin_gate(
                auth_service=disabled_service,
                admin_renderer=renderer,
            )
        renderer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
