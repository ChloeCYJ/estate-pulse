from __future__ import annotations

from datetime import date, datetime
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - optional dependency for PostgreSQL runtime support
    psycopg = None
    dict_row = None


ANALYSIS_RESULT_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS analysis_result (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_type TEXT NOT NULL DEFAULT 'LISTING',
        listing_id INTEGER,
        complex_id INTEGER,
        area_bucket REAL,
        price_source TEXT,
        effective_price_snapshot INTEGER,
        reference_price INTEGER,
        sample_count INTEGER,
        latest_transaction_date TEXT,
        selected_transaction_min_price INTEGER,
        selected_transaction_max_price INTEGER,
        confidence TEXT,
        volatility_status TEXT,
        finance_profile_id INTEGER,
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
        FOREIGN KEY (complex_id) REFERENCES apartment_complex(id) ON DELETE CASCADE,
        FOREIGN KEY (finance_profile_id) REFERENCES user_finance_profile(id) ON DELETE SET NULL
    )
"""


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
        molit_lawd_cd TEXT,
        molit_apt_name TEXT,
        molit_umd_name TEXT,
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
        home_count INTEGER DEFAULT 0,
        owned_real_estate_value INTEGER DEFAULT 0,
        owned_real_estate_debt INTEGER DEFAULT 0,
        credit_loan_balance INTEGER DEFAULT 0,
        other_loan_balance INTEGER DEFAULT 0,
        use_manual_ltv INTEGER DEFAULT 0,
        manual_ltv_rate REAL,
        created_at TEXT NOT NULL
    )
    """,
    ANALYSIS_RESULT_TABLE_SQL,
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
    """
    CREATE TABLE IF NOT EXISTS policy_event (
        policy_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_type TEXT NOT NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        detail TEXT NOT NULL,
        effective_from TEXT NOT NULL,
        effective_to TEXT,
        affected_region_sido TEXT,
        affected_region_sigungu TEXT,
        affected_region_dong TEXT,
        affected_buyer_type TEXT NOT NULL,
        affected_investment_purpose TEXT NOT NULL,
        impact_level TEXT NOT NULL,
        calculation_supported INTEGER NOT NULL,
        action_required INTEGER NOT NULL,
        source_text TEXT NOT NULL,
        source_name TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS policy_event_candidate (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_import_id INTEGER NOT NULL,
        policy_type TEXT NOT NULL,
        title TEXT NOT NULL,
        impact_level TEXT NOT NULL,
        proposed_event_json TEXT NOT NULL,
        confidence REAL,
        warnings TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        reviewed_at TEXT,
        applied_at TEXT,
        FOREIGN KEY (policy_import_id) REFERENCES policy_import(id) ON DELETE CASCADE
    )
    """,
]

