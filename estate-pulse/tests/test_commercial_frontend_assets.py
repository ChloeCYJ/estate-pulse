from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent
FRONTEND_BUILD_DIR = ROOT / "commercial_ui" / "frontend" / "build"


class CommercialFrontendAssetTests(unittest.TestCase):
    def test_css_build_asset_exists_and_is_not_empty(self) -> None:
        css_path = FRONTEND_BUILD_DIR / "commercial-ui.css"

        self.assertTrue(css_path.exists(), f"Missing CSS asset: {css_path}")
        self.assertGreater(css_path.stat().st_size, 0, "CSS asset should not be empty")

    def test_css_build_asset_contains_required_selectors(self) -> None:
        css_path = FRONTEND_BUILD_DIR / "commercial-ui.css"
        css_text = css_path.read_text(encoding="utf-8")

        for selector in (
            ".ep-shell",
            ".ep-layout",
            ".ep-searchbar__input",
            ".ep-button--primary",
            ".ep-recent-card",
            ".ep-recent-grid",
        ):
            self.assertIn(selector, css_text)


if __name__ == "__main__":
    unittest.main()
