from __future__ import annotations

import unittest

from modules.ui.admin_view import _group_loan_rule_rows


class AdminViewLoanGroupingTests(unittest.TestCase):
    def test_same_rule_version_purpose_and_region_are_grouped_together(self) -> None:
        rows = [
            {
                "rule_version": "2026.06-비규제-실거주-보완",
                "investment_purpose": "실거주",
                "region_type": "비규제지역",
                "buyer_type": "전체",
                "house_price_range": "15억~20억 미만",
            },
            {
                "rule_version": "2026.06-비규제-실거주-보완",
                "investment_purpose": "실거주",
                "region_type": "비규제지역",
                "buyer_type": "전체",
                "house_price_range": "20억 이상",
            },
        ]

        grouped = _group_loan_rule_rows(rows)

        self.assertEqual(len(grouped), 1)
        group_key = ("2026.06-비규제-실거주-보완", "실거주", "비규제지역")
        self.assertIn(group_key, grouped)
        self.assertEqual(len(grouped[group_key]), 2)


if __name__ == "__main__":
    unittest.main()
