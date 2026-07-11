from __future__ import annotations

import calendar
from datetime import date
import re
import unicodedata


class MolitComplexSearchService:
    def __init__(
        self,
        *,
        complex_repository,
        molit_sale_collector,
        lawd_code_service,
    ) -> None:
        self.complex_repository = complex_repository
        self.molit_sale_collector = molit_sale_collector
        self.lawd_code_service = lawd_code_service
        self.last_search_warning: str | None = None

    def search_candidates(
        self,
        *,
        keyword: str,
        months: int = 1,
        max_candidates: int = 20,
        reference_date: date | None = None,
    ) -> list[dict]:
        self.last_search_warning = None
        normalized_keyword = _normalize_search_text(keyword)
        if not normalized_keyword:
            raise ValueError("Apartment search keyword is required.")
        if months <= 0:
            raise ValueError("months must be greater than zero.")
        if max_candidates <= 0:
            raise ValueError("max_candidates must be greater than zero.")

        target_date = reference_date or date.today()
        year_months = list(reversed(_recent_year_months(target_date=target_date, months=months)))
        search_regions = self.lawd_code_service.list_search_regions()
        registered_index = _build_registered_index(self.complex_repository.list_all())

        grouped_candidates: dict[tuple[str, str, str, str, str], dict] = {}
        failed_requests = 0
        total_requests = 0
        for year_month in year_months:
            for region in search_regions:
                total_requests += 1
                try:
                    rows = self.molit_sale_collector.collect(
                        lawd_code=str(region["lawd_code"]),
                        year_month=year_month,
                    )
                except Exception:
                    failed_requests += 1
                    continue
                for row in rows:
                    apt_name = str(row.get("aptNm") or "").strip()
                    if not apt_name:
                        continue
                    if normalized_keyword not in _normalize_search_text(apt_name):
                        continue

                    candidate = _candidate_from_row(
                        row=row,
                        lawd_code=str(region["lawd_code"]),
                        sido=str(region["sido"] or "").strip(),
                        sigungu=str(region.get("sigungu") or "").strip(),
                    )
                    key = (
                        candidate["apt_name"],
                        candidate["sido"],
                        candidate["sigungu"],
                        candidate["dong"],
                        candidate["lawd_cd"],
                    )
                    existing = grouped_candidates.get(key)
                    if existing is None:
                        candidate["count"] = 1
                        candidate["is_registered"] = key in registered_index
                        candidate["existing_complex_id"] = registered_index.get(key)
                        grouped_candidates[key] = candidate
                    else:
                        existing["count"] += 1
                        if _candidate_sort_key(candidate) > _candidate_sort_key(existing):
                            preserved_count = existing["count"]
                            preserved_registered = existing["is_registered"]
                            preserved_complex_id = existing["existing_complex_id"]
                            existing.update(candidate)
                            existing["count"] = preserved_count
                            existing["is_registered"] = preserved_registered
                            existing["existing_complex_id"] = preserved_complex_id

            # Stop once we have enough recent candidates to keep search bounded.
            if len(grouped_candidates) >= max_candidates:
                break

        candidates = list(grouped_candidates.values())
        candidates.sort(key=_candidate_sort_key, reverse=True)
        self.last_search_warning = _build_search_warning(
            failed_requests=failed_requests,
            total_requests=total_requests,
            matched_count=len(candidates),
        )
        if not candidates and failed_requests == total_requests and total_requests > 0:
            raise ValueError(
                "MOLIT 후보 검색 중 API 호출이 모두 실패했습니다. 잠시 후 다시 시도해 주세요."
            )
        return candidates[:max_candidates]

    def build_registration_payload(
        self,
        *,
        candidate: dict,
        memo: str | None = None,
    ) -> dict:
        apt_name = str(candidate.get("apt_name") or candidate.get("aptNm") or "").strip()
        sido = str(candidate.get("sido") or "").strip()
        sigungu = str(candidate.get("sigungu") or "").strip()
        dong = str(candidate.get("dong") or candidate.get("umdNm") or "").strip()

        if not apt_name:
            raise ValueError("Selected MOLIT candidate is missing aptNm.")

        lawd_code = self.lawd_code_service.resolve_lawd_code(
            sido=sido or None,
            sigungu=sigungu or None,
            dong=dong or None,
        )
        if not lawd_code:
            raise ValueError("Failed to resolve LAWD_CD for selected MOLIT candidate.")

        return {
            "name": apt_name,
            "sido": sido,
            "sigungu": sigungu,
            "dong": dong,
            "address": _build_address(sido=sido, sigungu=sigungu, dong=dong),
            "build_year": None,
            "household_count": None,
            "lat": None,
            "lng": None,
            "molit_lawd_cd": lawd_code,
            "molit_apt_name": apt_name,
            "molit_umd_name": dong or None,
            "memo": _build_molit_memo(memo),
        }

    def register_candidate(
        self,
        *,
        candidate: dict,
        memo: str | None = None,
    ) -> int:
        payload = self.build_registration_payload(candidate=candidate, memo=memo)
        return self.complex_repository.create(**payload)


