from __future__ import annotations

import unittest

from modules.analyzers.brokerage_analyzer import calculate_brokerage_breakdown
from modules.analyzers.tax_analyzer import calculate_tax_breakdown


class TransactionCostAnalyzerTests(unittest.TestCase):
    def test_default_transaction_cost_breakdowns(self) -> None:
        tax_breakdown = calculate_tax_breakdown(sale_price=900_000_000)
        brokerage_breakdown = calculate_brokerage_breakdown(sale_price=900_000_000)

        self.assertEqual(tax_breakdown["acquisition_tax"], 18_000_000)
        self.assertEqual(tax_breakdown["local_education_tax"], 1_800_000)
        self.assertEqual(tax_breakdown["applied_tax_rule_version"], "2026.05-estimate")
        self.assertEqual(brokerage_breakdown["brokerage_fee"], 4_500_000)
        self.assertEqual(brokerage_breakdown["legal_fee"], 300_000)
        self.assertEqual(brokerage_breakdown["reserve_cost"], 4_500_000)
        self.assertEqual(
            brokerage_breakdown["applied_brokerage_rule_version"],
            "2026.05-estimate",
        )

    def test_manual_override_marks_rule_version(self) -> None:
        tax_breakdown = calculate_tax_breakdown(
            sale_price=900_000_000,
            acquisition_tax_override=11_000_000,
        )
        brokerage_breakdown = calculate_brokerage_breakdown(
            sale_price=900_000_000,
            brokerage_fee_override=3_000_000,
            legal_fee_override=500_000,
        )

        self.assertEqual(tax_breakdown["acquisition_tax"], 11_000_000)
        self.assertEqual(tax_breakdown["applied_tax_rule_version"], "2026.05-estimate+manual")
        self.assertEqual(brokerage_breakdown["brokerage_fee"], 3_000_000)
        self.assertEqual(brokerage_breakdown["legal_fee"], 500_000)
        self.assertEqual(
            brokerage_breakdown["applied_brokerage_rule_version"],
            "2026.05-estimate+manual",
        )


if __name__ == "__main__":
    unittest.main()
