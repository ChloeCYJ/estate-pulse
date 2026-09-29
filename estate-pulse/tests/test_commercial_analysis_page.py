from __future__ import annotations

from unittest.mock import Mock, patch
import unittest

from modules.ui.commercial_page_state import (
    CommercialPageState,
    load_commercial_page_state,
    save_commercial_page_state,
)


class CommercialAnalysisPageTests(unittest.TestCase):
    def test_handle_save_requested_promotes_live_result_to_saved_snapshot(self) -> None:
        from modules.ui.commercial_analysis_page import handle_save_requested

        session_state: dict[str, object] = {}
        live_result = {
            "complex_id": 7,
            "complex_name": "Test Complex",
            "area_bucket": 84.9,
            "sale_price": 990_000_000,
            "required_cash": 250_000_000,
            "shortage_cash": 0,
            "expected_loan_amount": 540_000_000,
            "monthly_repayment": None,
            "decision": "affordable",
            "summary": "summary",
        }
        save_commercial_page_state(
            session_state,
            CommercialPageState(
                commercial_page="analysis_dashboard",
                analysis_source="live",
                active_analysis_result=live_result,
                last_trigger="analysis_requested",
            ),
        )

        analysis_service = Mock()
        analysis_service.save_completed_analysis_result.return_value = 41
        analysis_repository = Mock()
        analysis_repository.get_by_id_for_user.return_value = {
            "id": 41,
            "complex_name_snapshot": "Test Complex",
            "area_bucket": 84.9,
            "sale_price_snapshot": 990_000_000,
            "required_cash": 250_000_000,
            "shortage_cash": 0,
            "expected_loan_amount": 540_000_000,
            "monthly_repayment": None,
            "decision": "affordable",
            "summary": "summary",
        }

        state = handle_save_requested(
            session_state=session_state,
            analysis_service=analysis_service,
            analysis_repository=analysis_repository,
            user_id=11,
        )

        analysis_service.save_completed_analysis_result.assert_called_once_with(
            live_result,
            user_id=11,
        )
        analysis_repository.get_by_id_for_user.assert_called_once_with(
            analysis_id=41,
            user_id=11,
        )
        self.assertEqual(state.analysis_source, "saved")
        self.assertEqual(state.active_analysis_id, 41)
        self.assertEqual(state.active_analysis_result, live_result)
        self.assertEqual(state.last_trigger, "save_requested")
        self.assertEqual(load_commercial_page_state(session_state).analysis_source, "saved")

    def test_render_commercial_analysis_page_keeps_active_result_when_component_raises(self) -> None:
        from modules.ui.commercial_analysis_page import render_commercial_analysis_page

        streamlit_mock = Mock()
        streamlit_mock.session_state = {}
        streamlit_mock.button.side_effect = [False, False]
        active_result = {
            "analysis_id": 12,
            "complex_id": 7,
            "complex_name": "Test Complex",
            "area_bucket": 84.9,
            "sale_price": 990_000_000,
            "required_cash": 250_000_000,
            "shortage_cash": 0,
            "expected_loan_amount": 540_000_000,
            "monthly_repayment": None,
            "decision": "affordable",
            "summary": "summary",
            "risks": [],
        }
        save_commercial_page_state(
            streamlit_mock.session_state,
            CommercialPageState(
                commercial_page="analysis_dashboard",
                analysis_source="live",
                active_analysis_id=12,
                active_analysis_result=active_result,
                last_trigger="analysis_requested",
            ),
        )

        with (
            patch("modules.ui.commercial_analysis_page.st", streamlit_mock),
            patch(
                "modules.ui.commercial_analysis_page.render_commercial_ui",
                side_effect=RuntimeError("boom"),
            ),
            patch("modules.ui.commercial_analysis_page.LOGGER") as logger_mock,
        ):
            render_commercial_analysis_page(
                analysis_repository=Mock(),
                analysis_service=Mock(),
            )

        state = load_commercial_page_state(streamlit_mock.session_state)
        self.assertEqual(state.active_analysis_result, active_result)
        streamlit_mock.error.assert_called_once()
        streamlit_mock.button.assert_any_call("다시 시도", key="commercial-analysis-retry")
        streamlit_mock.button.assert_any_call(
            "단지 검색으로 돌아가기",
            key="commercial-analysis-back",
        )
        logger_mock.exception.assert_called_once()


if __name__ == "__main__":
    unittest.main()
