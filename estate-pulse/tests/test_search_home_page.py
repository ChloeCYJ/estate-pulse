from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch
import unittest

from modules.ui.page_ids import PAGE_COMPARISON, PAGE_DASHBOARD
from modules.ui.search_home_page import (
    NAVIGATION_TARGET_COMPARISON,
    NAVIGATION_TARGET_SAVED_ANALYSES,
    SEARCH_STATUS_ERROR,
    SEARCH_STATUS_NO_RESULTS,
    SEARCH_STATUS_SUCCESS,
    SIDEBAR_USER_PAGE_KEY,
    build_search_home_page_state,
    handle_navigation_selected,
    handle_recent_analysis_selected,
    handle_search_submitted,
    render_search_home_page,
)


@dataclass(frozen=True)
class _AddressCandidate:
    complex_name: str
    road_address: str
    jibun_address: str


class SearchHomePageTests(unittest.TestCase):
    def test_handle_search_submitted_combines_registered_complex_and_address_results(self) -> None:
        complex_repository = Mock()
        complex_repository.list_all.return_value = [
            {
                "id": 3,
                "name": "서울숲트리마제",
                "sido": "서울",
                "sigungu": "성동구",
                "dong": "성수동1가",
                "address": "서울 성동구 왕십리로 83",
            }
        ]
        address_search_service = Mock()
        address_search_service.search_candidates.return_value = [
            _AddressCandidate(
                complex_name="서울숲트리마제",
                road_address="서울 성동구 왕십리로 83",
                jibun_address="서울 성동구 성수동1가 685-700",
            )
        ]

        state = handle_search_submitted(
            query="성수",
            complex_repository=complex_repository,
            address_search_service=address_search_service,
        )

        self.assertEqual(state.search_status, SEARCH_STATUS_SUCCESS)
        self.assertEqual(len(state.search_results), 2)
        self.assertEqual(state.search_results[0]["result_type"], "registered_complex")
        self.assertEqual(state.search_results[1]["result_type"], "address_candidate")

    def test_handle_search_submitted_marks_no_results_without_error(self) -> None:
        complex_repository = Mock()
        complex_repository.list_all.return_value = []
        address_search_service = Mock()
        address_search_service.search_candidates.return_value = []

        state = handle_search_submitted(
            query="없는단지",
            complex_repository=complex_repository,
            address_search_service=address_search_service,
        )

        self.assertEqual(state.search_status, SEARCH_STATUS_NO_RESULTS)
        self.assertEqual(state.search_results, [])
        self.assertIsNone(state.display_error)

    def test_handle_search_submitted_surfaces_system_error(self) -> None:
        complex_repository = Mock()
        complex_repository.list_all.return_value = []
        address_search_service = Mock()
        address_search_service.search_candidates.side_effect = RuntimeError("boom")

        state = handle_search_submitted(
            query="성수",
            complex_repository=complex_repository,
            address_search_service=address_search_service,
        )

        self.assertEqual(state.search_status, SEARCH_STATUS_ERROR)
        self.assertEqual(state.display_error["code"], "search_failed")
        self.assertEqual(state.search_results, [])

    def test_handle_recent_analysis_selected_records_selected_analysis_id(self) -> None:
        session_state: dict[str, object] = {}

        handle_recent_analysis_selected(
            session_state=session_state,
            analysis_id="18",
        )

        self.assertEqual(session_state["commercial_search_home_selected_analysis_id"], "18")

    def test_handle_navigation_selected_routes_comparison_to_existing_page(self) -> None:
        session_state: dict[str, object] = {
            SIDEBAR_USER_PAGE_KEY: PAGE_DASHBOARD,
        }

        handle_navigation_selected(
            session_state=session_state,
            target=NAVIGATION_TARGET_COMPARISON,
        )

        self.assertEqual(session_state[SIDEBAR_USER_PAGE_KEY], PAGE_COMPARISON)

    def test_handle_navigation_selected_keeps_dashboard_for_saved_analyses_until_phase_two(self) -> None:
        session_state: dict[str, object] = {
            SIDEBAR_USER_PAGE_KEY: PAGE_DASHBOARD,
        }

        handle_navigation_selected(
            session_state=session_state,
            target=NAVIGATION_TARGET_SAVED_ANALYSES,
        )

        self.assertEqual(session_state[SIDEBAR_USER_PAGE_KEY], PAGE_DASHBOARD)
        self.assertEqual(session_state["commercial_search_home_navigation_target"], NAVIGATION_TARGET_SAVED_ANALYSES)

    def test_build_search_home_page_state_defaults_to_empty_idle(self) -> None:
        state = build_search_home_page_state({})

        self.assertEqual(state.search_query, "")
        self.assertEqual(state.search_status, "idle")
        self.assertEqual(state.search_results, [])
        self.assertIsNone(state.display_error)

    def test_render_search_home_page_in_commercial_mode_does_not_render_legacy_dashboard(self) -> None:
        streamlit_mock = Mock()
        streamlit_mock.session_state = {}
        complex_repository = Mock()
        complex_repository.get.return_value = None
        analysis_repository = Mock()
        analysis_repository.list_recent.return_value = []

        with (
            patch("modules.ui.search_home_page.st", streamlit_mock),
            patch("modules.ui.search_home_page.render_dashboard_page") as legacy_dashboard_mock,
            patch("commercial_ui.component.render_commercial_ui", return_value=None) as component_mock,
        ):
            render_search_home_page(
                settings=SimpleNamespace(ui_mode="commercial"),
                complex_repository=complex_repository,
                listing_repository=Mock(),
                finance_repository=Mock(),
                analysis_repository=analysis_repository,
                policy_event_service=Mock(),
                address_search_service=Mock(),
            )

        component_mock.assert_called_once()
        legacy_dashboard_mock.assert_not_called()
        streamlit_mock.error.assert_not_called()


if __name__ == "__main__":
    unittest.main()
