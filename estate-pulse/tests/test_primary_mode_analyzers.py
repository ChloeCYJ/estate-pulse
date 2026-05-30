from __future__ import annotations

import unittest

from modules.analyzers.investment_analyzer import calculate_investment_metrics
from modules.analyzers.owner_occupied_analyzer import calculate_owner_occupied_metrics


class PrimaryModeAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.acquisition_cost_total = 23_300_000

    def test_owner_occupied_metrics_include_affordability_and_repayment(self) -> None:
        result = calculate_owner_occupied_metrics(
            sale_price=900_000_000,
            estimated_loan=300_000_000,
            acquisition_cost_total=self.acquisition_cost_total,
            cash_amount=700_000_000,
            annual_income=120_000_000,
            annual_interest_rate=0.04,
        )

        self.assertEqual(result["required_cash"], 623_300_000)
        self.assertEqual(result["shortage_cash"], -76_700_000)
        self.assertEqual(result["remaining_cash_after_purchase"], 76_700_000)
        self.assertEqual(result["monthly_repayment"], 1_432_246)
        self.assertAlmostEqual(result["dsr"], 14.32246, places=4)

    def test_gap_investment_metrics_include_gap_amount_and_efficiency(self) -> None:
        result = calculate_investment_metrics(
            investment_type="GAP_INVESTMENT",
            sale_price=900_000_000,
            estimated_loan=300_000_000,
            acquisition_cost_total=self.acquisition_cost_total,
            expected_jeonse_price=400_000_000,
        )

        self.assertEqual(result["required_cash"], 223_300_000)
        self.assertEqual(result["gap_amount"], 500_000_000)
        self.assertAlmostEqual(result["estimated_investment_efficiency"], 4.03, places=2)

    def test_jeonse_takeover_metrics_use_takeover_deposit(self) -> None:
        result = calculate_investment_metrics(
            investment_type="JEONSE_TAKEOVER",
            sale_price=900_000_000,
            estimated_loan=300_000_000,
            acquisition_cost_total=self.acquisition_cost_total,
            takeover_jeonse_deposit=350_000_000,
        )

        self.assertEqual(result["required_cash"], 273_300_000)
        self.assertEqual(result["gap_amount"], 550_000_000)

    def test_monthly_rent_metrics_keep_monthly_cash_flow(self) -> None:
        result = calculate_investment_metrics(
            investment_type="MONTHLY_RENT",
            sale_price=900_000_000,
            estimated_loan=300_000_000,
            acquisition_cost_total=self.acquisition_cost_total,
            rent_deposit=100_000_000,
            expected_monthly_rent=2_000_000,
        )

        self.assertEqual(result["required_cash"], 523_300_000)
        self.assertEqual(result["gap_amount"], 800_000_000)
        self.assertEqual(result["monthly_cash_flow"], 2_000_000)


if __name__ == "__main__":
    unittest.main()
