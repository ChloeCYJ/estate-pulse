from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all, fetch_one
from modules.utils.date_utils import utc_now_iso


class ManualListingRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create(
        self,
        *,
        complex_id: int,
        area_m2: float,
        sale_price: int,
        expected_jeonse_price: int,
        investment_type: str | None = None,
        takeover_jeonse_deposit: int = 0,
        rent_deposit: int = 0,
        expected_monthly_rent: int = 0,
        floor: str,
        direction: str,
        condition_memo: str,
        source_memo: str,
        checked_at: str,
    ) -> int:
        return execute(
            self.database_path,
            """
            INSERT INTO manual_listing (
                complex_id, area_m2, sale_price, expected_jeonse_price, investment_type,
                takeover_jeonse_deposit, rent_deposit, expected_monthly_rent, floor,
                direction, condition_memo, source_memo, checked_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                complex_id,
                area_m2,
                sale_price,
                expected_jeonse_price,
                investment_type,
                takeover_jeonse_deposit,
                rent_deposit,
                expected_monthly_rent,
                floor,
                direction,
                condition_memo,
                source_memo,
                checked_at,
                utc_now_iso(),
            ),
        )

    def get(self, listing_id: int) -> dict | None:
        row = fetch_one(
            self.database_path,
            """
            SELECT ml.*, ac.name AS complex_name
            FROM manual_listing ml
            JOIN apartment_complex ac ON ac.id = ml.complex_id
            WHERE ml.id = ?
            """,
            (listing_id,),
        )
        return self._with_effective_investment_type(row)

    def list_all(self) -> list[dict]:
        rows = fetch_all(
            self.database_path,
            """
            SELECT ml.*, ac.name AS complex_name
            FROM manual_listing ml
            JOIN apartment_complex ac ON ac.id = ml.complex_id
            ORDER BY ml.created_at DESC
            """,
        )
        return [self._with_effective_investment_type(row) for row in rows]

    def list_by_complex(self, complex_id: int) -> list[dict]:
        rows = fetch_all(
            self.database_path,
            """
            SELECT ml.*, ac.name AS complex_name
            FROM manual_listing ml
            JOIN apartment_complex ac ON ac.id = ml.complex_id
            WHERE ml.complex_id = ?
            ORDER BY ml.created_at DESC
            """,
            (complex_id,),
        )
        return [self._with_effective_investment_type(row) for row in rows]

    def update(
        self,
        listing_id: int,
        *,
        complex_id: int,
        area_m2: float,
        sale_price: int,
        expected_jeonse_price: int,
        investment_type: str | None = None,
        takeover_jeonse_deposit: int = 0,
        rent_deposit: int = 0,
        expected_monthly_rent: int = 0,
        floor: str,
        direction: str,
        condition_memo: str,
        source_memo: str,
        checked_at: str,
    ) -> None:
        execute(
            self.database_path,
            """
            UPDATE manual_listing
            SET
                complex_id = ?,
                area_m2 = ?,
                sale_price = ?,
                expected_jeonse_price = ?,
                investment_type = ?,
                takeover_jeonse_deposit = ?,
                rent_deposit = ?,
                expected_monthly_rent = ?,
                floor = ?,
                direction = ?,
                condition_memo = ?,
                source_memo = ?,
                checked_at = ?
            WHERE id = ?
            """,
            (
                complex_id,
                area_m2,
                sale_price,
                expected_jeonse_price,
                investment_type,
                takeover_jeonse_deposit,
                rent_deposit,
                expected_monthly_rent,
                floor,
                direction,
                condition_memo,
                source_memo,
                checked_at,
                listing_id,
            ),
        )

    def delete(self, listing_id: int) -> None:
        execute(
            self.database_path,
            "DELETE FROM manual_listing WHERE id = ?",
            (listing_id,),
        )

    def _with_effective_investment_type(self, row: dict | None) -> dict | None:
        if not row:
            return row

        effective_investment_type = row.get("investment_type")
        if not effective_investment_type:
            expected_jeonse_price = int(row.get("expected_jeonse_price") or 0)
            effective_investment_type = (
                "GAP_INVESTMENT" if expected_jeonse_price > 0 else "OWNER_OCCUPIED"
            )

        updated_row = dict(row)
        updated_row["effective_investment_type"] = effective_investment_type
        return updated_row
