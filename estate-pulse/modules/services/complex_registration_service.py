from __future__ import annotations

from modules.services.address_search_service import AddressCandidate


class ComplexRegistrationError(ValueError):
    """Base application error for complex registration flows."""


class ComplexAlreadyExistsError(ComplexRegistrationError):
    """Raised when the selected complex already exists."""


class LawdCodeMappingError(ComplexRegistrationError):
    """Raised when LAWD mapping or cross-validation fails."""


class ComplexRegistrationService:
    def __init__(self, *, complex_repository, lawd_code_service) -> None:
        self.complex_repository = complex_repository
        self.lawd_code_service = lawd_code_service

    def prepare_registration(self, *, candidate: AddressCandidate | None) -> dict:
        if candidate is None:
            raise ValueError("Address candidate selection is required.")

        dong_name = str(candidate.li or candidate.emd or "").strip()
        if not dong_name:
            raise LawdCodeMappingError("Failed to map LAWD_CD because the selected dong is empty.")

        matches = self.lawd_code_service.find_lawd_code_matches(
            sido=candidate.sido,
            sigungu=candidate.sigungu,
            dong=dong_name,
        )
        if not matches:
            raise LawdCodeMappingError("Failed to map LAWD_CD for the selected address candidate.")
        if len(matches) > 1:
            raise LawdCodeMappingError("Failed to map LAWD_CD because multiple lawd code matches exist.")

        lawd_code = str(matches[0])[:5]
        admin_prefix = str(candidate.admin_code or "").strip()[:5]
        if admin_prefix and admin_prefix != lawd_code:
            raise LawdCodeMappingError("admCd prefix mismatch detected for the selected address candidate.")

        return {
            "name": candidate.complex_name,
            "sido": candidate.sido,
            "sigungu": candidate.sigungu,
            "dong": dong_name,
            "address": candidate.jibun_address or candidate.road_address,
            "lawd_cd": lawd_code,
            "road_address": candidate.road_address,
            "jibun_address": candidate.jibun_address,
        }

    def register_candidate(self, *, candidate: AddressCandidate | None, memo: str | None = None) -> int:
        preview = self.prepare_registration(candidate=candidate)
        if self._already_exists(preview):
            raise ComplexAlreadyExistsError("The selected complex already exists.")

        return self.complex_repository.create(
            name=preview["name"],
            sido=preview["sido"],
            sigungu=preview["sigungu"],
            dong=preview["dong"],
            address=preview["address"],
            build_year=None,
            household_count=None,
            lat=None,
            lng=None,
            molit_lawd_cd=preview["lawd_cd"],
            molit_apt_name=None,
            molit_umd_name=None,
            memo=memo,
        )

    def _already_exists(self, preview: dict) -> bool:
        normalized_name = _normalize_text(preview["name"])
        normalized_sido = _normalize_text(preview["sido"])
        normalized_sigungu = _normalize_text(preview["sigungu"])
        normalized_dong = _normalize_text(preview["dong"])

        for row in self.complex_repository.list_all():
            if (
                _normalize_text(row.get("name")) == normalized_name
                and _normalize_text(row.get("sido")) == normalized_sido
                and _normalize_text(row.get("sigungu")) == normalized_sigungu
                and _normalize_text(row.get("dong")) == normalized_dong
            ):
                return True
        return False


def _normalize_text(value: object) -> str:
    return str(value or "").strip().casefold()
