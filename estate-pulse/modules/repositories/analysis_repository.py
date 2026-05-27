from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all
from modules.utils.date_utils import utc_now_iso


class AnalysisRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create(self, payload: dict) -> int:
        return execute(
            self.database_path,
            """
            INSERT INTO analysis_result (
                listing_id,
                required_cash,
                shortage_cash,
                jeonse_ratio,
                discount_vs_recent_avg,
                drop_from_high,
                bargain_score,
                undervalue_score,
                risk_score,
                decision,
                summary,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["listing_id"],
                payload["required_cash"],
                payload["shortage_cash"],
                payload["jeonse_ratio"],
                payload["discount_vs_recent_avg"],
                payload["drop_from_high"],
                payload["bargain_score"],
                payload.get("undervalue_score"),
                payload.get("risk_score"),
                payload["decision"],
                payload["summary"],
                utc_now_iso(),
            ),
        )

    def list_recent(self, limit: int = 20) -> list[dict]:
        return fetch_all(
            self.database_path,
            """
            SELECT ar.*, ml.sale_price, ml.expected_jeonse_price, ac.name AS complex_name
            FROM analysis_result ar
            JOIN manual_listing ml ON ml.id = ar.listing_id
            JOIN apartment_complex ac ON ac.id = ml.complex_id
            ORDER BY ar.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
