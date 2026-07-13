from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.analysis_repository import AnalysisRepository
from modules.repositories.database import initialize_database


class AnalysisResultSqliteMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "legacy.db"
        self._create_legacy_database(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_initialize_database_preserves_legacy_analysis_result_data_indexes_and_foreign_keys(self) -> None:
        initialize_database(self.database_path)

        repository = AnalysisRepository(self.database_path)
        latest = repository.get_latest_by_listing(1)
        self.assertIsNotNone(latest)
        assert latest is not None
        self.assertEqual(latest["id"], 1)
        self.assertEqual(latest["target_type"], "LISTING")
        self.assertEqual(latest["listing_id"], 1)
        self.assertEqual(latest["sale_price_snapshot"], 900_000_000)
        self.assertEqual(latest["jeonse_price_snapshot"], 540_000_000)
        self.assertEqual(latest["complex_name_snapshot"], "Legacy Complex")

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            listing_row = next(
                row
                for row in connection.execute("PRAGMA table_info(analysis_result)").fetchall()
                if row["name"] == "listing_id"
            )
            self.assertEqual(int(listing_row["notnull"]), 0)

            index_names = {
                row["name"]
                for row in connection.execute("PRAGMA index_list(analysis_result)").fetchall()
            }
            self.assertIn("idx_analysis_result_listing_created", index_names)

            foreign_key_tables = {
                row["table"]
                for row in connection.execute(
                    "PRAGMA foreign_key_list(analysis_result)"
                ).fetchall()
            }
            self.assertIn("manual_listing", foreign_key_tables)
            self.assertIn("user_finance_profile", foreign_key_tables)
            self.assertIn("apartment_complex", foreign_key_tables)

        recent = repository.list_recent(limit=1)[0]
        self.assertEqual(recent["target_type"], "LISTING")
        self.assertEqual(recent["sale_price"], 900_000_000)
        self.assertEqual(recent["expected_jeonse_price"], 540_000_000)
        self.assertEqual(recent["complex_name"], "Legacy Complex")

    def _create_legacy_database(self, database_path: Path) -> None:
        with sqlite3.connect(database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(
                """
                CREATE TABLE apartment_complex (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE manual_listing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complex_id INTEGER NOT NULL,
                    area_m2 REAL NOT NULL,
                    sale_price INTEGER NOT NULL,
                    expected_jeonse_price INTEGER,
                    checked_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (complex_id) REFERENCES apartment_complex(id) ON DELETE CASCADE
                );

                CREATE TABLE user_finance_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cash_amount INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE analysis_result (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id INTEGER NOT NULL,
                    finance_profile_id INTEGER,
                    required_cash INTEGER,
                    shortage_cash INTEGER,
                    jeonse_ratio REAL,
                    discount_vs_recent_avg REAL,
                    drop_from_high REAL,
                    bargain_score INTEGER,
                    investment_type TEXT,
                    current_required_cash INTEGER,
                    future_required_cash INTEGER,
                    monthly_cash_flow INTEGER,
                    acquisition_tax INTEGER,
                    local_education_tax INTEGER,
                    brokerage_fee INTEGER,
                    legal_fee INTEGER,
                    reserve_cost INTEGER,
                    total_transaction_cost INTEGER,
                    applied_tax_rule_version TEXT,
                    applied_brokerage_rule_version TEXT,
                    liquidity_score INTEGER,
                    investment_score INTEGER,
                    complex_grade TEXT,
                    sale_price_snapshot INTEGER,
                    jeonse_price_snapshot INTEGER,
                    area_m2_snapshot REAL,
                    complex_name_snapshot TEXT,
                    available_cash_snapshot INTEGER,
                    annual_income_snapshot INTEGER,
                    buyer_type_snapshot TEXT,
                    expected_loan_amount INTEGER,
                    monthly_repayment INTEGER,
                    loan_rule_version TEXT,
                    decision TEXT,
                    summary TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (listing_id) REFERENCES manual_listing(id) ON DELETE CASCADE,
                    FOREIGN KEY (finance_profile_id) REFERENCES user_finance_profile(id) ON DELETE SET NULL
                );

                CREATE INDEX idx_analysis_result_listing_created
                    ON analysis_result(listing_id, created_at);
                """
            )

            connection.execute(
                """
                INSERT INTO apartment_complex (id, name, created_at)
                VALUES (1, 'Legacy Complex', '2026-07-12T00:00:00+00:00')
                """
            )
            connection.execute(
                """
                INSERT INTO manual_listing (
                    id,
                    complex_id,
                    area_m2,
                    sale_price,
                    expected_jeonse_price,
                    checked_at,
                    created_at
                )
                VALUES (
                    1,
                    1,
                    84.9,
                    900000000,
                    540000000,
                    '2026-05-27',
                    '2026-07-12T00:00:00+00:00'
                )
                """
            )
            connection.execute(
                """
                INSERT INTO user_finance_profile (id, cash_amount, created_at)
                VALUES (1, 300000000, '2026-07-12T00:00:00+00:00')
                """
            )
            connection.execute(
                """
                INSERT INTO analysis_result (
                    id,
                    listing_id,
                    finance_profile_id,
                    required_cash,
                    shortage_cash,
                    jeonse_ratio,
                    discount_vs_recent_avg,
                    drop_from_high,
                    bargain_score,
                    investment_type,
                    current_required_cash,
                    future_required_cash,
                    monthly_cash_flow,
                    acquisition_tax,
                    local_education_tax,
                    brokerage_fee,
                    legal_fee,
                    reserve_cost,
                    total_transaction_cost,
                    applied_tax_rule_version,
                    applied_brokerage_rule_version,
                    liquidity_score,
                    investment_score,
                    complex_grade,
                    sale_price_snapshot,
                    jeonse_price_snapshot,
                    area_m2_snapshot,
                    complex_name_snapshot,
                    available_cash_snapshot,
                    annual_income_snapshot,
                    buyer_type_snapshot,
                    expected_loan_amount,
                    monthly_repayment,
                    loan_rule_version,
                    decision,
                    summary,
                    created_at
                )
                VALUES (
                    1,
                    1,
                    1,
                    360000000,
                    60000000,
                    60.0,
                    5.0,
                    4.0,
                    55,
                    'GAP_INVESTMENT',
                    360000000,
                    NULL,
                    NULL,
                    9900000,
                    900000,
                    3500000,
                    300000,
                    4500000,
                    18200000,
                    'tax-legacy',
                    'brokerage-legacy',
                    65,
                    72,
                    'NORMAL',
                    900000000,
                    540000000,
                    84.9,
                    'Legacy Complex',
                    300000000,
                    120000000,
                    'NO_HOME',
                    540000000,
                    2576943,
                    'loan-legacy',
                    'legacy decision',
                    'legacy summary',
                    '2026-07-12T00:00:00+00:00'
                )
                """
            )
            connection.commit()


if __name__ == "__main__":
    unittest.main()
