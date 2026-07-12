from __future__ import annotations

import unittest

from modules.ui.admin_view import (
    MOLIT_SALE_IMPORT_STATE_KEY,
    _build_molit_mapping_update_payload,
    _clear_molit_sale_import_state,
    _default_molit_lawd_code,
    _format_molit_sale_candidate_options,
    _format_molit_sale_candidates,
    _get_molit_sale_import_state_for_complex,
    _store_molit_sale_import_state,
)


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

    def test_format_molit_sale_candidate_options_returns_label_mapping(self) -> None:
        options = _format_molit_sale_candidate_options(
            [
                {"aptNm": "대우", "umdNm": "금호동4가", "count": 38},
                {"aptNm": "서울숲 한신 더 휴", "umdNm": "행당동", "count": 54},
            ]
        )

        self.assertEqual(
            list(options.keys()),
            [
                "aptNm=대우 | umdNm=금호동4가 | count=38",
                "aptNm=서울숲 한신 더 휴 | umdNm=행당동 | count=54",
            ],
        )
        self.assertEqual(options["aptNm=대우 | umdNm=금호동4가 | count=38"]["aptNm"], "대우")

    def test_build_molit_mapping_update_payload_preserves_existing_complex_fields(self) -> None:
        payload = _build_molit_mapping_update_payload(
            {
                "id": 12,
                "name": "서울숲푸르지오1차",
                "sido": "서울특별시",
                "sigungu": "성동구",
                "dong": "금호동4가",
                "address": "서울특별시 성동구 금호로 15",
                "build_year": 2007,
                "household_count": 888,
                "lat": 37.0,
                "lng": 127.0,
                "complex_grade": "NORMAL",
                "memo": "memo",
            },
            lawd_code="11200",
            apt_name="대우",
            umd_name="금호동4가",
        )

        self.assertEqual(
            payload,
            {
                "name": "서울숲푸르지오1차",
                "sido": "서울특별시",
                "sigungu": "성동구",
                "dong": "금호동4가",
                "address": "서울특별시 성동구 금호로 15",
                "build_year": 2007,
                "household_count": 888,
                "lat": 37.0,
                "lng": 127.0,
                "molit_lawd_cd": "11200",
                "molit_apt_name": "대우",
                "molit_umd_name": "금호동4가",
                "complex_grade": "NORMAL",
                "memo": "memo",
            },
        )

    def test_molit_sale_import_state_round_trip_for_same_complex(self) -> None:
        session_state: dict = {}

        _store_molit_sale_import_state(
            session_state,
            complex_id=16,
            lawd_code="11200",
            message="No matching MOLIT sale transactions were found.",
            candidates=[{"aptNm": "옥수삼성", "umdNm": "옥수동", "count": 4}],
        )

        state = _get_molit_sale_import_state_for_complex(session_state, complex_id=16)

        self.assertIsNotNone(state)
        self.assertEqual(session_state[MOLIT_SALE_IMPORT_STATE_KEY]["complex_id"], 16)
        self.assertEqual(state["lawd_code"], "11200")
        self.assertEqual(state["candidates"][0]["aptNm"], "옥수삼성")

    def test_molit_sale_import_state_is_ignored_for_other_complex(self) -> None:
        session_state: dict = {}

        _store_molit_sale_import_state(
            session_state,
            complex_id=16,
            lawd_code="11200",
            message="No matching MOLIT sale transactions were found.",
            candidates=[{"aptNm": "옥수삼성", "umdNm": "옥수동", "count": 4}],
        )

        self.assertIsNone(_get_molit_sale_import_state_for_complex(session_state, complex_id=99))

    def test_clear_molit_sale_import_state_removes_saved_no_match_state(self) -> None:
        session_state = {
            MOLIT_SALE_IMPORT_STATE_KEY: {
                "complex_id": 16,
                "lawd_code": "11200",
                "message": "No matching MOLIT sale transactions were found.",
                "candidates": [],
            }
        }

        _clear_molit_sale_import_state(session_state)

        self.assertNotIn(MOLIT_SALE_IMPORT_STATE_KEY, session_state)


class _StubLawdCodeService:
    def __init__(self, resolved_value: str | None) -> None:
        self.resolved_value = resolved_value

    def resolve_lawd_code(self, *, sido, sigungu, dong) -> str | None:
        return self.resolved_value


if __name__ == "__main__":
    unittest.main()
