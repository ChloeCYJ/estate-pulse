from __future__ import annotations

import json
import unittest

from modules.ui.viewmodels.search_home import (
    SEARCH_STATUS_ERROR,
    SEARCH_STATUS_IDLE,
    SEARCH_STATUS_NO_RESULTS,
    build_search_home_view_model,
)


class SearchHomeViewModelTests(unittest.TestCase):
    def test_build_search_home_view_model_keeps_idle_empty_state_distinct(self) -> None:
        view_model = build_search_home_view_model(
            search_query="",
            search_status=SEARCH_STATUS_IDLE,
            recent_analyses=[],
            search_results=None,
            display_error=None,
        )

        self.assertEqual(view_model["search_status"], SEARCH_STATUS_IDLE)
        self.assertTrue(view_model["empty_state"])
        self.assertEqual(view_model["recent_analyses"], [])
        self.assertEqual(view_model["search_results"], [])
        self.assertIsNone(view_model["display_error"])

    def test_build_search_home_view_model_formats_recent_analysis_cards(self) -> None:
        view_model = build_search_home_view_model(
            search_query="마포",
            search_status=SEARCH_STATUS_IDLE,
            recent_analyses=[
                {
                    "id": 41,
                    "complex_name": "마포래미안푸르지오",
                    "area_m2": 84.9,
                    "sale_price": 1_230_000_000,
                    "created_at": "2026-07-25T09:41:00+09:00",
                    "location_label": "서울 마포구 아현동",
                }
            ],
            search_results=[],
            display_error=None,
        )

        self.assertEqual(view_model["recent_analyses"][0]["analysis_id"], "41")
        self.assertEqual(view_model["recent_analyses"][0]["complex_name"], "마포래미안푸르지오")
        self.assertEqual(view_model["recent_analyses"][0]["area_label"], "84.9m²")
        self.assertEqual(view_model["recent_analyses"][0]["reference_price_label"], "12.3억")
        self.assertEqual(view_model["recent_analyses"][0]["analyzed_at_label"], "2026-07-25 09:41")
        self.assertEqual(view_model["recent_analyses"][0]["location_label"], "서울 마포구 아현동")

    def test_build_search_home_view_model_distinguishes_no_results_from_error(self) -> None:
        no_results = build_search_home_view_model(
            search_query="없는단지",
            search_status=SEARCH_STATUS_NO_RESULTS,
            recent_analyses=[],
            search_results=[],
            display_error=None,
        )
        error_state = build_search_home_view_model(
            search_query="오류단지",
            search_status=SEARCH_STATUS_ERROR,
            recent_analyses=[],
            search_results=[],
            display_error={
                "code": "system_error",
                "message": "검색 중 오류가 발생했습니다.",
            },
        )

        self.assertEqual(no_results["search_status"], SEARCH_STATUS_NO_RESULTS)
        self.assertIsNone(no_results["display_error"])
        self.assertEqual(error_state["search_status"], SEARCH_STATUS_ERROR)
        self.assertEqual(error_state["display_error"]["code"], "system_error")

    def test_view_model_is_json_serializable(self) -> None:
        view_model = build_search_home_view_model(
            search_query="성수",
            search_status=SEARCH_STATUS_IDLE,
            recent_analyses=[],
            search_results=[
                {
                    "result_id": "complex:1",
                    "result_type": "registered_complex",
                    "title": "트리마제",
                    "subtitle": "서울 성동구 성수동1가",
                    "meta": "등록된 단지",
                }
            ],
            display_error=None,
        )

        payload = json.dumps(view_model, ensure_ascii=False)

        self.assertIn('"service_title": "Estate Plus"', payload)


if __name__ == "__main__":
    unittest.main()
