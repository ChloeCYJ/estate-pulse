from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all, fetch_one
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
                investment_type,
                required_cash,
                shortage_cash,
                current_required_cash,
                future_required_cash,
                monthly_cash_flow,
                acquisition_tax,
                local_education_tax,
                brokerage_fee,
                legal_fee,
                reserve_cost,
                total_transaction_cost,
                applied_tax_rule_version,
                applied_brokerage_rule_version,
                liquidity_score,
                investment_score,
                complex_grade,
                jeonse_ratio,
                discount_vs_recent_avg,
                drop_from_high,
                bargain_score,
                undervalue_score,
                risk_score,
                loan_rule_version,
                decision,
                summary,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["listing_id"],
                payload.get("investment_type"),
                payload["required_cash"],
                payload["shortage_cash"],
                payload.get("current_required_cash"),
                payload.get("future_required_cash"),
                payload.get("monthly_cash_flow"),
                payload.get("acquisition_tax"),
                payload.get("local_education_tax"),
                payload.get("brokerage_fee"),
                payload.get("legal_fee"),
                payload.get("reserve_cost"),
                payload.get("total_transaction_cost"),
                payload.get("applied_tax_rule_version"),
                payload.get("applied_brokerage_rule_version"),
                payload.get("liquidity_score"),
                payload.get("investment_score"),
                payload.get("complex_grade"),
                payload["jeonse_ratio"],
                payload["discount_vs_recent_avg"],
                payload["drop_from_high"],
                payload["bargain_score"],
                payload.get("undervalue_score"),
                payload.get("risk_score"),
                payload.get("loan_rule_version"),
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

    def get_latest_by_listing(self, listing_id: int) -> dict | None:
        return fetch_one(
            self.database_path,
            """
            SELECT *
            FROM analysis_result
            WHERE listing_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (listing_id,),
        )

    def get_latest_created_at_by_listing(self, listing_id: int) -> str | None:
        rows = fetch_all(
            self.database_path,
            """
            SELECT created_at
            FROM analysis_result
            WHERE listing_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (listing_id,),
        )
        return rows[0]["created_at"] if rows else None

    def get_latest_created_at_by_complex(self, complex_id: int) -> str | None:
        rows = fetch_all(
            self.database_path,
            """
            SELECT ar.created_at
            FROM analysis_result ar
            JOIN manual_listing ml ON ml.id = ar.listing_id
            WHERE ml.complex_id = ?
            ORDER BY ar.created_at DESC, ar.id DESC
            LIMIT 1
            """,
            (complex_id,),
        )
        return rows[0]["created_at"] if rows else None
