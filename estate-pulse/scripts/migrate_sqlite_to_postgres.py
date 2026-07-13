from __future__ import annotations

import argparse
import os
from pathlib import Path
import sqlite3

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


TABLES_WITH_IDS = (
    "interest_area",
    "apartment_complex",
    "user_finance_profile",
    "manual_listing",
    "sale_transaction",
    "rent_transaction",
    "analysis_result",
    "watchlist",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate Estate Pulse data from SQLite to PostgreSQL.")
    parser.add_argument(
        "--sqlite-path",
        default=str(ROOT_DIR / "data" / "app.db"),
        help="Source SQLite DB path",
    )
    parser.add_argument(
        "--postgres-url",
        default=os.getenv("DATABASE_URL"),
        help="Target PostgreSQL DATABASE_URL",
    )
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite_path)
    postgres_url = str(args.postgres_url or "").strip()
    if not sqlite_path.exists():
        raise SystemExit(f"SQLite DB not found: {sqlite_path}")
    if not postgres_url:
        raise SystemExit("DATABASE_URL is required for PostgreSQL migration.")

    with sqlite3.connect(sqlite_path) as sqlite_conn, psycopg.connect(
        postgres_url,
        row_factory=dict_row,
    ) as pg_conn:
        sqlite_conn.row_factory = sqlite3.Row
        pg_conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE")

        source_counts = _read_counts_sqlite(sqlite_conn)
        target_counts_before = _read_counts_postgres(pg_conn)

        complex_id_map = _migrate_complexes(sqlite_conn, pg_conn)
        finance_profile_id_map = _migrate_rows_with_id_map(
            sqlite_conn,
            pg_conn,
            table_name="user_finance_profile",
        )
        listing_id_map = _migrate_manual_listings(
            sqlite_conn,
            pg_conn,
            complex_id_map=complex_id_map,
        )
        _migrate_rows_with_id_map(sqlite_conn, pg_conn, table_name="interest_area")
        _migrate_transactions(
            sqlite_conn,
            pg_conn,
            table_name="sale_transaction",
            complex_id_map=complex_id_map,
        )
        _migrate_transactions(
            sqlite_conn,
            pg_conn,
            table_name="rent_transaction",
            complex_id_map=complex_id_map,
        )
        _migrate_analysis_results(
            sqlite_conn,
            pg_conn,
            complex_id_map=complex_id_map,
            listing_id_map=listing_id_map,
            finance_profile_id_map=finance_profile_id_map,
        )
        _migrate_watchlist(
            sqlite_conn,
            pg_conn,
            complex_id_map=complex_id_map,
            listing_id_map=listing_id_map,
        )

        _sync_postgres_sequences(pg_conn)
        pg_conn.commit()

        target_counts_after = _read_counts_postgres(pg_conn)

    print("SQLite source counts:")
    for table_name, count in source_counts.items():
        print(f"  {table_name}: {count}")
    print("PostgreSQL target counts before:")
    for table_name, count in target_counts_before.items():
        print(f"  {table_name}: {count}")
    print("PostgreSQL target counts after:")
    for table_name, count in target_counts_after.items():
        print(f"  {table_name}: {count}")


