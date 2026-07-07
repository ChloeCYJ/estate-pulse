from __future__ import annotations

import calendar
from collections import Counter
from datetime import date
import re
import unicodedata

from modules.utils.date_utils import utc_now_iso


class MolitSaleImportNoMatchError(ValueError):
    def __init__(self, *, message: str, candidates: list[dict]) -> None:
        super().__init__(message)
        self.message = message
        self.candidates = candidates

    def __str__(self) -> str:
        if not self.candidates:
            return self.message
        lines = [self.message, "API candidates:"]
        for candidate in self.candidates:
            lines.append(
                f"- aptNm={candidate['aptNm']}, umdNm={candidate['umdNm']}, count={candidate['count']}"
            )
        return "\n".join(lines)


class MolitSaleImportService:
    def __init__(
        self,
        *,
        complex_repository,
        sale_transaction_repository,
        molit_sale_collector,
    ) -> None:
        self.complex_repository = complex_repository
        self.sale_transaction_repository = sale_transaction_repository
        self.molit_sale_collector = molit_sale_collector

    def import_recent_transactions(
        self,
        *,
        complex_id: int,
        lawd_code: str,
        months: int = 12,
        reference_date: date | None = None,
    ) -> dict:
        if months <= 0:
            raise ValueError("months must be greater than zero.")

        complex_row = self.complex_repository.get(complex_id)
        if not complex_row:
            raise ValueError("Apartment complex not found.")

        normalized_lawd_code, expected_complex_name, expected_dong_name = _resolve_matching_context(
            complex_row=complex_row,
            lawd_code=lawd_code,
        )
        if not re.fullmatch(r"\d{5}", normalized_lawd_code):
            raise ValueError("LAWD_CD must be a 5-digit lawd code.")

        target_date = reference_date or date.today()
        year_months = _recent_year_months(target_date=target_date, months=months)

        collected_rows: list[dict] = []
        for year_month in year_months:
            collected_rows.extend(
                self.molit_sale_collector.collect(
                    lawd_code=normalized_lawd_code,
                    year_month=year_month,
                )
            )

        payload, skipped_count = self._build_payload(
            complex_id=int(complex_row["id"]),
            complex_name=str(complex_row["name"]),
            fallback_address=str(complex_row.get("address") or ""),
            expected_complex_name=expected_complex_name,
            expected_dong_name=expected_dong_name,
            collected_rows=collected_rows,
        )
        if not payload:
            raise MolitSaleImportNoMatchError(
                message="No matching MOLIT sale transactions were found.",
                candidates=_collect_api_candidates(collected_rows),
            )

        start_date = _window_start_date(target_date=target_date, months=months).isoformat()
        end_date = target_date.isoformat()
        deleted_count = self.sale_transaction_repository.delete_by_complex_and_date_range(
            complex_id=int(complex_row["id"]),
            start_date=start_date,
            end_date=end_date,
        )
        self.sale_transaction_repository.bulk_create(payload)

        return {
            "complex_id": int(complex_row["id"]),
            "complex_name": complex_row["name"],
            "lawd_code": normalized_lawd_code,
            "year_months": year_months,
            "window_start_date": start_date,
            "window_end_date": end_date,
            "raw_row_count": len(collected_rows),
            "imported_row_count": len(payload),
            "deleted_row_count": deleted_count,
            "skipped_row_count": skipped_count,
        }

    def _build_payload(
        self,
        *,
        complex_id: int,
        complex_name: str,
        fallback_address: str,
        expected_complex_name: str,
        expected_dong_name: str,
        collected_rows: list[dict],
    ) -> tuple[list[dict], int]:
        payload: list[dict] = []
        skipped_count = 0
        for row in collected_rows:
            if _normalize_name(row.get("aptNm") or row.get("아파트")) != expected_complex_name:
                continue
            api_dong_name = _normalize_name(row.get("umdNm") or row.get("법정동"))
            if expected_dong_name and api_dong_name and api_dong_name != expected_dong_name:
                continue

            normalized_row = _normalize_sale_row(
                complex_id=complex_id,
                complex_name=complex_name,
                row=row,
                fallback_address=fallback_address,
            )
            if normalized_row is None:
                skipped_count += 1
                continue
            payload.append(normalized_row)

        payload.sort(
            key=lambda item: (
                int(item["deal_year"]),
                int(item["deal_month"]),
                int(item["deal_day"]),
                float(item["area_m2"]),
                int(item["price"]),
            )
        )
        return payload, skipped_count


