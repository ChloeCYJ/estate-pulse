from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all, fetch_one
from modules.utils.date_utils import utc_now_iso


class ApartmentComplexRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create(
        self,
        *,
        name: str,
        sido: str,
        sigungu: str,
        dong: str,
        address: str,
        build_year: int | None,
        household_count: int | None,
        lat: float | None,
        lng: float | None,
        memo: str | None = None,
    ) -> int:
        complex_id = execute(
            self.database_path,
            """
            INSERT INTO apartment_complex (
                name, sido, sigungu, dong, address, build_year,
                household_count, lat, lng, memo, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                sido,
                sigungu,
                dong,
                address,
                build_year,
                household_count,
                lat,
                lng,
                memo,
                utc_now_iso(),
            ),
        )
        return complex_id

    def get(self, complex_id: int) -> dict | None:
        return fetch_one(
            self.database_path,
            "SELECT * FROM apartment_complex WHERE id = ?",
            (complex_id,),
        )

    def get_by_name(self, name: str) -> dict | None:
        return fetch_one(
            self.database_path,
            "SELECT * FROM apartment_complex WHERE name = ?",
            (name,),
        )

    def list_all(self) -> list[dict]:
        return fetch_all(
            self.database_path,
            "SELECT * FROM apartment_complex ORDER BY created_at DESC",
        )

    def update(
        self,
        complex_id: int,
        *,
        name: str,
        sido: str,
        sigungu: str,
        dong: str,
        address: str,
        build_year: int | None,
        household_count: int | None,
        lat: float | None,
        lng: float | None,
        memo: str | None = None,
    ) -> None:
        execute(
            self.database_path,
            """
            UPDATE apartment_complex
            SET
                name = ?,
                sido = ?,
                sigungu = ?,
                dong = ?,
                address = ?,
                build_year = ?,
                household_count = ?,
                lat = ?,
                lng = ?,
                memo = ?
            WHERE id = ?
            """,
            (
                name,
                sido,
                sigungu,
                dong,
                address,
                build_year,
                household_count,
                lat,
                lng,
                memo,
                complex_id,
            ),
        )

    def delete(self, complex_id: int) -> None:
        execute(
            self.database_path,
            "DELETE FROM apartment_complex WHERE id = ?",
            (complex_id,),
        )
