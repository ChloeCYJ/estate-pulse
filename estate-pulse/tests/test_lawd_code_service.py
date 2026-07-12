from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.services.lawd_code_service import LawdCodeService


class LawdCodeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.source_path = Path(self.temp_dir.name) / "lawd.txt"
        self.source_path.write_text(
            "\t".join(
                [
                    "\ubc95\uc815\ub3d9\ucf54\ub4dc",
                    "\ubc95\uc815\ub3d9\uba85",
                    "\ud3d0\uc9c0\uc5ec\ubd80",
                ]
            )
            + "\n"
            + "\n".join(
                [
                    "1100000000\t\uc11c\uc6b8\ud2b9\ubcc4\uc2dc\t\uc874\uc7ac",
                    "2600000000\t\ubd80\uc0b0\uad11\uc5ed\uc2dc\t\uc874\uc7ac",
                    "2635000000\t\ubd80\uc0b0\uad11\uc5ed\uc2dc \ud574\uc6b4\ub300\uad6c\t\uc874\uc7ac",
                    "2635010100\t\ubd80\uc0b0\uad11\uc5ed\uc2dc \ud574\uc6b4\ub300\uad6c \uc6b0\ub3d9\t\uc874\uc7ac",
                    "1168000000\t\uc11c\uc6b8\ud2b9\ubcc4\uc2dc \uac15\ub0a8\uad6c\t\uc874\uc7ac",
                    "1120000000\t\uc11c\uc6b8\ud2b9\ubcc4\uc2dc \uc131\ub3d9\uad6c\t\uc874\uc7ac",
                    "1120011300\t\uc11c\uc6b8\ud2b9\ubcc4\uc2dc \uc131\ub3d9\uad6c \uae08\ud638\ub3d94\uac00\t\uc874\uc7ac",
                    "1168010100\t\uc11c\uc6b8\ud2b9\ubcc4\uc2dc \uac15\ub0a8\uad6c \uc5ed\uc0bc\ub3d9\t\uc874\uc7ac",
                    "1168010200\t\uc11c\uc6b8\ud2b9\ubcc4\uc2dc \uac15\ub0a8\uad6c \uac1c\ud3ec\ub3d9\t\ud3d0\uc9c0",
                    "3611000000\t\uc138\uc885\ud2b9\ubcc4\uc790\uce58\uc2dc\t\uc874\uc7ac",
                    "3611025000\t\uc138\uc885\ud2b9\ubcc4\uc790\uce58\uc2dc \uc870\uce58\uc6d0\uc74d\t\uc874\uc7ac",
                ]
            ),
            encoding="utf-8",
        )
        self.service = LawdCodeService(self.source_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_resolve_lawd_code_returns_sigungu_prefix_for_exact_dong_match(self) -> None:
        self.assertEqual(
            self.service.resolve_lawd_code(
                sido="\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
                sigungu="\uac15\ub0a8\uad6c",
                dong="\uc5ed\uc0bc\ub3d9",
            ),
            "11680",
        )

    def test_resolve_lawd_code_returns_none_for_wrong_dong(self) -> None:
        self.assertEqual(
            self.service.resolve_lawd_code(
                sido="\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
                sigungu="\uac15\ub0a8\uad6c",
                dong="\ub9e4\uce6d\uc5c6\uc74c",
            ),
            None,
        )

    def test_resolve_lawd_code_ignores_deleted_rows(self) -> None:
        self.assertEqual(
            self.service.resolve_lawd_code(
                sido="\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
                sigungu="\uac15\ub0a8\uad6c",
                dong="\uac1c\ud3ec\ub3d9",
            ),
            None,
        )

    def test_resolve_lawd_code_supports_sido_plus_dong_without_sigungu(self) -> None:
        self.assertEqual(
            self.service.resolve_lawd_code(
                sido="\uc138\uc885\ud2b9\ubcc4\uc790\uce58\uc2dc",
                sigungu=None,
                dong="\uc870\uce58\uc6d0\uc74d",
            ),
            "36110",
        )

    def test_resolve_lawd_code_supports_seoul_sido_alias(self) -> None:
        self.assertEqual(
            self.service.resolve_lawd_code(
                sido="\uc11c\uc6b8\uc2dc",
                sigungu="\uc131\ub3d9\uad6c",
                dong="\uae08\ud638\ub3d94\uac00",
            ),
            "11200",
        )

    def test_resolve_lawd_code_supports_full_seoul_sido_name(self) -> None:
        self.assertEqual(
            self.service.resolve_lawd_code(
                sido="\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
                sigungu="\uc131\ub3d9\uad6c",
                dong="\uae08\ud638\ub3d94\uac00",
            ),
            "11200",
        )

    def test_resolve_lawd_code_supports_busan_sido_alias(self) -> None:
        self.assertEqual(
            self.service.resolve_lawd_code(
                sido="\ubd80\uc0b0\uc2dc",
                sigungu="\ud574\uc6b4\ub300\uad6c",
                dong="\uc6b0\ub3d9",
            ),
            "26350",
        )

    def test_find_lawd_code_matches_returns_exact_10_digit_matches(self) -> None:
        self.assertEqual(
            self.service.find_lawd_code_matches(
                sido="\uc11c\uc6b8\uc2dc",
                sigungu="\uc131\ub3d9\uad6c",
                dong="\uae08\ud638\ub3d94\uac00",
            ),
            ["1120011300"],
        )

    def test_list_search_regions_returns_sigungu_codes_and_special_city_top_level(self) -> None:
        self.assertEqual(
            self.service.list_search_regions(),
            [
                {
                    "lawd_code": "26350",
                    "sido": "\ubd80\uc0b0\uad11\uc5ed\uc2dc",
                    "sigungu": "\ud574\uc6b4\ub300\uad6c",
                },
                {
                    "lawd_code": "11680",
                    "sido": "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
                    "sigungu": "\uac15\ub0a8\uad6c",
                },
                {
                    "lawd_code": "11200",
                    "sido": "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
                    "sigungu": "\uc131\ub3d9\uad6c",
                },
                {
                    "lawd_code": "36110",
                    "sido": "\uc138\uc885\ud2b9\ubcc4\uc790\uce58\uc2dc",
                    "sigungu": None,
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
