from __future__ import annotations

from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest
from unittest.mock import Mock, patch

from modules.repositories.database import get_connection


class DatabaseConnectionTests(unittest.TestCase):
    def test_sqlite_connection_context_manager_commits_on_normal_exit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "test.db"

            with get_connection(database_path) as connection:
                connection.execute("CREATE TABLE sample (value INTEGER)")
                connection.execute("INSERT INTO sample (value) VALUES (1)")

            with closing(sqlite3.connect(database_path)) as verification_connection:
                row = verification_connection.execute("SELECT COUNT(*) FROM sample").fetchone()

            assert row is not None
            self.assertEqual(int(row[0]), 1)

    def test_sqlite_connection_context_manager_rolls_back_and_closes_on_exception(self) -> None:
        with TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "test.db"

            with closing(sqlite3.connect(database_path)) as seed_connection:
                seed_connection.execute("CREATE TABLE sample (value INTEGER)")
                seed_connection.commit()

            with self.assertRaisesRegex(RuntimeError, "boom"):
                with get_connection(database_path) as connection:
                    connection.execute("INSERT INTO sample (value) VALUES (1)")
                    raise RuntimeError("boom")

            with closing(sqlite3.connect(database_path)) as verification_connection:
                row = verification_connection.execute("SELECT COUNT(*) FROM sample").fetchone()

            assert row is not None
            self.assertEqual(int(row[0]), 0)

            # The rollback path must also close the sqlite file handle on Windows.
            database_path.unlink()

    def test_sqlite_connection_context_manager_closes_file_handle(self) -> None:
        with TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "test.db"

            with get_connection(database_path) as connection:
                connection.execute("CREATE TABLE IF NOT EXISTS sample (id INTEGER)")

            # Windows keeps the database file locked until the sqlite connection is closed.
            database_path.unlink()

    def test_postgres_target_uses_psycopg_connect_without_touching_sqlite(self) -> None:
        fake_connection = Mock()

        with (
            patch("modules.repositories.database.psycopg.connect", return_value=fake_connection) as connect_mock,
            patch("modules.repositories.database.sqlite3.connect") as sqlite_connect_mock,
        ):
            with get_connection("postgresql://estate:estate@localhost:5432/estate_pulse_test") as connection:
                self.assertIs(connection, fake_connection)

        connect_mock.assert_called_once()
        sqlite_connect_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
