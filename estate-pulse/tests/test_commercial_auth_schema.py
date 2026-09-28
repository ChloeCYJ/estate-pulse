from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.database import initialize_database


class CommercialAuthSchemaTests(unittest.TestCase):
    def test_initialize_database_creates_account_tables_and_owner_columns(self) -> None:
        with TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "test.db"
            initialize_database(database_path)

            with closing(sqlite3.connect(database_path)) as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    ).fetchall()
                }
                finance_columns = {
                    row[1]
                    for row in connection.execute(
                        "PRAGMA table_info(user_finance_profile)"
                    ).fetchall()
                }
                analysis_columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(analysis_result)").fetchall()
                }

            self.assertIn("app_user", tables)
            self.assertIn("auth_identity", tables)
            self.assertIn("user_id", finance_columns)
            self.assertIn("user_id", analysis_columns)

    def test_initialize_database_keeps_legacy_rows_unowned(self) -> None:
        with TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "legacy.db"
            self._create_legacy_owned_tables(database_path)
            initialize_database(database_path)

            with closing(sqlite3.connect(database_path)) as connection:
                finance_owner = connection.execute(
                    "SELECT user_id FROM user_finance_profile WHERE id = 1"
                ).fetchone()
                analysis_owner = connection.execute(
                    "SELECT user_id FROM analysis_result WHERE id = 1"
                ).fetchone()

            self.assertEqual(finance_owner, (None,))
            self.assertEqual(analysis_owner, (None,))

    def test_owned_finance_profile_index_allows_one_profile_per_user(self) -> None:
        with TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "test.db"
            initialize_database(database_path)

            with closing(sqlite3.connect(database_path)) as connection:
                connection.execute(
                    "INSERT INTO app_user (id, is_active, created_at, updated_at) VALUES (1, 1, 'now', 'now')"
                )
                connection.execute(
                    "INSERT INTO user_finance_profile (cash_amount, created_at, user_id) VALUES (100, 'now', 1)"
                )
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "INSERT INTO user_finance_profile (cash_amount, created_at, user_id) VALUES (200, 'later', 1)"
                    )

    def _create_legacy_owned_tables(self, database_path: Path) -> None:
        with closing(sqlite3.connect(database_path)) as connection:
            connection.executescript(
                """
                CREATE TABLE user_finance_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cash_amount INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE analysis_result (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id INTEGER,
                    finance_profile_id INTEGER,
                    created_at TEXT NOT NULL
                );

                INSERT INTO user_finance_profile (id, cash_amount, created_at)
                VALUES (1, 300000000, '2026-09-28T00:00:00+00:00');

                INSERT INTO analysis_result (id, listing_id, finance_profile_id, created_at)
                VALUES (1, NULL, 1, '2026-09-28T00:00:00+00:00');
                """
            )
            connection.commit()


if __name__ == "__main__":
    unittest.main()
