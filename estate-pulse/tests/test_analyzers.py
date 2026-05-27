from __future__ import annotations

import unittest

from modules.analyzers.bargain_analyzer import calculate_bargain_score
from modules.analyzers.cash_flow_analyzer import (
    calculate_jeonse_ratio,
    calculate_required_cash,
    calculate_shortage_cash,
)


class AnalyzerTests(unittest.TestCase):
    def test_required_cash(self) -> None:
        required_cash = calculate_required_cash(
            sale_price=900_000_000,
            expected_loan_amount=300_000_000,
            expected_jeonse_price=400_000_000,
            acquisition_tax=9_900_000,
            brokerage_fee=3_600_000,
            legal_fee=300_000,
            repair_cost=5_000_000,
            contingency_fee=4_500_000,
        )
        self.assertEqual(required_cash, 223_300_000)

    def test_shortage_cash(self) -> None:
        self.assertEqual(calculate_shortage_cash(250_000_000, 200_000_000), 50_000_000)

    def test_jeonse_ratio(self) -> None:
        self.assertAlmostEqual(calculate_jeonse_ratio(420_000_000, 700_000_000), 60.0)

    def test_bargain_score(self) -> None:
        result = calculate_bargain_score(
            sale_price=700_000_000,
            recent_avg_price=780_000_000,
            one_year_high_price=900_000_000,
            expected_jeonse_price=490_000_000,
            required_cash=150_000_000,
            user_cash=200_000_000,
        )
        self.assertEqual(result["score"], 80)
        self.assertEqual(result["grade"], "강한 급매 후보")


if __name__ == "__main__":
    unittest.main()
