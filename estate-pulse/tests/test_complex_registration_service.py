from __future__ import annotations

from dataclasses import dataclass
import unittest

from modules.services.address_search_service import AddressCandidate
from modules.services.complex_registration_service import (
    ComplexAlreadyExistsError,
    ComplexRegistrationService,
    LawdCodeMappingError,
)


@dataclass
class _LawdMatch:
    code: str


class _StubComplexRepository:
    def __init__(self, existing_rows: list[dict] | None = None) -> None:
        self.existing_rows = list(existing_rows or [])
        self.created_payloads: list[dict] = []

    def list_all(self) -> list[dict]:
        return list(self.existing_rows)

    def create(self, **payload) -> int:
        self.created_payloads.append(payload)
        return 101


class _StubLawdCodeService:
    def __init__(self, matches: list[str]) -> None:
        self.matches = matches
        self.calls: list[dict] = []

    def find_lawd_code_matches(self, *, sido: str | None, sigungu: str | None, dong: str | None) -> list[str]:
        self.calls.append({"sido": sido, "sigungu": sigungu, "dong": dong})
        return list(self.matches)


class ComplexRegistrationServiceTests(unittest.TestCase):
    def test_prepare_registration_uses_li_name_when_present(self) -> None:
        service = ComplexRegistrationService(
            complex_repository=_StubComplexRepository(),
            lawd_code_service=_StubLawdCodeService(["1120011300"]),
        )

        preview = service.prepare_registration(
            candidate=self._candidate(li="백현리", emd="행당동", admin_code="1120011300")
        )

        self.assertEqual(preview["dong"], "백현리")
        self.assertEqual(preview["lawd_cd"], "11200")

    def test_prepare_registration_uses_emd_name_when_li_is_missing(self) -> None:
        lawd_code_service = _StubLawdCodeService(["1120011300"])
        service = ComplexRegistrationService(
            complex_repository=_StubComplexRepository(),
            lawd_code_service=lawd_code_service,
        )

        preview = service.prepare_registration(candidate=self._candidate(li="", emd="행당동"))

        self.assertEqual(preview["dong"], "행당동")
        self.assertEqual(lawd_code_service.calls[0]["dong"], "행당동")

    def test_prepare_registration_raises_when_candidate_is_missing(self) -> None:
        service = ComplexRegistrationService(
            complex_repository=_StubComplexRepository(),
            lawd_code_service=_StubLawdCodeService(["1120011300"]),
        )

        with self.assertRaisesRegex(ValueError, "candidate selection is required"):
            service.prepare_registration(candidate=None)

    def test_prepare_registration_raises_when_no_lawd_match_exists(self) -> None:
        service = ComplexRegistrationService(
            complex_repository=_StubComplexRepository(),
            lawd_code_service=_StubLawdCodeService([]),
        )

        with self.assertRaisesRegex(LawdCodeMappingError, "Failed to map LAWD_CD"):
            service.prepare_registration(candidate=self._candidate())

    def test_prepare_registration_raises_when_multiple_lawd_matches_exist(self) -> None:
        service = ComplexRegistrationService(
            complex_repository=_StubComplexRepository(),
            lawd_code_service=_StubLawdCodeService(["1120011300", "1120011400"]),
        )

        with self.assertRaisesRegex(LawdCodeMappingError, "multiple lawd code matches"):
            service.prepare_registration(candidate=self._candidate())

    def test_prepare_registration_raises_when_adm_code_prefix_mismatches_lawd_code(self) -> None:
        service = ComplexRegistrationService(
            complex_repository=_StubComplexRepository(),
            lawd_code_service=_StubLawdCodeService(["1120011300"]),
        )

        with self.assertRaisesRegex(LawdCodeMappingError, "admCd prefix mismatch"):
            service.prepare_registration(candidate=self._candidate(admin_code="1171010100"))

    def test_register_candidate_raises_for_existing_duplicate(self) -> None:
        repository = _StubComplexRepository(
            existing_rows=[
                {
                    "name": "행당한진타운",
                    "sido": "서울특별시",
                    "sigungu": "성동구",
                    "dong": "행당동",
                }
            ]
        )
        service = ComplexRegistrationService(
            complex_repository=repository,
            lawd_code_service=_StubLawdCodeService(["1120011300"]),
        )

        with self.assertRaisesRegex(ComplexAlreadyExistsError, "already exists"):
            service.register_candidate(candidate=self._candidate())

    def test_register_candidate_calls_repository_create_with_expected_payload(self) -> None:
        repository = _StubComplexRepository()
        service = ComplexRegistrationService(
            complex_repository=repository,
            lawd_code_service=_StubLawdCodeService(["1120011300"]),
        )

        complex_id = service.register_candidate(candidate=self._candidate(), memo="address search")

        self.assertEqual(complex_id, 101)
        self.assertEqual(
            repository.created_payloads[0],
            {
                "name": "행당한진타운",
                "sido": "서울특별시",
                "sigungu": "성동구",
                "dong": "행당동",
                "address": "서울특별시 성동구 행당동 346",
                "build_year": None,
                "household_count": None,
                "lat": None,
                "lng": None,
                "molit_lawd_cd": "11200",
                "molit_apt_name": None,
                "molit_umd_name": None,
                "memo": "address search",
            },
        )

    @staticmethod
    def _candidate(
        *,
        li: str = "",
        emd: str = "행당동",
        admin_code: str = "1120011300",
    ) -> AddressCandidate:
        return AddressCandidate(
            complex_name="행당한진타운",
            road_address="서울특별시 성동구 행당로 82",
            jibun_address="서울특별시 성동구 행당동 346",
            sido="서울특별시",
            sigungu="성동구",
            emd=emd,
            li=li,
            admin_code=admin_code,
            building_management_no="1120011300103460000012345",
            is_apartment=True,
        )


if __name__ == "__main__":
    unittest.main()
