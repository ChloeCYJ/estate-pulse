import unittest

from modules.ui.analysis_view import (
    _cash_judgment,
    _complex_grade_label,
    _display_value,
    _high_interest_rate_warning,
    _liquidity_label,
    _loan_region_type_label,
    _missing_metric_reason,
    _region_policy_type_label,
    _scenario_interpretation_lines,
    _scenario_limited_impact_lines,
    _scenario_score_line,
    _source_label,
)


class AnalysisViewLabelTests(unittest.TestCase):
    def test_complex_grade_codes_are_translated(self) -> None:
        self.assertEqual(_complex_grade_label("LEADER"), "대장")
        self.assertEqual(_complex_grade_label("SUB_LEADER"), "준대장")
        self.assertEqual(_complex_grade_label("GENERAL"), "일반")
        self.assertEqual(_complex_grade_label(None), "-")

    def test_liquidity_codes_are_translated(self) -> None:
        self.assertEqual(_liquidity_label("high liquidity"), "유동성 높음")
        self.assertEqual(_liquidity_label("medium liquidity"), "유동성 보통")
        self.assertEqual(_liquidity_label("low liquidity"), "유동성 낮음")
        self.assertEqual(_liquidity_label(None), "정보 없음")

    def test_region_codes_are_translated(self) -> None:
        self.assertEqual(_loan_region_type_label("NON_REGULATED"), "비규제지역")
        self.assertEqual(_loan_region_type_label("REGULATED"), "공통 규제 규칙")
        self.assertEqual(_region_policy_type_label("ADJUSTMENT_TARGET"), "조정대상지역")
        self.assertEqual(_region_policy_type_label("SPECULATION_OVERHEATED"), "투기과열지구")
        self.assertEqual(
            _region_policy_type_label("LAND_TRANSACTION_PERMISSION"),
            "토지거래허가구역",
        )

    def test_none_like_values_are_hidden_from_user_labels(self) -> None:
        self.assertEqual(_display_value(None), "-")
        self.assertEqual(_display_value("None"), "-")
        self.assertEqual(_source_label("manual override"), "수동 보정")
        self.assertEqual(_source_label("region_policy_status"), "지역 규제 상태")

    def test_cash_judgment_uses_available_cash_and_required_cash(self) -> None:
        judgment = _cash_judgment(
            {
                "required_cash": 490_000_000,
                "purchase_power": {"available_cash_for_purchase": 200_000_000},
            }
        )

        self.assertFalse(judgment["can_purchase"])
        self.assertEqual(judgment["available_cash"], 200_000_000)
        self.assertEqual(judgment["required_cash"], 490_000_000)
        self.assertEqual(judgment["additional_cash_required"], 290_000_000)
        self.assertEqual(judgment["cash_balance_after_purchase"], -290_000_000)

    def test_cash_judgment_reports_cash_balance_when_purchase_is_possible(self) -> None:
        judgment = _cash_judgment(
            {
                "required_cash": 490_000_000,
                "purchase_power": {"available_cash_for_purchase": 600_000_000},
            }
        )

        self.assertTrue(judgment["can_purchase"])
        self.assertEqual(judgment["additional_cash_required"], 0)
        self.assertEqual(judgment["cash_balance_after_purchase"], 110_000_000)

    def test_missing_metric_reason_explains_unavailable_repayment_metrics(self) -> None:
        self.assertEqual(
            _missing_metric_reason("monthly_repayment", None),
            "금리 정보가 없어 계산하지 않았습니다.",
        )
        self.assertEqual(
            _missing_metric_reason("dsr", None),
            "연소득 정보가 없어 계산하지 않았습니다.",
        )
        self.assertEqual(
            _missing_metric_reason(
                "dsr",
                None,
                explicit_reason="실거주 분석에서만 계산합니다.",
            ),
            "실거주 분석에서만 계산합니다.",
        )
        self.assertIsNone(_missing_metric_reason("dsr", 35.0))

    def test_high_interest_rate_warning_is_shown_for_extreme_rate(self) -> None:
        warning = _high_interest_rate_warning(
            {
                "applied_rules": {
                    "monthly_repayment": {
                        "annual_interest_rate": 0.40,
                    }
                }
            }
        )

        self.assertIn("40.0%", warning)

    def test_high_interest_rate_warning_is_hidden_for_normal_rate(self) -> None:
        self.assertIsNone(
            _high_interest_rate_warning(
                {
                    "applied_rules": {
                        "monthly_repayment": {
                            "annual_interest_rate": 0.04,
                        }
                    }
                }
            )
        )

    def test_scenario_ltv_no_change_reason_uses_limiting_factor(self) -> None:
        lines = _scenario_limited_impact_lines(
            baseline_result={"expected_loan_amount": 400_000_000, "shortage_cash": 700_000_000},
            scenario_result={
                "expected_loan_amount": 400_000_000,
                "shortage_cash": 700_000_000,
                "applied_rules": {
                    "loan_ltv": {
                        "final_limiting_factor": "가격구간 최대한도",
                    }
                },
            },
            jeonse_price_change_pct=0,
            ltv_change_pct=6,
        )

        self.assertEqual(len(lines), 1)
        self.assertIn("가격구간 최대한도", lines[0])

    def test_scenario_jeonse_no_change_reason_for_owner_occupied(self) -> None:
        lines = _scenario_limited_impact_lines(
            baseline_result={"expected_loan_amount": 400_000_000, "shortage_cash": 700_000_000},
            scenario_result={
                "expected_loan_amount": 400_000_000,
                "shortage_cash": 700_000_000,
                "primary_user_mode": "OWNER_OCCUPIED",
            },
            jeonse_price_change_pct=3,
            ltv_change_pct=0,
        )

        self.assertEqual(len(lines), 1)
        self.assertIn("실거주 기준 분석", lines[0])

    def test_scenario_score_line_explains_unchanged_score(self) -> None:
        line = _scenario_score_line(
            baseline_result={"investment_score": 22},
            scenario_result={"investment_score": 22},
            has_input_changes=True,
        )

        self.assertIn("주요 점수 구간이 바뀌지 않아", line)

    def test_interest_rate_interpretation_separates_loan_and_repayment_effects(self) -> None:
        lines = _scenario_interpretation_lines(
            baseline_result={
                "expected_loan_amount": 400_000_000,
                "shortage_cash": 800_000_000,
                "investment_score": 22,
                "monthly_repayment": 2_000_000,
                "applied_rules": {"monthly_repayment": {"annual_interest_rate": 0.04}},
            },
            scenario_result={
                "expected_loan_amount": 85_680_000,
                "shortage_cash": 1_114_320_000,
                "investment_score": 22,
                "monthly_repayment": 1_480_000,
                "applied_rules": {"monthly_repayment": {"annual_interest_rate": 0.045}},
            },
            sale_price_change_pct=0,
            jeonse_price_change_pct=0,
            interest_rate_change_pct=0.5,
            ltv_change_pct=0,
        )

        self.assertTrue(any("은행 대출 가능액" in line for line in lines))
        self.assertTrue(any("기존 대출금 유지 시 월 부담" in line for line in lines))
        self.assertTrue(any("은행 승인액 기준 월 부담" in line for line in lines))

    def test_scenario_interpretation_uses_result_summary_once(self) -> None:
        lines = _scenario_interpretation_lines(
            baseline_result={
                "expected_loan_amount": 400_000_000,
                "shortage_cash": 800_000_000,
                "investment_score": 23,
                "monthly_repayment": 2_000_000,
                "applied_rules": {"monthly_repayment": {"annual_interest_rate": 0.04}},
            },
            scenario_result={
                "expected_loan_amount": 400_000_000,
                "shortage_cash": 718_490_000,
                "investment_score": 23,
                "monthly_repayment": 1_850_000,
                "applied_rules": {"monthly_repayment": {"annual_interest_rate": 0.035}},
            },
            sale_price_change_pct=-3,
            jeonse_price_change_pct=4,
            interest_rate_change_pct=-0.5,
            ltv_change_pct=6,
        )

        self.assertTrue(any("추가 준비 현금이 약" in line for line in lines))
        self.assertFalse(any("매매가가" in line for line in lines))
        self.assertFalse(any("전세가가" in line for line in lines))

    def test_scenario_limited_impact_lines_are_capped_to_two(self) -> None:
        lines = _scenario_limited_impact_lines(
            baseline_result={"expected_loan_amount": 400_000_000, "shortage_cash": 700_000_000},
            scenario_result={
                "expected_loan_amount": 400_000_000,
                "shortage_cash": 700_000_000,
                "primary_user_mode": "OWNER_OCCUPIED",
                "applied_rules": {
                    "loan_ltv": {
                        "final_limiting_factor": "가격구간 최대한도",
                    }
                },
            },
            jeonse_price_change_pct=3,
            ltv_change_pct=6,
        )

        self.assertLessEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
