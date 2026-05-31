from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all, fetch_one
from modules.utils.date_utils import utc_now_iso


class RuleCandidateRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create(
        self,
        *,
        policy_import_id: int,
        target_rule_type: str,
        rule_name: str,
        rule_version: str | None,
        previous_rule_json: str | None,
        proposed_rule_json: str,
        changed_fields_json: str | None,
        confidence: float | None,
        warnings: str | None,
        status: str,
    ) -> int:
        return execute(
            self.database_path,
            """
            INSERT INTO rule_candidate (
                policy_import_id,
                target_rule_type,
                rule_name,
                rule_version,
                previous_rule_json,
                proposed_rule_json,
                changed_fields_json,
                confidence,
                warnings,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                policy_import_id,
                target_rule_type,
                rule_name,
                rule_version,
                previous_rule_json,
                proposed_rule_json,
                changed_fields_json,
                confidence,
                warnings,
                status,
                utc_now_iso(),
            ),
        )

    def get(self, candidate_id: int) -> dict | None:
        return fetch_one(
            self.database_path,
            "SELECT * FROM rule_candidate WHERE id = ?",
            (candidate_id,),
        )

    def list_by_policy_import(self, policy_import_id: int) -> list[dict]:
        return fetch_all(
            self.database_path,
            """
            SELECT *
            FROM rule_candidate
            WHERE policy_import_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (policy_import_id,),
        )

    def list_applied_by_type(self, target_rule_type: str) -> list[dict]:
        return fetch_all(
            self.database_path,
            """
            SELECT *
            FROM rule_candidate
            WHERE target_rule_type = ? AND status = 'APPLIED'
            ORDER BY applied_at ASC, id ASC
            """,
            (target_rule_type,),
        )

    def update_candidate_payload(
        self,
        *,
        candidate_id: int,
        proposed_rule_json: str,
        changed_fields_json: str | None,
        warnings: str | None,
        confidence: float | None,
        rule_name: str,
        rule_version: str | None,
    ) -> None:
        execute(
            self.database_path,
            """
            UPDATE rule_candidate
            SET proposed_rule_json = ?,
                changed_fields_json = ?,
                warnings = ?,
                confidence = ?,
                rule_name = ?,
                rule_version = ?
            WHERE id = ?
            """,
            (
                proposed_rule_json,
                changed_fields_json,
                warnings,
                confidence,
                rule_name,
                rule_version,
                candidate_id,
            ),
        )

    def update_status(self, *, candidate_id: int, status: str, timestamp_field: str | None) -> None:
        if timestamp_field == "reviewed_at":
            execute(
                self.database_path,
                "UPDATE rule_candidate SET status = ?, reviewed_at = ? WHERE id = ?",
                (status, utc_now_iso(), candidate_id),
            )
            return
        if timestamp_field == "applied_at":
            execute(
                self.database_path,
                "UPDATE rule_candidate SET status = ?, applied_at = ? WHERE id = ?",
                (status, utc_now_iso(), candidate_id),
            )
            return
        execute(
            self.database_path,
            "UPDATE rule_candidate SET status = ? WHERE id = ?",
            (status, candidate_id),
        )
