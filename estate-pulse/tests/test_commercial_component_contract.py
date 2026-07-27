from __future__ import annotations

from importlib import import_module, reload
from pathlib import Path
import sys
from unittest.mock import Mock, patch
import unittest


ROOT = Path(__file__).resolve().parent.parent
COMPONENT_PROJECT_ROOT = ROOT / "commercial_ui"


class CommercialComponentContractTests(unittest.TestCase):
    def setUp(self) -> None:
        if str(COMPONENT_PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(COMPONENT_PROJECT_ROOT))

    def test_render_commercial_ui_mounts_v2_component_with_expected_envelope(self) -> None:
        mount_mock = Mock(return_value=Mock(search_submitted=None))

        with patch("streamlit.components.v2.component", return_value=mount_mock) as component_factory:
            module = import_module("commercial_ui.component")
            module = reload(module)

            result = module.render_commercial_ui(
                page="search-home",
                view_model={"service_title": "Estate Plus"},
                key="commercial-search-home",
            )

        component_factory.assert_called_once_with(
            "commercial_ui.commercial_ui",
            html=" ",
            js="commercial-ui.js",
            css="commercial-ui.css",
            isolate_styles=True,
        )
        mount_mock.assert_called_once()
        mount_kwargs = mount_mock.call_args.kwargs
        self.assertEqual(mount_kwargs["key"], "commercial-search-home")
        self.assertEqual(mount_kwargs["height"], "content")
        self.assertEqual(mount_kwargs["width"], "stretch")
        self.assertEqual(mount_kwargs["data"]["page"], "search-home")
        self.assertEqual(mount_kwargs["data"]["view_model"]["service_title"], "Estate Plus")
        self.assertEqual(mount_kwargs["data"]["meta"]["locale"], "ko-KR")
        self.assertIs(result, mount_mock.return_value)

    def test_component_build_dir_helper_points_to_package_build_output(self) -> None:
        module = import_module("commercial_ui.component")
        module = reload(module)

        build_dir = module.get_component_build_dir()

        self.assertEqual(
            build_dir,
            COMPONENT_PROJECT_ROOT / "frontend" / "build",
        )


if __name__ == "__main__":
    unittest.main()