def _candidate_from_row(*, row: dict, lawd_code: str, sido: str, sigungu: str) -> dict:
    dong = str(row.get("umdNm") or "").strip()
    deal_year = _to_int(row.get("dealYear"))
    deal_month = _to_int(row.get("dealMonth"))
    deal_day = _to_int(row.get("dealDay"))
    return {
        "apt_name": str(row.get("aptNm") or "").strip(),
        "lawd_cd": lawd_code,
        "sido": sido,
        "sigungu": sigungu,
        "dong": dong,
        "deal_year": deal_year,
        "deal_month": deal_month,
        "deal_day": deal_day,
        "area_m2": _to_float(row.get("excluUseAr")),
        "price": _to_amount(row.get("dealAmount")),
        "jibun": str(row.get("jibun") or "").strip() or None,
        "count": 0,
        "is_registered": False,
        "existing_complex_id": None,
    }


def _build_registered_index(complex_rows: list[dict]) -> dict[tuple[str, str, str, str, str], int]:
    registered: dict[tuple[str, str, str, str, str], int] = {}
    for row in complex_rows:
        key = (
            str(row.get("molit_apt_name") or row.get("name") or "").strip(),
            str(row.get("sido") or "").strip(),
            str(row.get("sigungu") or "").strip(),
            str(row.get("molit_umd_name") or row.get("dong") or "").strip(),
            str(row.get("molit_lawd_cd") or "").strip(),
        )
        if not key[0]:
            continue
        registered[key] = int(row["id"])
    return registered


def _build_address(*, sido: str, sigungu: str, dong: str) -> str:
    return " ".join(part for part in (sido, sigungu, dong) if part)


def _build_molit_memo(memo: str | None) -> str | None:
    suffix = str(memo or "").strip()
    if suffix:
        return f"MOLIT raw candidate registration | {suffix}"
    return "MOLIT raw candidate registration"


def _build_search_warning(*, failed_requests: int, total_requests: int, matched_count: int) -> str | None:
    if failed_requests <= 0:
        return None
    if matched_count > 0:
        return (
            f"MOLIT 후보 검색 중 일부 API 호출이 실패했습니다. "
            f"partial_result={matched_count}, failed_requests={failed_requests}/{total_requests}"
        )
    return (
        "MOLIT 후보 검색 중 일부 API 호출이 실패했습니다. "
        f"failed_requests={failed_requests}/{total_requests}"
    )


def _candidate_sort_key(candidate: dict) -> tuple[int, int, int, int, int, str, str, str]:
    return (
        int(candidate.get("deal_year") or 0),
        int(candidate.get("deal_month") or 0),
        int(candidate.get("deal_day") or 0),
        int(candidate.get("count") or 0),
        int(candidate.get("price") or 0),
        str(candidate.get("apt_name") or ""),
        str(candidate.get("sido") or ""),
        str(candidate.get("sigungu") or ""),
    )


def _recent_year_months(*, target_date: date, months: int) -> list[str]:
    year_months: list[str] = []
    current = date(target_date.year, target_date.month, 1)
    for offset in range(months):
        year_months.append(f"{current.year:04d}{current.month:02d}")
        current = _subtract_months(current, 1)
    year_months.reverse()
    return year_months


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


def _normalize_search_text(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    normalized = re.sub(r"\s+", "", normalized)
    return "".join(char for char in normalized if _is_search_character(char))


def _is_search_character(char: str) -> bool:
    category = unicodedata.category(char)
    return bool(category) and category[0] in {"L", "N"}


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
