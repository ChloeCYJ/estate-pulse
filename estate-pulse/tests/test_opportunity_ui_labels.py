import unittest

from modules.ui.comparison_view import _format_money_or_dash as _comparison_money_label
from modules.ui.ranking_view import _format_money_or_dash as _ranking_money_label
from modules.ui.watchlist_view import _format_money_or_dash as _watchlist_money_label


class OpportunityUiLabelTests(unittest.TestCase):
    def test_comparison_additional_cash_display_does_not_show_negative_values(self) -> None:
        self.assertEqual(_comparison_money_label(-50_000_000), "0원")

    def test_ranking_additional_cash_display_does_not_show_negative_values(self) -> None:
        self.assertEqual(_ranking_money_label(-50_000_000), "0원")

    def test_watchlist_additional_cash_display_does_not_show_negative_values(self) -> None:
        self.assertEqual(_watchlist_money_label(-50_000_000), "0원")


if __name__ == "__main__":
    unittest.main()
