from __future__ import annotations

import unittest

from modules.analyzers.cash_flow_analyzer import (
    calculate_acquisition_cost_total,
    calculate_investment_scenario_cash,
)


class InvestmentScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.acquisition_cost_total = calculate_acquisition_cost_total(
            acquisition_tax=9_900_000,
            brokerage_fee=3_600_000,
            legal_fee=300_000,
            repair_cost=5_000_000,
            contingency_fee=4_500_000,
        )

    def test_owner_occupied_required_cash(self) -> None:
        result = calculate_investment_scenario_cash(
            investment_type="OWNER_OCCUPIED",
            sale_price=900_000_000,
            estimated_loan=300_000_000,
            acquisition_cost_total=self.acquisition_cost_total,
            expected_jeonse_price=400_000_000,
        )
        self.assertEqual(result["required_cash"], 623_300_000)

    def test_gap_investment_required_cash(self) -> None:
        result = calculate_investment_scenario_cash(
            investment_type="GAP_INVESTMENT",
            sale_price=900_000_000,
            estimated_loan=300_000_000,
            acquisition_cost_total=self.acquisition_cost_total,
            expected_jeonse_price=400_000_000,
        )
        self.assertEqual(result["required_cash"], 223_300_000)

    def test_jeonse_takeover_required_cash(self) -> None:
        result = calculate_investment_scenario_cash(
            investment_type="JEONSE_TAKEOVER",
            sale_price=900_000_000,
            estimated_loan=300_000_000,
            acquisition_cost_total=self.acquisition_cost_total,
            takeover_jeonse_deposit=350_000_000,
        )
        self.assertEqual(result["required_cash"], 273_300_000)

    def test_monthly_rent_cash_flow(self) -> None:
        result = calculate_investment_scenario_cash(
            investment_type="MONTHLY_RENT",
            sale_price=900_000_000,
            estimated_loan=300_000_000,
            acquisition_cost_total=self.acquisition_cost_total,
            rent_deposit=100_000_000,
            expected_monthly_rent=2_000_000,
        )
        self.assertEqual(result["required_cash"], 523_300_000)
        self.assertEqual(result["monthly_cash_flow"], 2_000_000)

    def test_future_move_in_split_cash_calculation(self) -> None:
        result = calculate_investment_scenario_cash(
            investment_type="FUTURE_MOVE_IN",
            sale_price=900_000_000,
            estimated_loan=300_000_000,
            acquisition_cost_total=self.acquisition_cost_total,
            expected_jeonse_price=400_000_000,
        )
        self.assertEqual(result["required_cash"], 223_300_000)
        self.assertEqual(result["current_required_cash"], 223_300_000)
        self.assertEqual(result["future_required_cash"], 623_300_000)


if __name__ == "__main__":
    unittest.main()
