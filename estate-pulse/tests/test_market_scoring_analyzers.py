from __future__ import annotations

from datetime import date
import unittest

from modules.analyzers.complex_grade_analyzer import calculate_complex_grade
from modules.analyzers.liquidity_analyzer import calculate_liquidity_score


class MarketScoringAnalyzerTests(unittest.TestCase):
    def test_liquidity_score_high_band(self) -> None:
        reference_date = date(2026, 5, 30)
        sale_transactions = [
            {"deal_date": "2025-06-05", "price": 890_000_000},
            {"deal_date": "2025-07-05", "price": 895_000_000},
            {"deal_date": "2025-08-05", "price": 900_000_000},
            {"deal_date": "2025-09-05", "price": 905_000_000},
            {"deal_date": "2025-10-05", "price": 910_000_000},
            {"deal_date": "2025-11-05", "price": 915_000_000},
            {"deal_date": "2025-12-05", "price": 920_000_000},
            {"deal_date": "2026-01-05", "price": 925_000_000},
            {"deal_date": "2026-02-05", "price": 930_000_000},
            {"deal_date": "2026-03-05", "price": 935_000_000},
            {"deal_date": "2026-04-05", "price": 940_000_000},
            {"deal_date": "2026-05-05", "price": 945_000_000},
        ]
        rent_transactions = [
            {"deal_date": "2025-06-10", "deposit": 430_000_000},
            {"deal_date": "2025-07-10", "deposit": 432_000_000},
            {"deal_date": "2025-08-10", "deposit": 434_000_000},
            {"deal_date": "2025-09-10", "deposit": 436_000_000},
            {"deal_date": "2025-10-10", "deposit": 438_000_000},
            {"deal_date": "2025-11-10", "deposit": 440_000_000},
            {"deal_date": "2025-12-10", "deposit": 442_000_000},
            {"deal_date": "2026-01-10", "deposit": 444_000_000},
            {"deal_date": "2026-02-10", "deposit": 446_000_000},
            {"deal_date": "2026-03-10", "deposit": 448_000_000},
            {"deal_date": "2026-04-10", "deposit": 450_000_000},
            {"deal_date": "2026-05-10", "deposit": 452_000_000},
        ]

        result = calculate_liquidity_score(
            sale_transactions=sale_transactions,
            rent_transactions=rent_transactions,
            reference_date=reference_date,
        )

        self.assertGreaterEqual(result["score"], 80)
        self.assertEqual(result["band"], "HIGH")

    def test_complex_grade_leader(self) -> None:
        result = calculate_complex_grade(
            household_count=1800,
            building_age=8,
            recent_sale_transaction_count=20,
            recent_rent_transaction_count=18,
            average_sale_price_rank=1,
            price_per_area_rank=1,
            region_complex_count=8,
            liquidity_score=92,
        )

        self.assertEqual(result["grade"], "LEADER")
        self.assertEqual(result["label"], "대장")


if __name__ == "__main__":
    unittest.main()
