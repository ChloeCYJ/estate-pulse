from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all, fetch_one
from modules.utils.date_utils import utc_now_iso


class PolicyEventCandidateRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create(
        self,
        *,
        policy_import_id: int,
        policy_type: str,
        title: str,
        impact_level: str,
        proposed_event_json: str,
        confidence: float | None,
        warnings: str | None,
        status: str,
    ) -> int:
        return execute(
            self.database_path,
            """
            INSERT INTO policy_event_candidate (
                policy_import_id,
                policy_type,
                title,
                impact_level,
                proposed_event_json,
                confidence,
                warnings,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                policy_import_id,
                policy_type,
                title,
                impact_level,
                proposed_event_json,
                confidence,
                warnings,
                status,
                utc_now_iso(),
            ),
        )

    def get(self, candidate_id: int) -> dict | None:
        return fetch_one(
            self.database_path,
            "SELECT * FROM policy_event_candidate WHERE id = ?",
            (candidate_id,),
        )

    def list_by_policy_import(self, policy_import_id: int) -> list[dict]:
        return fetch_all(
            self.database_path,
            """
            SELECT *
            FROM policy_event_candidate
            WHERE policy_import_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (policy_import_id,),
        )

    def update_candidate_payload(
        self,
        *,
        candidate_id: int,
        policy_type: str,
        title: str,
        impact_level: str,
        proposed_event_json: str,
        warnings: str | None,
        confidence: float | None,
    ) -> None:
        execute(
            self.database_path,
            """
            UPDATE policy_event_candidate
            SET
                policy_type = ?,
                title = ?,
                impact_level = ?,
                proposed_event_json = ?,
                warnings = ?,
                confidence = ?
            WHERE id = ?
            """,
            (
                policy_type,
                title,
                impact_level,
                proposed_event_json,
                warnings,
                confidence,
                candidate_id,
            ),
        )

    def update_status(self, *, candidate_id: int, status: str, timestamp_field: str | None) -> None:
        if timestamp_field == "reviewed_at":
            execute(
                self.database_path,
                "UPDATE policy_event_candidate SET status = ?, reviewed_at = ? WHERE id = ?",
                (status, utc_now_iso(), candidate_id),
            )
            return
        if timestamp_field == "applied_at":
            execute(
                self.database_path,
                "UPDATE policy_event_candidate SET status = ?, applied_at = ? WHERE id = ?",
                (status, utc_now_iso(), candidate_id),
            )
            return
        execute(
            self.database_path,
            "UPDATE policy_event_candidate SET status = ? WHERE id = ?",
            (status, candidate_id),
        )
