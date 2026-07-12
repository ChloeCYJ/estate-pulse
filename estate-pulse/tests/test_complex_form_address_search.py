from __future__ import annotations

import unittest

from modules.services.address_search_service import AddressCandidate
from modules.ui.complex_form import (
    JUSO_PREVIEW_KEY,
    JUSO_SEARCH_KEYWORD_KEY,
    JUSO_SEARCH_RESULTS_KEY,
    MANAGE_SELECT_COLUMN,
    _candidate_from_label,
    _candidate_selectbox_options,
    _manage_complex_editor_rows,
    _render_registration_preview,
    _render_selected_candidate,
    _reset_search_state_if_keyword_changed,
    _selected_manage_complex,
    _selected_manage_complexes,
)


class ComplexFormAddressSearchTests(unittest.TestCase):
    def test_candidate_selectbox_options_include_placeholder(self) -> None:
        candidates = [self._candidate("Haengdang Xi")]

        options = _candidate_selectbox_options(candidates)

        self.assertEqual(options[0], "선택하세요")
        self.assertIn("Haengdang Xi", options[1])

    def test_candidate_from_label_returns_none_for_placeholder(self) -> None:
        self.assertIsNone(_candidate_from_label("선택하세요", [self._candidate("Haengdang Xi")]))

    def test_candidate_selectbox_options_disambiguate_duplicate_labels_with_road_address(self) -> None:
        first = self._candidate("Seoul Forest Prugio", road_address="서울특별시 성동구 금호로 82")
        second = self._candidate("Seoul Forest Prugio", road_address="서울특별시 성동구 금호로 10")

        options = _candidate_selectbox_options([first, second])

        self.assertEqual(len(options), 3)
        self.assertNotEqual(options[1], options[2])
        self.assertIn(first.road_address, options[1])
        self.assertIn(second.road_address, options[2])

    def test_candidate_from_label_returns_matching_candidate_for_disambiguated_option(self) -> None:
        first = self._candidate("Seoul Forest Prugio", road_address="서울특별시 성동구 금호로 82")
        second = self._candidate("Seoul Forest Prugio", road_address="서울특별시 성동구 금호로 10")

        options = _candidate_selectbox_options([first, second])
        selected = _candidate_from_label(options[2], [first, second])

        self.assertEqual(selected, second)

    def test_reset_search_state_clears_cached_candidates_when_keyword_changes(self) -> None:
        session_state = {
            JUSO_SEARCH_KEYWORD_KEY: "행당",
            JUSO_SEARCH_RESULTS_KEY: [self._candidate("Haengdang Xi")],
            JUSO_PREVIEW_KEY: {"lawd_cd": "11200"},
            "juso_candidate_selectbox": "Haengdang Xi | 서울특별시 성동구 행당동",
        }

        _reset_search_state_if_keyword_changed(
            session_state,
            current_keyword="마장",
            search_clicked=False,
        )

        self.assertNotIn(JUSO_SEARCH_KEYWORD_KEY, session_state)
        self.assertNotIn(JUSO_SEARCH_RESULTS_KEY, session_state)
        self.assertNotIn(JUSO_PREVIEW_KEY, session_state)
        self.assertNotIn("juso_candidate_selectbox", session_state)

    def test_reset_search_state_keeps_candidates_when_search_button_was_clicked(self) -> None:
        candidate = self._candidate("Haengdang Xi")
        session_state = {
            JUSO_SEARCH_KEYWORD_KEY: "행당",
            JUSO_SEARCH_RESULTS_KEY: [candidate],
        }

        _reset_search_state_if_keyword_changed(
            session_state,
            current_keyword="마장",
            search_clicked=True,
        )

        self.assertEqual(session_state[JUSO_SEARCH_RESULTS_KEY], [candidate])

    def test_selected_candidate_preview_uses_explicit_widget_keys(self) -> None:
        recorded_keys: list[str | None] = []
        fake_streamlit = _FakeStreamlit(recorded_keys)

        from modules.ui import complex_form

        original_streamlit = complex_form.st
        complex_form.st = fake_streamlit
        try:
            _render_selected_candidate(self._candidate("Haengdang Xi"))
        finally:
            complex_form.st = original_streamlit

        self.assertEqual(
            recorded_keys,
            [
                "juso_selected_complex_name",
                "juso_selected_region",
                "juso_selected_road_address",
                "juso_selected_jibun_address",
            ],
        )

    def test_registration_preview_uses_explicit_widget_keys(self) -> None:
        recorded_keys: list[str | None] = []
        fake_streamlit = _FakeStreamlit(recorded_keys)

        from modules.ui import complex_form

        original_streamlit = complex_form.st
        complex_form.st = fake_streamlit
        try:
            _render_registration_preview(
                {
                    "name": "Haengdang Xi",
                    "lawd_cd": "11200",
                    "sido": "서울특별시",
                    "sigungu": "성동구",
                    "dong": "행당동",
                    "address": "서울특별시 성동구 행당동 346",
                }
            )
        finally:
            complex_form.st = original_streamlit

        self.assertEqual(
            recorded_keys,
            [
                "juso_preview_complex_name",
                "juso_preview_lawd_cd",
                "juso_preview_region_address",
                "juso_preview_full_address",
            ],
        )

    def test_manage_complex_editor_rows_start_unselected_and_keep_identifiers(self) -> None:
        rows = _manage_complex_editor_rows([self._complex_item(5, "서울숲푸르지오1차")])

        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0][MANAGE_SELECT_COLUMN])
        self.assertEqual(rows[0]["ID"], 5)
        self.assertEqual(rows[0]["단지명"], "서울숲푸르지오1차")

    def test_selected_manage_complex_returns_single_checked_complex(self) -> None:
        complexes = [
            self._complex_item(5, "서울숲푸르지오1차"),
            self._complex_item(1, "서울숲푸르지오1차", address="서울특별시 성동구 금호동4가 340"),
        ]
        rows = _manage_complex_editor_rows(complexes)
        rows[1][MANAGE_SELECT_COLUMN] = True

        selected, selected_count = _selected_manage_complex(rows, complexes)

        self.assertEqual(selected_count, 1)
        self.assertIsNotNone(selected)
        self.assertEqual(selected["id"], 1)

    def test_selected_manage_complexes_return_all_checked_complexes_for_bulk_delete(self) -> None:
        complexes = [
            self._complex_item(5, "서울숲푸르지오1차"),
            self._complex_item(4, "샘플레이크뷰"),
            self._complex_item(1, "서울숲푸르지오1차", address="서울특별시 성동구 금호동4가 340"),
        ]
        rows = _manage_complex_editor_rows(complexes)
        rows[0][MANAGE_SELECT_COLUMN] = True
        rows[2][MANAGE_SELECT_COLUMN] = True

        selected = _selected_manage_complexes(rows, complexes)

        self.assertEqual([item["id"] for item in selected], [5, 1])

    def test_selected_manage_complex_returns_none_for_multiple_checked_rows(self) -> None:
        complexes = [
            self._complex_item(5, "서울숲푸르지오1차"),
            self._complex_item(1, "서울숲푸르지오1차", address="서울특별시 성동구 금호동4가 340"),
        ]
        rows = _manage_complex_editor_rows(complexes)
        rows[0][MANAGE_SELECT_COLUMN] = True
        rows[1][MANAGE_SELECT_COLUMN] = True

        selected, selected_count = _selected_manage_complex(rows, complexes)

        self.assertEqual(selected_count, 2)
        self.assertIsNone(selected)

    @staticmethod
    def _candidate(name: str, *, road_address: str = "서울특별시 성동구 행당로 82") -> AddressCandidate:
        return AddressCandidate(
            complex_name=name,
            road_address=road_address,
            jibun_address="서울특별시 성동구 행당동 346",
            sido="서울특별시",
            sigungu="성동구",
            emd="행당동",
            li="",
            admin_code="1120011300",
            building_management_no="1120011300103460000012345",
            is_apartment=True,
        )

    @staticmethod
    def _complex_item(
        item_id: int,
        name: str,
        *,
        address: str = "서울특별시 성동구 금호로 15",
        created_at: str = "2026-07-12T15:33:26+09:00",
    ) -> dict:
        return {
            "id": item_id,
            "name": name,
            "sido": "서울시",
            "sigungu": "성동구",
            "dong": "금호동4가",
            "address": address,
            "created_at": created_at,
        }


class _FakeColumn:
    def __init__(self, recorded_keys: list[str | None]) -> None:
        self.recorded_keys = recorded_keys

    def text_input(self, _label: str, **kwargs) -> None:
        self.recorded_keys.append(kwargs.get("key"))


class _FakeStreamlit:
    def __init__(self, recorded_keys: list[str | None]) -> None:
        self.recorded_keys = recorded_keys

    def caption(self, _text: str) -> None:
        return None

    def columns(self, count: int) -> list[_FakeColumn]:
        return [_FakeColumn(self.recorded_keys) for _ in range(count)]

    def text_input(self, _label: str, **kwargs) -> None:
        self.recorded_keys.append(kwargs.get("key"))


if __name__ == "__main__":
    unittest.main()
