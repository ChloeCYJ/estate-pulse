from __future__ import annotations

from datetime import date
import unittest

from modules.analyzers.transaction_analyzer import (
    calculate_discount_rate_vs_recent_sale_average,
    calculate_drop_rate_from_one_year_high,
    calculate_jeonse_ratio_from_rent_data,
    calculate_latest_rent_deposit_average,
    calculate_one_year_high_sale_price,
    calculate_one_year_low_sale_price,
    calculate_recent_12_month_sale_average,
    calculate_recent_3_month_sale_average,
    calculate_recent_6_month_sale_average,
)


class TransactionAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reference_date = date(2026, 5, 27)
        self.sale_transactions = [
            {"deal_date": "2025-06-15", "price": 900_000_000},
            {"deal_date": "2025-09-15", "price": 930_000_000},
            {"deal_date": "2025-12-15", "price": 960_000_000},
            {"deal_date": "2026-02-15", "price": 980_000_000},
            {"deal_date": "2026-04-15", "price": 1_000_000_000},
            {"deal_date": "2026-05-15", "price": 1_020_000_000},
        ]
        self.rent_transactions = [
            {"deal_date": "2026-01-15", "deposit": 520_000_000},
            {"deal_date": "2026-03-15", "deposit": 540_000_000},
            {"deal_date": "2026-05-10", "deposit": 560_000_000},
        ]

    def test_recent_sale_averages(self) -> None:
        self.assertEqual(
            calculate_recent_3_month_sale_average(
                self.sale_transactions, reference_date=self.reference_date
            ),
            1_010_000_000,
        )
        self.assertEqual(
            calculate_recent_6_month_sale_average(
                self.sale_transactions, reference_date=self.reference_date
            ),
            990_000_000,
        )
        self.assertEqual(
            calculate_recent_12_month_sale_average(
                self.sale_transactions, reference_date=self.reference_date
            ),
            965_000_000,
        )

    def test_one_year_high_low(self) -> None:
        self.assertEqual(
            calculate_one_year_high_sale_price(
                self.sale_transactions, reference_date=self.reference_date
            ),
            1_020_000_000,
        )
        self.assertEqual(
            calculate_one_year_low_sale_price(
                self.sale_transactions, reference_date=self.reference_date
            ),
            900_000_000,
        )

    def test_rent_and_rate_metrics(self) -> None:
        latest_rent_average = calculate_latest_rent_deposit_average(
            self.rent_transactions,
            reference_date=self.reference_date,
        )
        self.assertEqual(latest_rent_average, 540_000_000)
        self.assertAlmostEqual(
            calculate_jeonse_ratio_from_rent_data(900_000_000, latest_rent_average),
            60.0,
        )
        self.assertAlmostEqual(
            calculate_discount_rate_vs_recent_sale_average(900_000_000, 990_000_000),
            9.090909,
            places=4,
        )
        self.assertAlmostEqual(
            calculate_drop_rate_from_one_year_high(900_000_000, 1_020_000_000),
            11.764705,
            places=4,
        )


if __name__ == "__main__":
    unittest.main()
