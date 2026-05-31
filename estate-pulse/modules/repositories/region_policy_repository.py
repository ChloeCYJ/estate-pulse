from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all, fetch_one
from modules.utils.date_utils import utc_now_iso


class RegionPolicyRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create(
        self,
        *,
        region_level: str,
        sido: str,
        sigungu: str | None,
        dong: str | None,
        policy_type: str,
        effective_from: str,
        effective_to: str | None,
        notes: str | None,
        source_policy_import_id: int | None = None,
    ) -> int:
        return execute(
            self.database_path,
            """
            INSERT INTO region_policy_status (
                region_level,
                sido,
                sigungu,
                dong,
                policy_type,
                effective_from,
                effective_to,
                notes,
                source_policy_import_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                region_level,
                sido,
                sigungu,
                dong,
                policy_type,
                effective_from,
                effective_to,
                notes,
                source_policy_import_id,
                utc_now_iso(),
            ),
        )

    def get(self, status_id: int) -> dict | None:
        return fetch_one(
            self.database_path,
            "SELECT * FROM region_policy_status WHERE id = ?",
            (status_id,),
        )

    def list_all(self) -> list[dict]:
        return fetch_all(
            self.database_path,
            """
            SELECT *
            FROM region_policy_status
            ORDER BY effective_from DESC, region_level DESC, sido, sigungu, dong, id DESC
            """,
        )

    def delete(self, status_id: int) -> None:
        execute(
            self.database_path,
            "DELETE FROM region_policy_status WHERE id = ?",
            (status_id,),
        )
