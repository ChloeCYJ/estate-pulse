from __future__ import annotations

from datetime import date
import unittest

from config.loan_rules import LoanRule
from modules.analyzers.loan_analyzer import calculate_loan_terms, select_loan_rule


class LoanAnalyzerRuleTests(unittest.TestCase):
    def test_selects_under_900m_bracket(self) -> None:
        rule = select_loan_rule(
            sale_price=850_000_000,
            region_type="NON_REGULATED",
            buyer_type="NO_HOME",
            purpose="INVESTMENT",
            reference_date=date(2026, 5, 28),
        )

        self.assertEqual(rule.rule_version, "2026.05-v2")
        self.assertEqual(rule.house_price_min, 0)
        self.assertEqual(rule.house_price_max, 899_999_999)
        self.assertEqual(rule.ltv_rate, 0.70)
        self.assertIsNone(rule.max_loan_amount)

    def test_selects_900m_to_1_5b_bracket(self) -> None:
        rule = select_loan_rule(
            sale_price=1_200_000_000,
            region_type="NON_REGULATED",
            buyer_type="NO_HOME",
            purpose="INVESTMENT",
            reference_date=date(2026, 5, 28),
        )

        self.assertEqual(rule.house_price_min, 900_000_000)
        self.assertEqual(rule.house_price_max, 1_499_999_999)
        self.assertEqual(rule.ltv_rate, 0.60)

    def test_selects_1_5b_to_2_5b_bracket(self) -> None:
        rule = select_loan_rule(
            sale_price=2_000_000_000,
            region_type="NON_REGULATED",
            buyer_type="NO_HOME",
            purpose="INVESTMENT",
            reference_date=date(2026, 5, 28),
        )

        self.assertEqual(rule.house_price_min, 1_500_000_000)
        self.assertEqual(rule.house_price_max, 2_499_999_999)
        self.assertEqual(rule.ltv_rate, 0.50)
        self.assertEqual(rule.max_loan_amount, 1_000_000_000)

    def test_selects_over_2_5b_bracket(self) -> None:
        rule = select_loan_rule(
            sale_price=2_600_000_000,
            region_type="NON_REGULATED",
            buyer_type="NO_HOME",
            purpose="INVESTMENT",
            reference_date=date(2026, 5, 28),
        )

        self.assertEqual(rule.house_price_min, 2_500_000_000)
        self.assertIsNone(rule.house_price_max)
        self.assertEqual(rule.ltv_rate, 0.40)
        self.assertEqual(rule.max_loan_amount, 1_200_000_000)

    def test_max_loan_amount_cap_is_applied(self) -> None:
        loan_terms = calculate_loan_terms(
            sale_price=2_000_000_000,
            region_type="REGULATED",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            reference_date=date(2026, 5, 28),
        )

        self.assertEqual(loan_terms["loan_amount_by_ltv"], 600_000_000)
        self.assertEqual(loan_terms["max_loan_amount"], 600_000_000)
        self.assertEqual(loan_terms["final_loan_amount"], 600_000_000)

    def test_specific_region_type_falls_back_to_regulated_rule(self) -> None:
        loan_terms = calculate_loan_terms(
            sale_price=2_000_000_000,
            region_type="LAND_TRANSACTION_PERMISSION",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            reference_date=date(2026, 5, 28),
        )

        self.assertEqual(loan_terms["region_type"], "REGULATED")
        self.assertEqual(loan_terms["final_loan_amount"], 600_000_000)

    def test_specific_region_rule_is_preferred_over_generic_regulated_rule(self) -> None:
        rules = [
            LoanRule(
                rule_version="generic-regulated",
                effective_from="2026-05-01",
                effective_to=None,
                region_type="REGULATED",
                buyer_type="NO_HOME",
                purpose="OWNER_OCCUPIED",
                house_price_min=1_500_000_000,
                house_price_max=1_999_999_999,
                ltv_rate=0.40,
                dsr_rate=0.40,
                max_loan_amount=600_000_000,
                description="generic regulated",
            ),
            LoanRule(
                rule_version="land-permission-15-20b",
                effective_from="2026-05-01",
                effective_to=None,
                region_type="LAND_TRANSACTION_PERMISSION",
                buyer_type="NO_HOME",
                purpose="OWNER_OCCUPIED",
                house_price_min=1_500_000_000,
                house_price_max=1_999_999_999,
                ltv_rate=0.40,
                dsr_rate=0.40,
                max_loan_amount=400_000_000,
                description="15억 이상 20억 미만 토허제 4억 제한",
            ),
        ]

        loan_terms = calculate_loan_terms(
            sale_price=1_800_000_000,
            region_type="LAND_TRANSACTION_PERMISSION",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            reference_date=date(2026, 6, 3),
            rules=rules,
        )

        self.assertEqual(loan_terms["rule_version"], "land-permission-15-20b")
        self.assertEqual(loan_terms["max_loan_amount"], 400_000_000)
        self.assertEqual(loan_terms["final_loan_amount"], 400_000_000)

    def test_all_buyer_type_rule_is_used_when_specific_rule_is_missing(self) -> None:
        rules = [
            LoanRule(
                rule_version="all-buyer-type",
                effective_from="2026-05-01",
                effective_to=None,
                region_type="NON_REGULATED",
                buyer_type="ALL",
                purpose="OWNER_OCCUPIED",
                house_price_min=0,
                house_price_max=899_999_999,
                ltv_rate=0.65,
                dsr_rate=0.40,
                max_loan_amount=None,
                description="all buyer type",
            ),
        ]

        loan_terms = calculate_loan_terms(
            sale_price=850_000_000,
            region_type="NON_REGULATED",
            buyer_type="ONE_HOME",
            purpose="OWNER_OCCUPIED",
            reference_date=date(2026, 6, 3),
            rules=rules,
        )

        self.assertEqual(loan_terms["rule_version"], "all-buyer-type")
        self.assertEqual(loan_terms["buyer_type"], "ALL")

    def test_specific_buyer_type_rule_is_preferred_over_all(self) -> None:
        rules = [
            LoanRule(
                rule_version="all-buyer-type",
                effective_from="2026-05-01",
                effective_to=None,
                region_type="NON_REGULATED",
                buyer_type="ALL",
                purpose="OWNER_OCCUPIED",
                house_price_min=0,
                house_price_max=899_999_999,
                ltv_rate=0.65,
                dsr_rate=0.40,
                max_loan_amount=None,
                description="all buyer type",
            ),
            LoanRule(
                rule_version="one-home-specific",
                effective_from="2026-05-01",
                effective_to=None,
                region_type="NON_REGULATED",
                buyer_type="ONE_HOME",
                purpose="OWNER_OCCUPIED",
                house_price_min=0,
                house_price_max=899_999_999,
                ltv_rate=0.55,
                dsr_rate=0.40,
                max_loan_amount=None,
                description="one home specific",
            ),
        ]

        loan_terms = calculate_loan_terms(
            sale_price=850_000_000,
            region_type="NON_REGULATED",
            buyer_type="ONE_HOME",
            purpose="OWNER_OCCUPIED",
            reference_date=date(2026, 6, 3),
            rules=rules,
        )

        self.assertEqual(loan_terms["rule_version"], "one-home-specific")
        self.assertEqual(loan_terms["buyer_type"], "ONE_HOME")

    def test_unlimited_max_loan_amount_uses_ltv_limit(self) -> None:
        loan_terms = calculate_loan_terms(
            sale_price=850_000_000,
            region_type="NON_REGULATED",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            reference_date=date(2026, 5, 28),
        )

        self.assertEqual(loan_terms["max_loan_amount"], None)
        self.assertEqual(loan_terms["loan_amount_by_ltv"], 595_000_000)
        self.assertEqual(loan_terms["final_loan_amount"], 595_000_000)

    def test_manual_override_is_applied_as_upper_bound(self) -> None:
        loan_terms = calculate_loan_terms(
            sale_price=1_200_000_000,
            region_type="REGULATED",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            reference_date=date(2026, 5, 28),
            ltv_rate_override=0.55,
            final_loan_amount_override=550_000_000,
        )

        self.assertEqual(loan_terms["applied_ltv_rate"], 0.55)
        self.assertEqual(loan_terms["policy_capped_loan_amount"], 600_000_000)
        self.assertEqual(loan_terms["final_loan_amount"], 550_000_000)
        self.assertEqual(loan_terms["ltv_source"], "manual override")
        self.assertEqual(loan_terms["loan_amount_source"], "manual override")

    def test_dsr_limit_can_reduce_final_loan_amount(self) -> None:
        loan_terms = calculate_loan_terms(
            sale_price=850_000_000,
            region_type="NON_REGULATED",
            buyer_type="NO_HOME",
            purpose="OWNER_OCCUPIED",
            reference_date=date(2026, 5, 28),
            annual_income=60_000_000,
            existing_debt=100_000_000,
            annual_interest_rate=0.04,
        )

        self.assertLess(loan_terms["dsr_based_loan_limit"], loan_terms["loan_amount_by_ltv"])
        self.assertEqual(loan_terms["final_loan_amount"], loan_terms["dsr_based_loan_limit"])


if __name__ == "__main__":
    unittest.main()
