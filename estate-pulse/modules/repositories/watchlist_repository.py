from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all
from modules.utils.date_utils import utc_now_iso


class WatchlistRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def add_complex(self, complex_id: int) -> int:
        return execute(
            self.database_path,
            """
            INSERT INTO watchlist (complex_id, listing_id, created_at)
            SELECT ?, NULL, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM watchlist
                WHERE complex_id = ?
                  AND listing_id IS NULL
            )
            """,
            (complex_id, utc_now_iso(), complex_id),
        )

    def add_listing(self, listing_id: int) -> int:
        return execute(
            self.database_path,
            """
            INSERT INTO watchlist (complex_id, listing_id, created_at)
            SELECT NULL, ?, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM watchlist
                WHERE complex_id IS NULL
                  AND listing_id = ?
            )
            """,
            (listing_id, utc_now_iso(), listing_id),
        )

    def list_all(self) -> list[dict]:
        return fetch_all(
            self.database_path,
            """
            SELECT
                w.id,
                w.complex_id,
                w.listing_id,
                w.created_at,
                COALESCE(ml.complex_id, w.complex_id) AS effective_complex_id,
                ac.name AS complex_name,
                ml.sale_price,
                ml.area_m2
            FROM watchlist w
            LEFT JOIN manual_listing ml ON ml.id = w.listing_id
            LEFT JOIN apartment_complex ac ON ac.id = COALESCE(ml.complex_id, w.complex_id)
            ORDER BY w.created_at DESC, w.id DESC
            """,
        )

    def delete(self, watchlist_id: int) -> None:
        execute(
            self.database_path,
            "DELETE FROM watchlist WHERE id = ?",
            (watchlist_id,),
        )
