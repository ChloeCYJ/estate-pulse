import unittest

from modules.ui.dashboard import (
    _active_policy_event_count,
    _best_candidate_cash_status,
    _best_candidate_conclusion,
    _best_candidate_payload,
    _best_candidate_purchase_status,
    _best_candidate_reasons,
    _best_candidate_score_label,
    _best_candidate_shortage_label,
    _dashboard_policy_summary,
    _minimum_shortage_cash,
)


class DashboardViewTests(unittest.TestCase):
    def test_minimum_shortage_cash_uses_zero_for_buyable_candidate(self) -> None:
        analyses = [
            {"shortage_cash": 320_000_000},
            {"shortage_cash": -50_000_000},
            {"shortage_cash": 120_000_000},
        ]

        self.assertEqual(_minimum_shortage_cash(analyses), 0)

    def test_best_candidate_payload_keeps_raw_cash_values(self) -> None:
        payload = _best_candidate_payload(
            {
                "complex_name": "샘플레이크뷰",
                "investment_score": 65,
                "liquidity_score": 100,
                "bargain_score": 70,
                "required_cash": 490_000_000,
                "shortage_cash": 0,
                "complex_grade": "SUB_LEADER",
            }
        )

        self.assertEqual(payload["단지"], "샘플레이크뷰")
        self.assertEqual(payload["현재 자금_raw"], 490_000_000)
        self.assertEqual(payload["추가 필요 현금_raw"], 0)
        self.assertEqual(payload["등급"], "준대장")

    def test_best_candidate_card_labels_and_conclusion_use_cash_first(self) -> None:
        feasible_row = {
            "단지": "샘플레이크뷰",
            "추가 필요 현금": "0원",
            "추가 필요 현금_raw": 0,
            "투자 점수": 65,
        }
        constrained_row = {
            "단지": "샘플리버파크",
            "추가 필요 현금": "7.6억",
            "추가 필요 현금_raw": 760_000_000,
            "투자 점수": 25,
        }

        self.assertEqual(_best_candidate_cash_status(feasible_row), "매수 가능")
        self.assertEqual(_best_candidate_cash_status(constrained_row), "7.6억 부족")
        self.assertEqual(_best_candidate_shortage_label(feasible_row), "0원")
        self.assertEqual(_best_candidate_shortage_label(constrained_row), "7.6억")
        self.assertEqual(_best_candidate_purchase_status(constrained_row), "자금 보강 필요")
        self.assertEqual(_best_candidate_score_label(constrained_row), "25점")
        self.assertIn("가장 현실적인 선택지", _best_candidate_conclusion(feasible_row))
        self.assertIn("약 7.6억의 추가 자금 확보", _best_candidate_conclusion(constrained_row))

    def test_best_candidate_reasons_surface_top_rank_and_cash_context(self) -> None:
        reasons = _best_candidate_reasons(
            {
                "투자 점수": 25,
                "유동성": 90,
                "등급": "준대장",
                "추가 필요 현금_raw": 690_000_000,
            }
        )

        self.assertIn("투자점수 1위", reasons)
        self.assertIn("유동성 우수", reasons)
        self.assertIn("단지등급 준대장", reasons)

    def test_policy_summary_uses_active_event_title(self) -> None:
        summary = _dashboard_policy_summary(
            [
                {
                    "status": "ACTIVE",
                    "policy_type": "LOAN",
                    "title": "20억이상 2억대출",
                    "summary": "20억 이상 주택 대출 한도 2억",
                }
            ]
        )

        self.assertIn("대출", summary)
        self.assertIn("20억 이상", summary)

    def test_active_policy_event_count_filters_active_only(self) -> None:
        count = _active_policy_event_count(
            [
                {"status": "ACTIVE"},
                {"status": "FUTURE"},
                {"status": "ACTIVE"},
            ]
        )

        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
