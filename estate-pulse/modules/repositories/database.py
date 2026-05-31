from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable, Sequence


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS interest_area (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sido TEXT NOT NULL,
        sigungu TEXT NOT NULL,
        dong TEXT,
        memo TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS apartment_complex (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sido TEXT,
        sigungu TEXT,
        dong TEXT,
        address TEXT,
        build_year INTEGER,
        household_count INTEGER,
        lat REAL,
        lng REAL,
        complex_grade TEXT,
        memo TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS manual_listing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complex_id INTEGER NOT NULL,
        area_m2 REAL NOT NULL,
        sale_price INTEGER NOT NULL,
        expected_jeonse_price INTEGER,
        investment_type TEXT,
        takeover_jeonse_deposit INTEGER,
        rent_deposit INTEGER,
        expected_monthly_rent INTEGER,
        floor TEXT,
        direction TEXT,
        condition_memo TEXT,
        source_memo TEXT,
        checked_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (complex_id) REFERENCES apartment_complex(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sale_transaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complex_id INTEGER,
        complex_name TEXT,
        area_m2 REAL,
        deal_year INTEGER,
        deal_month INTEGER,
        deal_day INTEGER,
        price INTEGER,
        floor INTEGER,
        raw_address TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rent_transaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complex_id INTEGER,
        complex_name TEXT,
        area_m2 REAL,
        deal_year INTEGER,
        deal_month INTEGER,
        deal_day INTEGER,
        deposit INTEGER,
        monthly_rent INTEGER,
        floor INTEGER,
        raw_address TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_finance_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cash_amount INTEGER NOT NULL,
        annual_income INTEGER,
        existing_debt INTEGER DEFAULT 0,
        interest_rate REAL,
        ltv_limit REAL,
        dsr_limit REAL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS analysis_result (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id INTEGER NOT NULL,
        required_cash INTEGER,
        shortage_cash INTEGER,
        jeonse_ratio REAL,
        discount_vs_recent_avg REAL,
        drop_from_high REAL,
        bargain_score INTEGER,
        undervalue_score INTEGER,
        risk_score INTEGER,
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
        loan_rule_version TEXT,
        decision TEXT,
        summary TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (listing_id) REFERENCES manual_listing(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complex_id INTEGER,
        listing_id INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY (complex_id) REFERENCES apartment_complex(id) ON DELETE CASCADE,
        FOREIGN KEY (listing_id) REFERENCES manual_listing(id) ON DELETE CASCADE,
        CHECK (complex_id IS NOT NULL OR listing_id IS NOT NULL),
        UNIQUE (complex_id, listing_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS policy_import (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_text TEXT NOT NULL,
        source_name TEXT,
        target_rule_type TEXT NOT NULL,
        effective_date TEXT,
        parser_name TEXT NOT NULL,
        parser_status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rule_candidate (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_import_id INTEGER NOT NULL,
        target_rule_type TEXT NOT NULL,
        rule_name TEXT NOT NULL,
        rule_version TEXT,
        previous_rule_json TEXT,
        proposed_rule_json TEXT NOT NULL,
        changed_fields_json TEXT,
        confidence REAL,
        warnings TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        reviewed_at TEXT,
        applied_at TEXT,
        FOREIGN KEY (policy_import_id) REFERENCES policy_import(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS region_policy_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_level TEXT NOT NULL,
        sido TEXT NOT NULL,
        sigungu TEXT,
        dong TEXT,
        policy_type TEXT NOT NULL,
        effective_from TEXT NOT NULL,
        effective_to TEXT,
        notes TEXT,
        source_policy_import_id INTEGER,
        created_at TEXT NOT NULL,
        FOREIGN KEY (source_policy_import_id) REFERENCES policy_import(id) ON DELETE SET NULL
    )
    """,
]


def get_connection(database_path: Path | str) -> sqlite3.Connection:
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path | str) -> None:
    with get_connection(database_path) as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        _ensure_manual_listing_columns(connection)
        _ensure_apartment_complex_columns(connection)
        _ensure_analysis_result_columns(connection)
        connection.commit()


def execute(database_path: Path | str, query: str, parameters: Sequence[Any] = ()) -> int:
    with get_connection(database_path) as connection:
        cursor = connection.execute(query, parameters)
        connection.commit()
        return int(cursor.lastrowid)


def execute_many(
    database_path: Path | str, query: str, parameters: Iterable[Sequence[Any]]
) -> None:
    with get_connection(database_path) as connection:
        connection.executemany(query, parameters)
        connection.commit()


def fetch_one(database_path: Path | str, query: str, parameters: Sequence[Any] = ()) -> dict | None:
    with get_connection(database_path) as connection:
        row = connection.execute(query, parameters).fetchone()
    return dict(row) if row else None


def fetch_all(database_path: Path | str, query: str, parameters: Sequence[Any] = ()) -> list[dict]:
    with get_connection(database_path) as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [dict(row) for row in rows]


def _ensure_analysis_result_columns(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(analysis_result)").fetchall()
    }
    if "investment_type" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN investment_type TEXT")
    if "current_required_cash" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN current_required_cash INTEGER")
    if "future_required_cash" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN future_required_cash INTEGER")
    if "monthly_cash_flow" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN monthly_cash_flow INTEGER")
    if "loan_rule_version" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN loan_rule_version TEXT")
    if "acquisition_tax" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN acquisition_tax INTEGER")
    if "local_education_tax" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN local_education_tax INTEGER")
    if "brokerage_fee" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN brokerage_fee INTEGER")
    if "legal_fee" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN legal_fee INTEGER")
    if "reserve_cost" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN reserve_cost INTEGER")
    if "total_transaction_cost" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN total_transaction_cost INTEGER")
    if "applied_tax_rule_version" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN applied_tax_rule_version TEXT")
    if "applied_brokerage_rule_version" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN applied_brokerage_rule_version TEXT")
    if "liquidity_score" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN liquidity_score INTEGER")
    if "investment_score" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN investment_score INTEGER")
    if "complex_grade" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN complex_grade TEXT")


def _ensure_manual_listing_columns(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(manual_listing)").fetchall()
    }
    if "investment_type" not in existing_columns:
        connection.execute("ALTER TABLE manual_listing ADD COLUMN investment_type TEXT")
    if "takeover_jeonse_deposit" not in existing_columns:
        connection.execute("ALTER TABLE manual_listing ADD COLUMN takeover_jeonse_deposit INTEGER")
    if "rent_deposit" not in existing_columns:
        connection.execute("ALTER TABLE manual_listing ADD COLUMN rent_deposit INTEGER")
    if "expected_monthly_rent" not in existing_columns:
        connection.execute("ALTER TABLE manual_listing ADD COLUMN expected_monthly_rent INTEGER")


def _ensure_apartment_complex_columns(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(apartment_complex)").fetchall()
    }
    if "complex_grade" not in existing_columns:
        connection.execute("ALTER TABLE apartment_complex ADD COLUMN complex_grade TEXT")
