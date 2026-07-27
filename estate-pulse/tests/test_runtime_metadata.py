from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class RuntimeMetadataTests(unittest.TestCase):
    def test_python_version_file_pins_python_3_14_6(self) -> None:
        version_file = ROOT / ".python-version"
        self.assertTrue(version_file.exists(), ".python-version must exist")
        self.assertEqual(version_file.read_text(encoding="utf-8").strip(), "3.14.6")

    def test_nvmrc_pins_node_24_18_0(self) -> None:
        nvmrc_file = ROOT / ".nvmrc"
        self.assertTrue(nvmrc_file.exists(), ".nvmrc must exist")
        self.assertEqual(nvmrc_file.read_text(encoding="utf-8").strip(), "24.18.0")

    def test_requirements_pin_streamlit_1_59_0(self) -> None:
        requirements_text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("streamlit==1.59.0", requirements_text)


if __name__ == "__main__":
    unittest.main()