def _normalize_sale_row(
    *,
    complex_id: int,
    complex_name: str,
    row: dict,
    fallback_address: str,
) -> dict | None:
    area_m2 = _to_float(row.get("excluUseAr") or row.get("전용면적"))
    deal_year = _to_int(row.get("dealYear") or row.get("년"))
    deal_month = _to_int(row.get("dealMonth") or row.get("월"))
    deal_day = _to_int(row.get("dealDay") or row.get("일"))
    price = _to_amount(row.get("dealAmount") or row.get("거래금액"))
    floor = _to_int(row.get("floor") or row.get("층"))

    if area_m2 is None or deal_year is None or deal_month is None or deal_day is None or price is None:
        return None

    umd_name = str(row.get("umdNm") or row.get("법정동") or "").strip()
    jibun = str(row.get("jibun") or row.get("지번") or "").strip()
    raw_address_parts = [part for part in [umd_name, jibun] if part]
    raw_address = " ".join(raw_address_parts) if raw_address_parts else fallback_address

    return {
        "complex_id": complex_id,
        "complex_name": complex_name,
        "area_m2": area_m2,
        "deal_year": deal_year,
        "deal_month": deal_month,
        "deal_day": deal_day,
        "price": price,
        "floor": floor,
        "raw_address": raw_address,
        "created_at": utc_now_iso(),
    }


def _recent_year_months(*, target_date: date, months: int) -> list[str]:
    year_months: list[str] = []
    current = date(target_date.year, target_date.month, 1)
    for offset in range(months):
        year_months.append(f"{current.year:04d}{current.month:02d}")
        current = _subtract_months(current, 1)
    year_months.reverse()
    return year_months


def _window_start_date(*, target_date: date, months: int) -> date:
    return _subtract_months(target_date, months)


def _subtract_months(target_date: date, months: int) -> date:
    month = target_date.month - months
    year = target_date.year
    while month <= 0:
        month += 12
        year -= 1
    day = min(target_date.day, _last_day_of_month(year=year, month=month))
    return date(year, month, day)


def _last_day_of_month(*, year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _resolve_matching_context(*, complex_row: dict, lawd_code: str) -> tuple[str, str, str]:
    normalized_lawd_code = lawd_code.strip()
    if _has_complete_molit_mapping(complex_row):
        return (
            normalized_lawd_code or str(complex_row.get("molit_lawd_cd") or "").strip(),
            _normalize_name(complex_row.get("molit_apt_name")),
            _normalize_name(complex_row.get("molit_umd_name")),
        )

    return (
        normalized_lawd_code,
        _normalize_name(complex_row.get("name")),
        _normalize_name(complex_row.get("dong")),
    )


def _normalize_name(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    normalized = re.sub(r"\s+", "", normalized)
    return "".join(char for char in normalized if _is_name_character(char))


def _has_complete_molit_mapping(complex_row: dict) -> bool:
    return all(
        _has_text(complex_row.get(key))
        for key in ("molit_lawd_cd", "molit_apt_name", "molit_umd_name")
    )


def _has_text(value: object) -> bool:
    return bool(str(value or "").strip())


def _is_name_character(char: str) -> bool:
    category = unicodedata.category(char)
    return bool(category) and category[0] in {"L", "N"}


def _collect_api_candidates(collected_rows: list[dict], limit: int = 20) -> list[dict]:
    candidate_counter: Counter[tuple[str, str]] = Counter()
    for row in collected_rows:
        apt_name = str(row.get("aptNm") or row.get("아파트") or "").strip()
        umd_name = str(row.get("umdNm") or row.get("법정동") or "").strip()
        if not apt_name and not umd_name:
            continue
        candidate_counter[(apt_name, umd_name)] += 1

    candidates: list[dict] = []
    for (apt_name, umd_name), count in candidate_counter.most_common(limit):
        candidates.append(
            {
                "aptNm": apt_name or "-",
                "umdNm": umd_name or "-",
                "count": int(count),
            }
        )
    return candidates


def _to_amount(value: object) -> int | None:
    if value in (None, ""):
        return None
    digits = re.sub(r"[^0-9]", "", str(value))
    if not digits:
        return None
    return int(digits)


def _to_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    digits = re.sub(r"[^0-9-]", "", str(value))
    if not digits:
        return None
    return int(digits)


def _to_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None
