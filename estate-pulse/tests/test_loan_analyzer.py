from __future__ import annotations

from datetime import date
import unittest

from modules.analyzers.loan_analyzer import calculate_loan_terms, select_loan_rule


class LoanAnalyzerRuleTests(unittest.TestCase):
    def test_selects_non_regulated_rule_by_price_band(self) -> None:
        rule = select_loan_rule(
            sale_price=850_000_000,
            region_type="NON_REGULATED",
            buyer_type="NO_HOME",
            purpose="INVESTMENT",
            reference_date=date(2026, 5, 28),
        )

        self.assertEqual(rule.rule_version, "2026.05-v1")
        self.assertEqual(rule.ltv_rate, 0.70)

    def test_selects_regulated_rule_by_buyer_type(self) -> None:
        rule = select_loan_rule(
            sale_price=1_200_000_000,
            region_type="REGULATED",
            buyer_type="ONE_HOME",
            purpose="INVESTMENT",
            reference_date=date(2026, 5, 28),
        )

        self.assertEqual(rule.ltv_rate, 0.30)
        self.assertEqual(rule.max_loan_amount, 400_000_000)

    def test_applies_manual_overrides(self) -> None:
        loan_terms = calculate_loan_terms(
            sale_price=1_200_000_000,
            region_type="REGULATED",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            reference_date=date(2026, 5, 28),
            ltv_rate_override=0.55,
            final_loan_amount_override=700_000_000,
        )

        self.assertEqual(loan_terms["rule_version"], "2026.05-v1")
        self.assertEqual(loan_terms["applied_ltv_rate"], 0.55)
        self.assertEqual(loan_terms["final_loan_amount"], 700_000_000)
        self.assertEqual(loan_terms["ltv_source"], "수동 입력")
        self.assertEqual(loan_terms["loan_amount_source"], "수동 입력")


if __name__ == "__main__":
    unittest.main()
