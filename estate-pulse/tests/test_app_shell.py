from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

import app


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


if __name__ == "__main__":
    unittest.main()
