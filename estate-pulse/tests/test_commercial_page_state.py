from __future__ import annotations

import unittest

from modules.ui.commercial_page_state import (
    COMMERCIAL_PAGE_STATE_KEY,
    CommercialPageState,
    load_commercial_page_state,
    save_commercial_page_state,
)


class CommercialPageStateTests(unittest.TestCase):
    def test_load_commercial_page_state_defaults_to_search_home(self) -> None:
        state = load_commercial_page_state({})

        self.assertEqual(state.commercial_page, "search_home")
        self.assertIsNone(state.analysis_source)
        self.assertIsNone(state.active_analysis_id)
        self.assertIsNone(state.active_analysis_result)
        self.assertIsNone(state.pending_analysis_request)
        self.assertIsNone(state.page_notice)
        self.assertIsNone(state.resume_action)
        self.assertIsNone(state.last_trigger)

    def test_save_and_reload_round_trips_page_notice(self) -> None:
        session_state: dict[str, object] = {}
        original = CommercialPageState(
            commercial_page="analysis_dashboard",
            analysis_source="saved",
            active_analysis_id=41,
            active_analysis_result=None,
            pending_analysis_request=None,
            page_notice={"level": "info", "code": "saved", "message": "ok"},
            last_trigger="recent_analysis_selected",
            resume_action="analysis",
        )

        save_commercial_page_state(session_state, original)
        restored = load_commercial_page_state(session_state)

        self.assertIn(COMMERCIAL_PAGE_STATE_KEY, session_state)
        self.assertNotIn("fallback_to_legacy", session_state[COMMERCIAL_PAGE_STATE_KEY])
        self.assertEqual(restored.commercial_page, "analysis_dashboard")
        self.assertEqual(restored.analysis_source, "saved")
        self.assertEqual(restored.active_analysis_id, 41)
        self.assertEqual(restored.page_notice["code"], "saved")
        self.assertEqual(restored.last_trigger, "recent_analysis_selected")
        self.assertEqual(restored.resume_action, "analysis")

    def test_finance_profile_route_round_trips(self) -> None:
        session_state: dict[str, object] = {}
        save_commercial_page_state(
            session_state,
            CommercialPageState(
                commercial_page="finance_profile",
                resume_action="finance_profile",
            ),
        )

        restored = load_commercial_page_state(session_state)

        self.assertEqual(restored.commercial_page, "finance_profile")
        self.assertEqual(restored.resume_action, "finance_profile")


if __name__ == "__main__":
    unittest.main()
