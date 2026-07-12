from __future__ import annotations

from dataclasses import dataclass


ALLOWED_SIDO = {"서울특별시", "경기도", "인천광역시"}
APARTMENT_BD_KDCD = {"1"}


@dataclass(frozen=True)
class AddressCandidate:
    complex_name: str
    road_address: str
    jibun_address: str
    sido: str
    sigungu: str
    emd: str
    li: str
    admin_code: str
    building_management_no: str
    is_apartment: bool


class AddressSearchService:
    def __init__(self, *, juso_address_client) -> None:
        self.juso_address_client = juso_address_client
        self.last_raw_result_count = 0
        self.last_candidate_count = 0

    def search_candidates(
        self,
        *,
        keyword: str,
        current_page: int = 1,
        count_per_page: int = 20,
    ) -> list[AddressCandidate]:
        normalized_keyword = str(keyword or "").strip()
        if len(normalized_keyword) < 2:
            raise ValueError("Address search keyword must be at least 2 characters.")

        raw_rows = self.juso_address_client.search(
            keyword=normalized_keyword,
            current_page=current_page,
            count_per_page=count_per_page,
        )
        self.last_raw_result_count = len(raw_rows)

        candidates: list[AddressCandidate] = []
        seen_keys: set[tuple[str, str]] = set()
        for row in raw_rows:
            candidate = _to_address_candidate(row)
            if candidate is None:
                continue
            dedupe_key = (candidate.complex_name, candidate.road_address)
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            candidates.append(candidate)
            if len(candidates) >= 20:
                break
        self.last_candidate_count = len(candidates)
        return candidates


def _to_address_candidate(row: dict) -> AddressCandidate | None:
    sido = str(row.get("siNm") or "").strip()
    if sido not in ALLOWED_SIDO:
        return None

    bd_kdcd = str(row.get("bdKdcd") or "").strip()
    if bd_kdcd not in APARTMENT_BD_KDCD:
        return None

    complex_name = str(row.get("bdNm") or "").strip()
    road_address = str(row.get("roadAddr") or "").strip()
    if not complex_name or not road_address:
        return None

    return AddressCandidate(
        complex_name=complex_name,
        road_address=road_address,
        jibun_address=str(row.get("jibunAddr") or "").strip(),
        sido=sido,
        sigungu=str(row.get("sggNm") or "").strip(),
        emd=str(row.get("emdNm") or "").strip(),
        li=str(row.get("liNm") or "").strip(),
        admin_code=str(row.get("admCd") or "").strip(),
        building_management_no=str(row.get("bdMgtSn") or "").strip(),
        is_apartment=True,
    )
