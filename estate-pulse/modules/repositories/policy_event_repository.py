from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all, fetch_one
from modules.utils.date_utils import utc_now_iso


class PolicyEventRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create(
        self,
        *,
        policy_type: str,
        title: str,
        summary: str,
        detail: str,
        effective_from: str,
        effective_to: str | None,
        affected_region_sido: str | None,
        affected_region_sigungu: str | None,
        affected_region_dong: str | None,
        affected_buyer_type: str,
        affected_investment_purpose: str,
        impact_level: str,
        calculation_supported: bool,
        action_required: bool,
        source_text: str,
        source_name: str | None,
        status: str,
    ) -> int:
        now = utc_now_iso()
        return execute(
            self.database_path,
            """
            INSERT INTO policy_event (
                policy_type,
                title,
                summary,
                detail,
                effective_from,
                effective_to,
                affected_region_sido,
                affected_region_sigungu,
                affected_region_dong,
                affected_buyer_type,
                affected_investment_purpose,
                impact_level,
                calculation_supported,
                action_required,
                source_text,
                source_name,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                policy_type,
                title,
                summary,
                detail,
                effective_from,
                effective_to,
                affected_region_sido,
                affected_region_sigungu,
                affected_region_dong,
                affected_buyer_type,
                affected_investment_purpose,
                impact_level,
                int(calculation_supported),
                int(action_required),
                source_text,
                source_name,
                status,
                now,
                now,
            ),
        )

    def get(self, policy_event_id: int) -> dict | None:
        row = fetch_one(
            self.database_path,
            "SELECT * FROM policy_event WHERE policy_event_id = ?",
            (policy_event_id,),
        )
        return self._to_row(row)

    def list_all(
        self,
        *,
        policy_type: str | None = None,
        status: str | None = None,
        impact_level: str | None = None,
    ) -> list[dict]:
        filters: list[str] = []
        parameters: list[object] = []
        if policy_type:
            filters.append("policy_type = ?")
            parameters.append(policy_type)
        if status:
            filters.append("status = ?")
            parameters.append(status)
        if impact_level:
            filters.append("impact_level = ?")
            parameters.append(impact_level)

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = fetch_all(
            self.database_path,
            f"""
            SELECT *
            FROM policy_event
            {where_clause}
            ORDER BY
                CASE impact_level
                    WHEN 'HIGH' THEN 1
                    WHEN 'MEDIUM' THEN 2
                    ELSE 3
                END,
                effective_from DESC,
                policy_event_id DESC
            """,
            tuple(parameters),
        )
        return [self._to_row(row) for row in rows]

    def update(
        self,
        policy_event_id: int,
        *,
        policy_type: str,
        title: str,
        summary: str,
        detail: str,
        effective_from: str,
        effective_to: str | None,
        affected_region_sido: str | None,
        affected_region_sigungu: str | None,
        affected_region_dong: str | None,
        affected_buyer_type: str,
        affected_investment_purpose: str,
        impact_level: str,
        calculation_supported: bool,
        action_required: bool,
        source_text: str,
        source_name: str | None,
        status: str,
    ) -> None:
        execute(
            self.database_path,
            """
            UPDATE policy_event
            SET
                policy_type = ?,
                title = ?,
                summary = ?,
                detail = ?,
                effective_from = ?,
                effective_to = ?,
                affected_region_sido = ?,
                affected_region_sigungu = ?,
                affected_region_dong = ?,
                affected_buyer_type = ?,
                affected_investment_purpose = ?,
                impact_level = ?,
                calculation_supported = ?,
                action_required = ?,
                source_text = ?,
                source_name = ?,
                status = ?,
                updated_at = ?
            WHERE policy_event_id = ?
            """,
            (
                policy_type,
                title,
                summary,
                detail,
                effective_from,
                effective_to,
                affected_region_sido,
                affected_region_sigungu,
                affected_region_dong,
                affected_buyer_type,
                affected_investment_purpose,
                impact_level,
                int(calculation_supported),
                int(action_required),
                source_text,
                source_name,
                status,
                utc_now_iso(),
                policy_event_id,
            ),
        )

    def expire(self, policy_event_id: int, *, effective_to: str, status: str) -> None:
        execute(
            self.database_path,
            """
            UPDATE policy_event
            SET effective_to = ?, status = ?, updated_at = ?
            WHERE policy_event_id = ?
            """,
            (effective_to, status, utc_now_iso(), policy_event_id),
        )

    def _to_row(self, row: dict | None) -> dict | None:
        if row is None:
            return None
        updated = dict(row)
        updated["calculation_supported"] = bool(updated.get("calculation_supported"))
        updated["action_required"] = bool(updated.get("action_required"))
        return updated