def _read_counts_sqlite(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        table_name: int(connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
        for table_name in TABLES_WITH_IDS
    }


def _read_counts_postgres(connection: psycopg.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    with connection.cursor() as cursor:
        for table_name in TABLES_WITH_IDS:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            counts[table_name] = int(cursor.fetchone()["count"])
    return counts


def _get_sqlite_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
    return [row["name"] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()]


def _get_postgres_columns(connection: psycopg.Connection, table_name: str) -> list[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        return [row["column_name"] for row in cursor.fetchall()]


def _fetch_sqlite_rows(connection: sqlite3.Connection, table_name: str) -> list[dict]:
    rows = connection.execute(f"SELECT * FROM {table_name} ORDER BY id ASC").fetchall()
    return [dict(row) for row in rows]


def _migrate_complexes(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg.Connection,
) -> dict[int, int]:
    source_rows = _fetch_sqlite_rows(sqlite_conn, "apartment_complex")
    target_columns = [column for column in _get_postgres_columns(pg_conn, "apartment_complex") if column != "id"]
    id_map: dict[int, int] = {}

    with pg_conn.cursor() as cursor:
        for row in source_rows:
            cursor.execute(
                """
                SELECT id
                FROM apartment_complex
                WHERE name = %s
                  AND COALESCE(address, '') = COALESCE(%s, '')
                LIMIT 1
                """,
                (row.get("name"), row.get("address")),
            )
            existing = cursor.fetchone()
            if existing:
                id_map[int(row["id"])] = int(existing["id"])
                continue

            payload = {column: row.get(column) for column in target_columns}
            id_map[int(row["id"])] = _insert_returning_id(
                cursor,
                table_name="apartment_complex",
                payload=payload,
            )
    return id_map


def _migrate_rows_with_id_map(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg.Connection,
    *,
    table_name: str,
) -> dict[int, int]:
    source_rows = _fetch_sqlite_rows(sqlite_conn, table_name)
    target_columns = [column for column in _get_postgres_columns(pg_conn, table_name) if column != "id"]
    id_map: dict[int, int] = {}

    with pg_conn.cursor() as cursor:
        for row in source_rows:
            payload = {column: row.get(column) for column in target_columns}
            id_map[int(row["id"])] = _insert_returning_id(
                cursor,
                table_name=table_name,
                payload=payload,
            )
    return id_map


def _migrate_manual_listings(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg.Connection,
    *,
    complex_id_map: dict[int, int],
) -> dict[int, int]:
    source_rows = _fetch_sqlite_rows(sqlite_conn, "manual_listing")
    target_columns = [column for column in _get_postgres_columns(pg_conn, "manual_listing") if column != "id"]
    id_map: dict[int, int] = {}

    with pg_conn.cursor() as cursor:
        for row in source_rows:
            payload = {column: row.get(column) for column in target_columns}
            payload["complex_id"] = complex_id_map[int(row["complex_id"])]
            id_map[int(row["id"])] = _insert_returning_id(
                cursor,
                table_name="manual_listing",
                payload=payload,
            )
    return id_map


def _migrate_transactions(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg.Connection,
    *,
    table_name: str,
    complex_id_map: dict[int, int],
) -> None:
    source_rows = _fetch_sqlite_rows(sqlite_conn, table_name)
    target_columns = [column for column in _get_postgres_columns(pg_conn, table_name) if column != "id"]

    with pg_conn.cursor() as cursor:
        for row in source_rows:
            payload = {column: row.get(column) for column in target_columns}
            complex_id = row.get("complex_id")
            if complex_id is not None:
                payload["complex_id"] = complex_id_map.get(int(complex_id))
            _insert_returning_id(cursor, table_name=table_name, payload=payload)


def _migrate_analysis_results(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg.Connection,
    *,
    complex_id_map: dict[int, int],
    listing_id_map: dict[int, int],
    finance_profile_id_map: dict[int, int],
) -> None:
    source_rows = _fetch_sqlite_rows(sqlite_conn, "analysis_result")
    source_columns = set(_get_sqlite_columns(sqlite_conn, "analysis_result"))
    target_columns = [column for column in _get_postgres_columns(pg_conn, "analysis_result") if column != "id"]

    with pg_conn.cursor() as cursor:
        for row in source_rows:
            payload = {column: row.get(column) for column in target_columns if column in source_columns}
            listing_id = row.get("listing_id")
            complex_id = row.get("complex_id")
            finance_profile_id = row.get("finance_profile_id")

            if "target_type" not in source_columns:
                payload["target_type"] = "LISTING" if listing_id is not None else "COMPLEX_AREA"
            if "price_source" not in source_columns:
                payload["price_source"] = "LISTING" if listing_id is not None else None
            if "effective_price_snapshot" not in source_columns:
                payload["effective_price_snapshot"] = row.get("sale_price_snapshot")

            payload["listing_id"] = listing_id_map.get(int(listing_id)) if listing_id is not None else None
            payload["complex_id"] = complex_id_map.get(int(complex_id)) if complex_id is not None else None
            payload["finance_profile_id"] = (
                finance_profile_id_map.get(int(finance_profile_id))
                if finance_profile_id is not None
                else None
            )
            _insert_returning_id(cursor, table_name="analysis_result", payload=payload)


def _migrate_watchlist(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg.Connection,
    *,
    complex_id_map: dict[int, int],
    listing_id_map: dict[int, int],
) -> None:
    source_rows = _fetch_sqlite_rows(sqlite_conn, "watchlist")
    source_columns = set(_get_sqlite_columns(sqlite_conn, "watchlist"))
    target_columns = [column for column in _get_postgres_columns(pg_conn, "watchlist") if column != "id"]

    with pg_conn.cursor() as cursor:
        for row in source_rows:
            payload = {column: row.get(column) for column in target_columns if column in source_columns}
            complex_id = row.get("complex_id")
            listing_id = row.get("listing_id")
            payload["complex_id"] = complex_id_map.get(int(complex_id)) if complex_id is not None else None
            payload["listing_id"] = listing_id_map.get(int(listing_id)) if listing_id is not None else None
            if payload["complex_id"] is None and payload["listing_id"] is None:
                continue
            _insert_returning_id(cursor, table_name="watchlist", payload=payload)


def _insert_returning_id(cursor, *, table_name: str, payload: dict) -> int:
    columns = list(payload.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(columns)
    cursor.execute(
        f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders}) RETURNING id",
        [payload[column] for column in columns],
    )
    return int(cursor.fetchone()["id"])


def _sync_postgres_sequences(connection: psycopg.Connection) -> None:
    with connection.cursor() as cursor:
        for table_name in TABLES_WITH_IDS:
            cursor.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence(%s, 'id'),
                    COALESCE((SELECT MAX(id) FROM public.""" + table_name + """), 1),
                    true
                )
                """,
                (f"public.{table_name}",),
            )


if __name__ == "__main__":
    main()
