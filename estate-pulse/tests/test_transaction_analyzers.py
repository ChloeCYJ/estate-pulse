from __future__ import annotations

from datetime import date
import unittest

from modules.analyzers.transaction_analyzer import (
    calculate_reference_price_metadata,
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

    def test_reference_price_metadata_prefers_recent_90_day_sample(self) -> None:
        metadata = calculate_reference_price_metadata(
            self.sale_transactions,
            reference_date=self.reference_date,
        )

        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["reference_price"], 1_020_000_000)
        self.assertEqual(metadata["sample_count"], 4)
        self.assertEqual(metadata["latest_transaction_date"], "2026-05-15")
        self.assertEqual(metadata["confidence"], "HIGH")
        self.assertEqual(metadata["volatility_status"], "STABLE")

    def test_reference_price_metadata_expands_window_up_to_twelve_months(self) -> None:
        sparse_transactions = [
            {"deal_date": "2026-05-15", "price": 1_020_000_000},
            {"deal_date": "2026-02-15", "price": 980_000_000},
        ]

        metadata = calculate_reference_price_metadata(
            sparse_transactions,
            reference_date=self.reference_date,
        )

        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["reference_price"], 1_020_000_000)
        self.assertEqual(metadata["sample_count"], 2)
        self.assertEqual(metadata["confidence"], "LOW")
        self.assertEqual(metadata["volatility_status"], "STABLE")

    def test_reference_price_metadata_excludes_canceled_transactions(self) -> None:
        metadata = calculate_reference_price_metadata(
            [
                {"deal_date": "2026-05-20", "price": 1_100_000_000, "is_canceled": True},
                {"deal_date": "2026-05-15", "price": 1_020_000_000},
                {"deal_date": "2026-04-15", "price": 1_000_000_000},
                {"deal_date": "2026-02-15", "price": 980_000_000},
            ],
            reference_date=self.reference_date,
        )

        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["sample_count"], 3)
        self.assertEqual(metadata["reference_price"], 1_020_000_000)
        self.assertEqual(metadata["latest_transaction_date"], "2026-05-15")

    def test_reference_price_metadata_returns_none_when_no_recent_sample_exists(self) -> None:
        stale_transactions = [
            {"deal_date": "2025-05-15", "price": 900_000_000},
        ]

        self.assertIsNone(
            calculate_reference_price_metadata(
                stale_transactions,
                reference_date=self.reference_date,
            )
        )


if __name__ == "__main__":
    unittest.main()
