import unittest

from modules.ui.analysis_view import (
    _cash_judgment,
    _complex_grade_label,
    _display_value,
    _liquidity_label,
    _loan_region_type_label,
    _missing_metric_reason,
    _region_policy_type_label,
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
            "금리 또는 대출기간 정보가 없어 계산하지 않았습니다.",
        )
        self.assertEqual(
            _missing_metric_reason("dsr", None),
            "연소득 정보가 없어 계산하지 않았습니다.",
        )
        self.assertIsNone(_missing_metric_reason("dsr", 35.0))


if __name__ == "__main__":
    unittest.main()
