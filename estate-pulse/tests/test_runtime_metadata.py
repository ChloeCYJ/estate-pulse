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

    def test_commercial_auth_configuration_is_safe_to_commit(self) -> None:
        gitignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        requirements_text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        example_text = (ROOT / ".streamlit" / "secrets.toml.example").read_text(
            encoding="utf-8"
        )

        self.assertIn(".streamlit/secrets.toml", gitignore_text)
        self.assertIn("Authlib>=1.3.2,<2.0", requirements_text)
        self.assertIn("httpx>=0.24.1,<1.0", requirements_text)
        self.assertIn("argon2-cffi>=25.1,<26.0", requirements_text)
        self.assertIn("[auth.auth0]", example_text)
        self.assertIn("REPLACE_WITH_AUTH0_CLIENT_ID", example_text)
        self.assertIn("[local_admin]", example_text)
        self.assertIn("REPLACE_WITH_ADMIN_USERNAME", example_text)
        self.assertIn("REPLACE_WITH_ARGON2_PASSWORD_HASH", example_text)
        self.assertNotIn("$argon2", example_text)
        self.assertNotIn("@", example_text)


if __name__ == "__main__":
    unittest.main()
