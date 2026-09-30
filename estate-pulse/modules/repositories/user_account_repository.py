from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any

from modules.repositories.database import execute, fetch_one, get_connection, is_postgres_target
from modules.utils.date_utils import utc_now_iso


class UserAccountRepository:
    def __init__(self, database_path: Path | str) -> None:
        self.database_path = database_path

    def get_by_identity(self, *, issuer: str, subject: str) -> dict | None:
        return fetch_one(
            self.database_path,
            """
            SELECT
                au.id AS user_id,
                ai.id AS identity_id,
                ai.issuer,
                ai.subject,
                ai.provider,
                au.email,
                au.display_name,
                au.is_active,
                au.created_at,
                au.updated_at,
                ai.last_login_at
            FROM auth_identity ai
            JOIN app_user au ON au.id = ai.user_id
            WHERE ai.issuer = ? AND ai.subject = ?
            LIMIT 1
            """,
            (issuer, subject),
        )

    def create_user_with_identity(
        self,
        *,
        issuer: str,
        subject: str,
        provider: str,
        email: str | None,
        display_name: str | None,
    ) -> dict:
        existing = self.get_by_identity(issuer=issuer, subject=subject)
        if existing is not None:
            return existing

        now = utc_now_iso()
        try:
            with get_connection(self.database_path) as connection:
                user_id = self._insert_and_return_id(
                    connection,
                    """
                    INSERT INTO app_user (
                        email, display_name, is_active, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (email, display_name, 1, now, now),
                )
                self._insert_and_return_id(
                    connection,
                    """
                    INSERT INTO auth_identity (
                        user_id, issuer, subject, provider, created_at, last_login_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, issuer, subject, provider, now, now),
                )
        except Exception as exc:
            if not _is_unique_violation(exc):
                raise
            raced_account = self.get_by_identity(issuer=issuer, subject=subject)
            if raced_account is None:
                raise
            return raced_account

        created = self.get_by_identity(issuer=issuer, subject=subject)
        if created is None:
            raise RuntimeError("Created authentication identity could not be reloaded.")
        return created

    def touch_identity(self, *, identity_id: int, provider: str | None = None) -> None:
        if provider is not None:
            execute(
                self.database_path,
                """
                UPDATE auth_identity
                SET provider = ?, last_login_at = ?
                WHERE id = ?
                """,
                (provider, utc_now_iso(), identity_id),
            )
            return
        execute(
            self.database_path,
            "UPDATE auth_identity SET last_login_at = ? WHERE id = ?",
            (utc_now_iso(), identity_id),
        )

    def _insert_and_return_id(
        self,
        connection: Any,
        query: str,
        parameters: tuple[object, ...],
    ) -> int:
        prepared_query = query
        if is_postgres_target(self.database_path):
            prepared_query = prepared_query.replace("?", "%s").rstrip() + " RETURNING id"
        cursor = connection.execute(prepared_query, parameters)
        if not is_postgres_target(self.database_path):
            return int(cursor.lastrowid)

        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Insert did not return an identifier.")
        if isinstance(row, dict):
            return int(row["id"])
        return int(row[0])


def _is_unique_violation(exc: Exception) -> bool:
    if isinstance(exc, sqlite3.IntegrityError):
        return "UNIQUE constraint failed" in str(exc)
    return getattr(exc, "sqlstate", None) == "23505"
