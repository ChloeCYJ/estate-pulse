from __future__ import annotations

import math
import unittest
from decimal import Decimal

from modules.utils.money_utils import format_compact_won, format_won, to_eok


class MoneyUtilsTests(unittest.TestCase):
    def test_formatters_handle_float_nan(self) -> None:
        self.assertEqual(format_won(math.nan), "0원")
        self.assertEqual(format_compact_won(math.nan), "0원")
        self.assertEqual(to_eok(math.nan), 0.0)

    def test_formatters_handle_decimal_nan(self) -> None:
        value = Decimal("NaN")

        self.assertEqual(format_won(value), "0원")
        self.assertEqual(format_compact_won(value), "0원")
        self.assertEqual(to_eok(value), 0.0)


if __name__ == "__main__":
    unittest.main()