POSTGRES_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations" / "postgres"
POSTGRES_URL_PREFIXES = ("postgresql://", "postgres://")
INSERT_TABLE_PATTERN = re.compile(r"INSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.IGNORECASE)


def is_postgres_target(database_path: Path | str) -> bool:
    return isinstance(database_path, str) and database_path.startswith(POSTGRES_URL_PREFIXES)


def build_deal_date_sql(database_path: Path | str) -> str:
    if is_postgres_target(database_path):
        return (
            "LPAD(deal_year::text, 4, '0') || '-' || "
            "LPAD(deal_month::text, 2, '0') || '-' || "
            "LPAD(deal_day::text, 2, '0')"
        )
    return "printf('%04d-%02d-%02d', deal_year, deal_month, deal_day)"


def get_connection(database_path: Path | str) -> Any:
    if is_postgres_target(database_path):
        if psycopg is None or dict_row is None:
            raise RuntimeError(
                "PostgreSQL support requires psycopg. Install project dependencies first."
            )
        return psycopg.connect(str(database_path), row_factory=dict_row)

    sqlite_database_path = Path(database_path)
    sqlite_database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(sqlite_database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path | str) -> None:
    with get_connection(database_path) as connection:
        if is_postgres_target(database_path):
            for statement in _load_postgres_schema_statements():
                connection.execute(statement)
            _ensure_postgres_apartment_complex_columns(connection)
            _ensure_postgres_analysis_result_columns(connection)
            connection.commit()
            return

        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        _ensure_manual_listing_columns(connection)
        _ensure_apartment_complex_columns(connection)
        _ensure_user_finance_profile_columns(connection)
        _ensure_analysis_result_listing_id_nullable(connection)
        _ensure_analysis_result_columns(connection)
        connection.commit()


def execute(database_path: Path | str, query: str, parameters: Sequence[Any] = ()) -> int:
    with get_connection(database_path) as connection:
        cursor = connection.execute(_prepare_query(database_path, query), parameters)
        if is_postgres_target(database_path) and _is_insert_query(query):
            row = cursor.fetchone()
            connection.commit()
            return _extract_inserted_id(row)
        connection.commit()
        return int(getattr(cursor, "lastrowid", 0) or 0)


def execute_many(
    database_path: Path | str, query: str, parameters: Iterable[Sequence[Any]]
) -> None:
    with get_connection(database_path) as connection:
        if is_postgres_target(database_path):
            with connection.cursor() as cursor:
                cursor.executemany(_prepare_query(database_path, query), parameters)
        else:
            connection.executemany(query, parameters)
        connection.commit()


def fetch_one(database_path: Path | str, query: str, parameters: Sequence[Any] = ()) -> dict | None:
    with get_connection(database_path) as connection:
        row = connection.execute(_prepare_query(database_path, query), parameters).fetchone()
    return _normalize_row(row)


def fetch_all(database_path: Path | str, query: str, parameters: Sequence[Any] = ()) -> list[dict]:
    with get_connection(database_path) as connection:
        rows = connection.execute(_prepare_query(database_path, query), parameters).fetchall()
    return [_normalize_row(row) for row in rows if row is not None]


def _ensure_user_finance_profile_columns(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(user_finance_profile)").fetchall()
    }
    if "home_count" not in existing_columns:
        connection.execute("ALTER TABLE user_finance_profile ADD COLUMN home_count INTEGER DEFAULT 0")
    if "owned_real_estate_value" not in existing_columns:
        connection.execute(
            "ALTER TABLE user_finance_profile ADD COLUMN owned_real_estate_value INTEGER DEFAULT 0"
        )
    if "owned_real_estate_debt" not in existing_columns:
        connection.execute(
            "ALTER TABLE user_finance_profile ADD COLUMN owned_real_estate_debt INTEGER DEFAULT 0"
        )
    if "credit_loan_balance" not in existing_columns:
        connection.execute(
            "ALTER TABLE user_finance_profile ADD COLUMN credit_loan_balance INTEGER DEFAULT 0"
        )
    if "other_loan_balance" not in existing_columns:
        connection.execute(
            "ALTER TABLE user_finance_profile ADD COLUMN other_loan_balance INTEGER DEFAULT 0"
        )
    if "use_manual_ltv" not in existing_columns:
        connection.execute("ALTER TABLE user_finance_profile ADD COLUMN use_manual_ltv INTEGER DEFAULT 0")
    if "manual_ltv_rate" not in existing_columns:
        connection.execute("ALTER TABLE user_finance_profile ADD COLUMN manual_ltv_rate REAL")


def _ensure_analysis_result_columns(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(analysis_result)").fetchall()
    }
    if "target_type" not in existing_columns:
        connection.execute(
            "ALTER TABLE analysis_result ADD COLUMN target_type TEXT NOT NULL DEFAULT 'LISTING'"
        )
    if "complex_id" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN complex_id INTEGER")
    if "area_bucket" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN area_bucket REAL")
    if "price_source" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN price_source TEXT")
    if "effective_price_snapshot" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN effective_price_snapshot INTEGER")
    if "reference_price" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN reference_price INTEGER")
    if "sample_count" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN sample_count INTEGER")
    if "latest_transaction_date" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN latest_transaction_date TEXT")
    if "selected_transaction_min_price" not in existing_columns:
        connection.execute(
            "ALTER TABLE analysis_result ADD COLUMN selected_transaction_min_price INTEGER"
        )
    if "selected_transaction_max_price" not in existing_columns:
        connection.execute(
            "ALTER TABLE analysis_result ADD COLUMN selected_transaction_max_price INTEGER"
        )
    if "confidence" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN confidence TEXT")
    if "volatility_status" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN volatility_status TEXT")
    if "finance_profile_id" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN finance_profile_id INTEGER")
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
    if "sale_price_snapshot" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN sale_price_snapshot INTEGER")
    if "jeonse_price_snapshot" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN jeonse_price_snapshot INTEGER")
    if "area_m2_snapshot" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN area_m2_snapshot REAL")
    if "complex_name_snapshot" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN complex_name_snapshot TEXT")
    if "available_cash_snapshot" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN available_cash_snapshot INTEGER")
    if "annual_income_snapshot" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN annual_income_snapshot INTEGER")
    if "buyer_type_snapshot" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN buyer_type_snapshot TEXT")
    if "expected_loan_amount" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN expected_loan_amount INTEGER")
    if "monthly_repayment" not in existing_columns:
        connection.execute("ALTER TABLE analysis_result ADD COLUMN monthly_repayment INTEGER")


def _ensure_analysis_result_listing_id_nullable(connection: sqlite3.Connection) -> None:
    table_info = connection.execute("PRAGMA table_info(analysis_result)").fetchall()
    listing_row = next((row for row in table_info if row["name"] == "listing_id"), None)
    if listing_row is None or int(listing_row["notnull"]) == 0:
        return

    existing_columns = [row["name"] for row in table_info]
    existing_indexes = [
        row["sql"]
        for row in connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'index'
              AND tbl_name = 'analysis_result'
              AND sql IS NOT NULL
            ORDER BY name ASC
            """
        ).fetchall()
    ]
    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("DROP TABLE IF EXISTS analysis_result_new")
    connection.execute(_analysis_result_table_sql_for_name("analysis_result_new"))

    copy_columns = [
        column_name
        for column_name in (
            "id",
            "listing_id",
            "finance_profile_id",
            "required_cash",
            "shortage_cash",
            "jeonse_ratio",
            "discount_vs_recent_avg",
            "drop_from_high",
            "bargain_score",
            "undervalue_score",
            "risk_score",
            "investment_type",
            "current_required_cash",
            "future_required_cash",
            "monthly_cash_flow",
            "acquisition_tax",
            "local_education_tax",
            "brokerage_fee",
            "legal_fee",
            "reserve_cost",
            "total_transaction_cost",
            "applied_tax_rule_version",
            "applied_brokerage_rule_version",
            "liquidity_score",
            "investment_score",
            "complex_grade",
            "sale_price_snapshot",
            "jeonse_price_snapshot",
            "area_m2_snapshot",
            "complex_name_snapshot",
            "available_cash_snapshot",
            "annual_income_snapshot",
            "buyer_type_snapshot",
            "expected_loan_amount",
            "monthly_repayment",
            "loan_rule_version",
            "decision",
            "summary",
            "created_at",
        )
        if column_name in existing_columns
    ]
    column_csv = ", ".join(copy_columns)
    connection.execute(
        f"""
        INSERT INTO analysis_result_new ({column_csv})
        SELECT {column_csv}
        FROM analysis_result
        """
    )
    connection.execute("DROP TABLE analysis_result")
    connection.execute("ALTER TABLE analysis_result_new RENAME TO analysis_result")
    for index_sql in existing_indexes:
        connection.execute(str(index_sql))
    connection.execute("PRAGMA foreign_keys = ON")


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
    if "molit_lawd_cd" not in existing_columns:
        connection.execute("ALTER TABLE apartment_complex ADD COLUMN molit_lawd_cd TEXT")
    if "molit_apt_name" not in existing_columns:
        connection.execute("ALTER TABLE apartment_complex ADD COLUMN molit_apt_name TEXT")
    if "molit_umd_name" not in existing_columns:
        connection.execute("ALTER TABLE apartment_complex ADD COLUMN molit_umd_name TEXT")
    if "complex_grade" not in existing_columns:
        connection.execute("ALTER TABLE apartment_complex ADD COLUMN complex_grade TEXT")


def _ensure_postgres_apartment_complex_columns(connection: Any) -> None:
    connection.execute("ALTER TABLE apartment_complex ADD COLUMN IF NOT EXISTS molit_lawd_cd TEXT")
    connection.execute("ALTER TABLE apartment_complex ADD COLUMN IF NOT EXISTS molit_apt_name TEXT")
    connection.execute("ALTER TABLE apartment_complex ADD COLUMN IF NOT EXISTS molit_umd_name TEXT")


def _ensure_postgres_analysis_result_columns(connection: Any) -> None:
    connection.execute("ALTER TABLE analysis_result ALTER COLUMN listing_id DROP NOT NULL")
    connection.execute(
        "ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS target_type TEXT NOT NULL DEFAULT 'LISTING'"
    )
    connection.execute("ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS complex_id BIGINT")
    connection.execute("ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS area_bucket DOUBLE PRECISION")
    connection.execute("ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS price_source TEXT")
    connection.execute(
        "ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS effective_price_snapshot BIGINT"
    )
    connection.execute("ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS reference_price BIGINT")
    connection.execute("ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS sample_count BIGINT")
    connection.execute(
        "ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS latest_transaction_date TEXT"
    )
    connection.execute(
        "ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS selected_transaction_min_price BIGINT"
    )
    connection.execute(
        "ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS selected_transaction_max_price BIGINT"
    )
    connection.execute("ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS confidence TEXT")
    connection.execute("ALTER TABLE analysis_result ADD COLUMN IF NOT EXISTS volatility_status TEXT")


def _prepare_query(database_path: Path | str, query: str) -> str:
    prepared_query = query
    if is_postgres_target(database_path):
        prepared_query = prepared_query.replace("?", "%s")
        if _is_insert_query(query) and "RETURNING" not in prepared_query.upper():
            table_name = _extract_insert_table_name(query)
            primary_key_column = _primary_key_column(table_name)
            prepared_query = f"{prepared_query.rstrip()} RETURNING {primary_key_column}"
    return prepared_query


def _is_insert_query(query: str) -> bool:
    return bool(INSERT_TABLE_PATTERN.search(query))


def _extract_insert_table_name(query: str) -> str:
    matched = INSERT_TABLE_PATTERN.search(query)
    if matched is None:
        raise ValueError("Unable to determine insert target table.")
    return matched.group(1).lower()


def _primary_key_column(table_name: str) -> str:
    if table_name == "policy_event":
        return "policy_event_id"
    return "id"


def _extract_inserted_id(row: Any) -> int:
    if row is None:
        return 0
    if isinstance(row, Mapping):
        value = next(iter(row.values()), 0)
        return int(value or 0)
    if isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray)):
        return int(row[0] or 0)
    return int(row or 0)


def _normalize_row(row: Any) -> dict | None:
    if row is None:
        return None
    return {key: _normalize_value(value) for key, value in dict(row).items()}


def _normalize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _analysis_result_table_sql_for_name(table_name: str) -> str:
    return ANALYSIS_RESULT_TABLE_SQL.replace(
        "CREATE TABLE IF NOT EXISTS analysis_result",
        f"CREATE TABLE {table_name}",
        1,
    )


def _load_postgres_schema_statements() -> list[str]:
    schema_sql_parts = [
        path.read_text(encoding="utf-8")
        for path in sorted(POSTGRES_MIGRATIONS_DIR.glob("*.sql"))
    ]
    schema_sql = "\n".join(schema_sql_parts)
    return _split_sql_statements(schema_sql)


def _split_sql_statements(schema_sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    dollar_tag: str | None = None
    index = 0

    while index < len(schema_sql):
        if dollar_tag is not None:
            if schema_sql.startswith(dollar_tag, index):
                current.append(dollar_tag)
                index += len(dollar_tag)
                dollar_tag = None
                continue
            current.append(schema_sql[index])
            index += 1
            continue

        if schema_sql.startswith("$$", index):
            dollar_tag = "$$"
            current.append(dollar_tag)
            index += len(dollar_tag)
            continue

        char = schema_sql[index]
        if char == "'":
            next_char = schema_sql[index + 1] if index + 1 < len(schema_sql) else ""
            current.append(char)
            index += 1
            if in_single_quote and next_char == "'":
                current.append(next_char)
                index += 1
                continue
            in_single_quote = not in_single_quote
            continue

        if char == ";" and not in_single_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            index += 1
            continue

        current.append(char)
        index += 1

    trailing_statement = "".join(current).strip()
    if trailing_statement:
        statements.append(trailing_statement)
    return statements
