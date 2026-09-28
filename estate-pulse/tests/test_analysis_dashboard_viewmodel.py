from __future__ import annotations

import unittest

from modules.ui.viewmodels.analysis_dashboard import (
    build_analysis_dashboard_view_model_from_live_result,
)


class AnalysisDashboardViewModelTests(unittest.TestCase):
    def test_build_analysis_dashboard_view_model_preserves_none_vs_zero(self) -> None:
        result = {
            "analysis_id": 41,
            "complex_id": 7,
            "complex_name": "Test Complex",
            "area_bucket": 84.9,
            "sale_price": 990_000_000,
            "price_source": "TRANSACTION_REFERENCE",
            "required_cash": 250_000_000,
            "shortage_cash": 0,
            "expected_loan_amount": 540_000_000,
            "monthly_repayment": None,
            "decision": "affordable",
            "summary": "summary",
            "risks": [],
            "reasons": [],
            "costs": {
                "acquisition_tax": 0,
                "brokerage_fee": 0,
                "total_transaction_cost": 0,
            },
            "reference_price_metadata": {},
        }

        view_model = build_analysis_dashboard_view_model_from_live_result(result)

        self.assertEqual(view_model["page_status"], "ready")
        self.assertEqual(view_model["property"]["analysis_id"], "41")
        self.assertEqual(view_model["financing"]["cash_shortfall"]["value"], 0)
        self.assertIsNone(view_model["financing"]["monthly_payment"]["value"])
if __name__ == "__main__":
    unittest.main()
