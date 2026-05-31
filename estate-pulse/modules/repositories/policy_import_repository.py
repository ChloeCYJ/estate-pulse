from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all, fetch_one
from modules.utils.date_utils import utc_now_iso


class PolicyImportRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create(
        self,
        *,
        source_text: str,
        source_name: str | None,
        target_rule_type: str,
        effective_date: str | None,
        parser_name: str,
        parser_status: str,
    ) -> int:
        return execute(
            self.database_path,
            """
            INSERT INTO policy_import (
                source_text,
                source_name,
                target_rule_type,
                effective_date,
                parser_name,
                parser_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_text,
                source_name,
                target_rule_type,
                effective_date,
                parser_name,
                parser_status,
                utc_now_iso(),
            ),
        )

    def update_status(self, policy_import_id: int, parser_status: str) -> None:
        execute(
            self.database_path,
            "UPDATE policy_import SET parser_status = ? WHERE id = ?",
            (parser_status, policy_import_id),
        )

    def get(self, policy_import_id: int) -> dict | None:
        return fetch_one(
            self.database_path,
            "SELECT * FROM policy_import WHERE id = ?",
            (policy_import_id,),
        )

    def list_recent(self, limit: int = 20) -> list[dict]:
        return fetch_all(
            self.database_path,
            """
            SELECT *
            FROM policy_import
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
