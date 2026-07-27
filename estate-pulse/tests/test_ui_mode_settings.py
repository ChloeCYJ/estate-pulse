from __future__ import annotations

import os
from unittest.mock import patch
import unittest

from config import settings as settings_module


class UIModeSettingsTests(unittest.TestCase):
    def tearDown(self) -> None:
        settings_module.get_settings.cache_clear()

    def test_ui_mode_defaults_to_legacy(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings_module.get_settings.cache_clear()

            settings = settings_module.get_settings()

        self.assertEqual(settings.ui_mode, "legacy")

    def test_ui_mode_accepts_commercial(self) -> None:
        with patch.dict(os.environ, {"ESTATE_PLUS_UI_MODE": "commercial"}, clear=True):
            settings_module.get_settings.cache_clear()

            settings = settings_module.get_settings()

        self.assertEqual(settings.ui_mode, "commercial")

    def test_ui_mode_falls_back_to_legacy_for_invalid_value(self) -> None:
        with patch.dict(os.environ, {"ESTATE_PLUS_UI_MODE": "future-ui"}, clear=True):
            settings_module.get_settings.cache_clear()

            settings = settings_module.get_settings()

        self.assertEqual(settings.ui_mode, "legacy")


if __name__ == "__main__":
    unittest.main()
