from __future__ import annotations

import unittest

from modules.ui.admin_view import _default_molit_lawd_code, _format_molit_sale_candidates


class AdminViewMolitCandidatesTests(unittest.TestCase):
    def test_format_molit_sale_candidates_returns_display_lines(self) -> None:
        lines = _format_molit_sale_candidates(
            [
                {
                    "aptNm": "\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc624",
                    "umdNm": "\uae08\ud638\ub3d94\uac00",
                    "count": 3,
                },
                {
                    "aptNm": "\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc6241\ucc28",
                    "umdNm": "\uae08\ud638\ub3d94\uac00",
                    "count": 1,
                },
            ]
        )

        self.assertEqual(
            lines,
            [
                "- aptNm=\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc624, umdNm=\uae08\ud638\ub3d94\uac00, count=3",
                "- aptNm=\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc6241\ucc28, umdNm=\uae08\ud638\ub3d94\uac00, count=1",
            ],
        )

    def test_default_molit_lawd_code_prefers_auto_resolved_value(self) -> None:
        service = _StubLawdCodeService("11680")
        self.assertEqual(
            _default_molit_lawd_code(
                {
                    "sido": "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
                    "sigungu": "\uac15\ub0a8\uad6c",
                    "dong": "\uc5ed\uc0bc\ub3d9",
                    "molit_lawd_cd": "12345",
                },
                lawd_code_service=service,
            ),
            "11680",
        )

    def test_default_molit_lawd_code_uses_saved_mapping_value(self) -> None:
        self.assertEqual(
            _default_molit_lawd_code({"molit_lawd_cd": "11200"}),
            "11200",
        )
        self.assertEqual(_default_molit_lawd_code({}), "")

    def test_default_molit_lawd_code_falls_back_when_service_returns_none(self) -> None:
        service = _StubLawdCodeService(None)
        self.assertEqual(
            _default_molit_lawd_code(
                {"molit_lawd_cd": "11200"},
                lawd_code_service=service,
            ),
            "11200",
        )


class _StubLawdCodeService:
    def __init__(self, resolved_value: str | None) -> None:
        self.resolved_value = resolved_value

    def resolve_lawd_code(self, *, sido, sigungu, dong) -> str | None:
        return self.resolved_value


if __name__ == "__main__":
    unittest.main()
