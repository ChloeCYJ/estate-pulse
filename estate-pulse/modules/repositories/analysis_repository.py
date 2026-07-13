from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all, fetch_one
from modules.utils.date_utils import utc_now_iso

TARGET_TYPE_LISTING = "LISTING"
TARGET_TYPE_COMPLEX_AREA = "COMPLEX_AREA"


class AnalysisRepository:
    def __init__(self, database_path: Path | str) -> None:
        self.database_path = database_path

    def create(self, payload: dict) -> int:
        return execute(
            self.database_path,
            """
            INSERT INTO analysis_result (
                target_type,
                listing_id,
                complex_id,
                area_bucket,
                price_source,
                effective_price_snapshot,
                reference_price,
                sample_count,
                latest_transaction_date,
                selected_transaction_min_price,
                selected_transaction_max_price,
                confidence,
                volatility_status,
                finance_profile_id,
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
                sale_price_snapshot,
                jeonse_price_snapshot,
                area_m2_snapshot,
                complex_name_snapshot,
                available_cash_snapshot,
                annual_income_snapshot,
                buyer_type_snapshot,
                expected_loan_amount,
                monthly_repayment,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("target_type", self._default_target_type(payload)),
                payload.get("listing_id"),
                payload.get("complex_id"),
                payload.get("area_bucket"),
                payload.get("price_source"),
                payload.get("effective_price_snapshot"),
                payload.get("reference_price"),
                payload.get("sample_count"),
                payload.get("latest_transaction_date"),
                payload.get("selected_transaction_min_price"),
                payload.get("selected_transaction_max_price"),
                payload.get("confidence"),
                payload.get("volatility_status"),
                payload.get("finance_profile_id"),
                payload.get("investment_type"),
                payload.get("required_cash"),
                payload.get("shortage_cash"),
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
                payload.get("sale_price_snapshot"),
                payload.get("jeonse_price_snapshot"),
                payload.get("area_m2_snapshot"),
                payload.get("complex_name_snapshot"),
                payload.get("available_cash_snapshot"),
                payload.get("annual_income_snapshot"),
                payload.get("buyer_type_snapshot"),
                payload.get("expected_loan_amount"),
                payload.get("monthly_repayment"),
                payload.get("jeonse_ratio"),
                payload.get("discount_vs_recent_avg"),
                payload.get("drop_from_high"),
                payload.get("bargain_score"),
                payload.get("undervalue_score"),
                payload.get("risk_score"),
                payload.get("loan_rule_version"),
                payload.get("decision"),
                payload.get("summary"),
                utc_now_iso(),
            ),
        )

    def list_recent(self, limit: int = 20) -> list[dict]:
        return fetch_all(
            self.database_path,
            """
            SELECT
                ar.*,
                COALESCE(
                    ar.sale_price_snapshot,
                    ar.effective_price_snapshot,
                    ml.sale_price
                ) AS sale_price,
                COALESCE(ar.jeonse_price_snapshot, ml.expected_jeonse_price) AS expected_jeonse_price,
                COALESCE(ar.area_m2_snapshot, ar.area_bucket, ml.area_m2) AS area_m2,
                COALESCE(ar.complex_name_snapshot, ac.name) AS complex_name
            FROM analysis_result ar
            LEFT JOIN manual_listing ml ON ml.id = ar.listing_id
            LEFT JOIN apartment_complex ac ON ac.id = COALESCE(ar.complex_id, ml.complex_id)
            ORDER BY ar.created_at DESC, ar.id DESC
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
            WHERE target_type = ?
              AND listing_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (TARGET_TYPE_LISTING, listing_id),
        )

    def get_latest_by_complex_area(self, *, complex_id: int, area_bucket: float) -> dict | None:
        return fetch_one(
            self.database_path,
            """
            SELECT *
            FROM analysis_result
            WHERE target_type = ?
              AND listing_id IS NULL
              AND complex_id = ?
              AND area_bucket = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (TARGET_TYPE_COMPLEX_AREA, complex_id, area_bucket),
        )

    def get_latest_created_at_by_listing(self, listing_id: int) -> str | None:
        rows = fetch_all(
            self.database_path,
            """
            SELECT created_at
            FROM analysis_result
            WHERE target_type = ?
              AND listing_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (TARGET_TYPE_LISTING, listing_id),
        )
        return rows[0]["created_at"] if rows else None

    def get_latest_created_at_by_complex_area(self, *, complex_id: int, area_bucket: float) -> str | None:
        rows = fetch_all(
            self.database_path,
            """
            SELECT created_at
            FROM analysis_result
            WHERE target_type = ?
              AND listing_id IS NULL
              AND complex_id = ?
              AND area_bucket = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (TARGET_TYPE_COMPLEX_AREA, complex_id, area_bucket),
        )
        return rows[0]["created_at"] if rows else None

    def get_latest_created_at_by_complex(self, complex_id: int) -> str | None:
        rows = fetch_all(
            self.database_path,
            """
            SELECT ar.created_at
            FROM analysis_result ar
            LEFT JOIN manual_listing ml ON ml.id = ar.listing_id
            WHERE COALESCE(
                ar.complex_id,
                CASE
                    WHEN ar.target_type = ? THEN ml.complex_id
                    ELSE NULL
                END
            ) = ?
            ORDER BY ar.created_at DESC, ar.id DESC
            LIMIT 1
            """,
            (TARGET_TYPE_LISTING, complex_id),
        )
        return rows[0]["created_at"] if rows else None

    def _default_target_type(self, payload: dict) -> str:
        if payload.get("listing_id") is not None:
            return TARGET_TYPE_LISTING
        return TARGET_TYPE_COMPLEX_AREA
