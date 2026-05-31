from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, execute_many, fetch_all


class SaleTransactionRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def bulk_create(self, payload: list[dict]) -> None:
        if not payload:
            return

        execute_many(
            self.database_path,
            """
            INSERT INTO sale_transaction (
                complex_id,
                complex_name,
                area_m2,
                deal_year,
                deal_month,
                deal_day,
                price,
                floor,
                raw_address,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item["complex_id"],
                    item["complex_name"],
                    item["area_m2"],
                    item["deal_year"],
                    item["deal_month"],
                    item["deal_day"],
                    item["price"],
                    item.get("floor"),
                    item.get("raw_address"),
                    item["created_at"],
                )
                for item in payload
            ],
        )

    def list_by_complex_area(
        self,
        *,
        complex_id: int,
        area_m2: float,
        area_tolerance: float = 5.0,
    ) -> list[dict]:
        return fetch_all(
            self.database_path,
            """
            SELECT
                *,
                printf('%04d-%02d-%02d', deal_year, deal_month, deal_day) AS deal_date
            FROM sale_transaction
            WHERE complex_id = ?
              AND ABS(area_m2 - ?) <= ?
            ORDER BY deal_year ASC, deal_month ASC, deal_day ASC, id ASC
            """,
            (complex_id, area_m2, area_tolerance),
        )

    def delete_by_complex_ids(self, complex_ids: list[int]) -> None:
        if not complex_ids:
            return

        placeholders = ", ".join("?" for _ in complex_ids)
        execute(
            self.database_path,
            f"DELETE FROM sale_transaction WHERE complex_id IN ({placeholders})",
            tuple(complex_ids),
        )

    def list_all(self) -> list[dict]:
        return fetch_all(
            self.database_path,
            """
            SELECT
                *,
                printf('%04d-%02d-%02d', deal_year, deal_month, deal_day) AS deal_date
            FROM sale_transaction
            ORDER BY deal_year ASC, deal_month ASC, deal_day ASC, id ASC
            """,
        )
