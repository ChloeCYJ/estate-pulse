from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import ANY, Mock, patch
import unittest

import app
from modules.services.auth_service import AuthenticatedUser
from modules.ui.commercial_auth import CommercialAuthContext
from modules.ui.commercial_page_state import CommercialPageState, save_commercial_page_state


class AppShellTests(unittest.TestCase):
    def test_render_app_shell_skips_sidebar_in_commercial_mode(self) -> None:
        dashboard_renderer = Mock()
        streamlit_mock = Mock()
        streamlit_mock.sidebar = Mock()
        streamlit_mock.session_state = {}

        with patch.object(app, "st", streamlit_mock):
            app.render_app_shell(
                settings=SimpleNamespace(app_name="Estate Pulse", ui_mode="commercial"),
                user_pages={"Dashboard": dashboard_renderer},
                admin_pages={"관리자": Mock()},
            )

        dashboard_renderer.assert_called_once_with()
        streamlit_mock.sidebar.title.assert_not_called()
        streamlit_mock.sidebar.radio.assert_not_called()

    def test_render_app_shell_keeps_legacy_sidebar_navigation(self) -> None:
        dashboard_renderer = Mock()
        streamlit_mock = Mock()
        streamlit_mock.sidebar = Mock()
        streamlit_mock.sidebar.radio.side_effect = ["사용자", "Dashboard"]
        streamlit_mock.session_state = {}

        with patch.object(app, "st", streamlit_mock):
            app.render_app_shell(
                settings=SimpleNamespace(app_name="Estate Pulse", ui_mode="legacy"),
                user_pages={"Dashboard": dashboard_renderer},
                admin_pages={"관리자": Mock()},
            )

        streamlit_mock.sidebar.title.assert_called_once_with("Estate Pulse")
        dashboard_renderer.assert_called_once_with()


    def test_render_commercial_root_page_routes_analysis_dashboard_state(self) -> None:
        streamlit_mock = Mock()
        streamlit_mock.session_state = {}
        save_commercial_page_state(
            streamlit_mock.session_state,
            CommercialPageState(
                commercial_page="analysis_dashboard",
                analysis_source="saved",
                active_analysis_id=41,
            ),
        )

        with (
            patch.object(app, "st", streamlit_mock),
            patch.object(app, "render_search_home_page") as search_home_mock,
            patch.object(app, "render_commercial_analysis_page") as analysis_page_mock,
            patch.object(app, "render_comparison_page") as comparison_page_mock,
        ):
            auth_context = CommercialAuthContext(
                user=AuthenticatedUser(
                    id=7,
                    display_name="회원",
                    email="member@example.com",
                    provider="Google",
                ),
                error_code=None,
            )
            auth_view_model = {"status": "authenticated"}
            app.render_commercial_root_page(
                settings=SimpleNamespace(ui_mode="commercial"),
                complex_repository=Mock(),
                listing_repository=Mock(),
                finance_repository=Mock(),
                analysis_repository=Mock(),
                policy_event_service=Mock(),
                address_search_service=Mock(),
                analysis_service=Mock(),
                opportunity_service=Mock(),
                auth_context=auth_context,
                auth_view_model=auth_view_model,
            )

        analysis_page_mock.assert_called_once_with(
            analysis_repository=ANY,
            analysis_service=ANY,
            auth_context=auth_context,
            auth_view_model=auth_view_model,
        )
        search_home_mock.assert_not_called()
        comparison_page_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
