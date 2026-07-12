from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.complex_repository import ApartmentComplexRepository
from modules.repositories.database import initialize_database
from modules.services.lawd_code_service import LawdCodeService
from modules.services.molit_complex_search_service import MolitComplexSearchService


class _FakeMolitSaleCollector:
    def __init__(
        self,
        responses_by_key: dict[tuple[str, str], list[dict]],
        errors_by_key: dict[tuple[str, str], Exception] | None = None,
    ) -> None:
        self.responses_by_key = responses_by_key
        self.errors_by_key = errors_by_key or {}
        self.calls: list[tuple[str, str]] = []
        self.service_key = "test-key"

    def collect(self, *, lawd_code: str, year_month: str) -> list[dict]:
        self.calls.append((lawd_code, year_month))
        error = self.errors_by_key.get((lawd_code, year_month))
        if error is not None:
            raise error
        return list(self.responses_by_key.get((lawd_code, year_month), []))


class MolitComplexSearchServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        self.lawd_path = Path(self.temp_dir.name) / "lawd.txt"
        self.lawd_path.write_text(
            "\t".join(
                [
                    "\ubc95\uc815\ub3d9\ucf54\ub4dc",
                    "\ubc95\uc815\ub3d9\uba85",
                    "\ud3d0\uc9c0\uc5ec\ubd80",
                ]
            )
            + "\n"
            + "\n".join(
                [
                    "1100000000\t\uc11c\uc6b8\ud2b9\ubcc4\uc2dc\t\uc874\uc7ac",
                    "1120000000\t\uc11c\uc6b8\ud2b9\ubcc4\uc2dc \uc131\ub3d9\uad6c\t\uc874\uc7ac",
                    "1120011300\t\uc11c\uc6b8\ud2b9\ubcc4\uc2dc \uc131\ub3d9\uad6c \uae08\ud638\ub3d94\uac00\t\uc874\uc7ac",
                    "2600000000\t\ubd80\uc0b0\uad11\uc5ed\uc2dc\t\uc874\uc7ac",
                    "2635000000\t\ubd80\uc0b0\uad11\uc5ed\uc2dc \ud574\uc6b4\ub300\uad6c\t\uc874\uc7ac",
                    "2635010100\t\ubd80\uc0b0\uad11\uc5ed\uc2dc \ud574\uc6b4\ub300\uad6c \uc6b0\ub3d9\t\uc874\uc7ac",
                ]
            ),
            encoding="utf-8",
        )
        initialize_database(self.database_path)
        self.complex_repository = ApartmentComplexRepository(self.database_path)
        self.lawd_code_service = LawdCodeService(self.lawd_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_search_candidates_returns_grouped_molit_results(self) -> None:
        service = self._service(
            {
                ("11200", "202607"): [
                    self._molit_row(
                        apt_name="\uc11c\uc6b8\uc232 1\ucc28 \ud478\ub974\uc9c0\uc624",
                        dong="\uae08\ud638\ub3d94\uac00",
                        day=3,
                        price="210,000",
                        area_m2="84.98",
                    ),
                    self._molit_row(
                        apt_name="\uc11c\uc6b8\uc232 1\ucc28 \ud478\ub974\uc9c0\uc624",
                        dong="\uae08\ud638\ub3d94\uac00",
                        day=1,
                        price="205,000",
                        area_m2="84.98",
                    ),
                ],
                ("26350", "202607"): [
                    self._molit_row(
                        apt_name="\ud574\uc6b4\ub300\uc790\uc774",
                        dong="\uc6b0\ub3d9",
                        day=2,
                        price="180,000",
                        area_m2="84.91",
                    )
                ],
            }
        )

        results = service.search_candidates(
            keyword="\uc11c\uc6b8\uc232",
            months=1,
            reference_date=date(2026, 7, 8),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["apt_name"], "\uc11c\uc6b8\uc232 1\ucc28 \ud478\ub974\uc9c0\uc624")
        self.assertEqual(results[0]["sido"], "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc")
        self.assertEqual(results[0]["sigungu"], "\uc131\ub3d9\uad6c")
        self.assertEqual(results[0]["dong"], "\uae08\ud638\ub3d94\uac00")
        self.assertEqual(results[0]["lawd_cd"], "11200")
        self.assertEqual(results[0]["count"], 2)
        self.assertEqual(results[0]["deal_day"], 3)
        self.assertEqual(results[0]["price"], 2_100_000_000)
        self.assertFalse(results[0]["is_registered"])

    def test_search_candidates_marks_existing_registered_complex(self) -> None:
        self.complex_repository.create(
            name="\uc11c\uc6b8\uc232 1\ucc28 \ud478\ub974\uc9c0\uc624",
            sido="\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
            sigungu="\uc131\ub3d9\uad6c",
            dong="\uae08\ud638\ub3d94\uac00",
            address="\uc11c\uc6b8\ud2b9\ubcc4\uc2dc \uc131\ub3d9\uad6c \uae08\ud638\ub3d94\uac00",
            build_year=None,
            household_count=None,
            lat=None,
            lng=None,
            molit_lawd_cd="11200",
            molit_apt_name="\uc11c\uc6b8\uc232 1\ucc28 \ud478\ub974\uc9c0\uc624",
            molit_umd_name="\uae08\ud638\ub3d94\uac00",
            memo=None,
        )
        service = self._service(
            {
                ("11200", "202607"): [
                    self._molit_row(
                        apt_name="\uc11c\uc6b8\uc232 1\ucc28 \ud478\ub974\uc9c0\uc624",
                        dong="\uae08\ud638\ub3d94\uac00",
                    )
                ]
            }
        )

        results = service.search_candidates(
            keyword="\uc11c\uc6b8\uc232",
            months=1,
            reference_date=date(2026, 7, 8),
        )

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["is_registered"])
        self.assertIsNotNone(results[0]["existing_complex_id"])

    def test_search_candidates_skips_failed_region_requests_and_keeps_partial_results(self) -> None:
        service = self._service(
            {
                ("11200", "202607"): [
                    self._molit_row(
                        apt_name="\ud589\ub2f9\ud55c\uc9c4\ud0c0\uc6b4",
                        dong="\ud589\ub2f9\ub3d9",
                        day=5,
                    )
                ],
            },
            errors_by_key={
                ("26350", "202607"): RuntimeError("502 Server Error: Bad Gateway"),
            },
        )

        results = service.search_candidates(
            keyword="\ud589\ub2f9",
            months=1,
            reference_date=date(2026, 7, 8),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["apt_name"], "\ud589\ub2f9\ud55c\uc9c4\ud0c0\uc6b4")
        self.assertIn("failed_requests=1/2", str(service.last_search_warning))

    def test_search_candidates_raises_when_all_region_requests_fail(self) -> None:
        service = self._service(
            {},
            errors_by_key={
                ("11200", "202607"): RuntimeError("502 Server Error: Bad Gateway"),
                ("26350", "202607"): RuntimeError("502 Server Error: Bad Gateway"),
            },
        )

        with self.assertRaisesRegex(ValueError, "API 호출이 모두 실패했습니다"):
            service.search_candidates(
                keyword="\ud589\ub2f9",
                months=1,
                reference_date=date(2026, 7, 8),
            )

    def test_build_registration_payload_uses_selected_candidate_and_lawd_resolution(self) -> None:
        service = self._service({})

        payload = service.build_registration_payload(
            candidate={
                "apt_name": "\uc11c\uc6b8\uc2321\ucc28\ud478\ub974\uc9c0\uc624",
                "sido": "\uc11c\uc6b8\uc2dc",
                "sigungu": "\uc131\ub3d9\uad6c",
                "dong": "\uae08\ud638\ub3d94\uac00",
            },
            memo="manual review",
        )

        self.assertEqual(payload["name"], "\uc11c\uc6b8\uc2321\ucc28\ud478\ub974\uc9c0\uc624")
        self.assertEqual(payload["sido"], "\uc11c\uc6b8\uc2dc")
        self.assertEqual(payload["sigungu"], "\uc131\ub3d9\uad6c")
        self.assertEqual(payload["dong"], "\uae08\ud638\ub3d94\uac00")
        self.assertEqual(payload["address"], "\uc11c\uc6b8\uc2dc \uc131\ub3d9\uad6c \uae08\ud638\ub3d94\uac00")
        self.assertEqual(payload["molit_lawd_cd"], "11200")
        self.assertEqual(payload["molit_apt_name"], "\uc11c\uc6b8\uc2321\ucc28\ud478\ub974\uc9c0\uc624")
        self.assertEqual(payload["molit_umd_name"], "\uae08\ud638\ub3d94\uac00")
        self.assertEqual(payload["memo"], "MOLIT raw candidate registration | manual review")

    def test_build_registration_payload_raises_when_lawd_mapping_fails(self) -> None:
        service = self._service({})

        with self.assertRaisesRegex(ValueError, "Failed to resolve LAWD_CD"):
            service.build_registration_payload(
                candidate={
                    "apt_name": "\uc11c\uc6b8\uc2321\ucc28\ud478\ub974\uc9c0\uc624",
                    "sido": "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
                    "sigungu": "\uc131\ub3d9\uad6c",
                    "dong": "\ub9e4\uce6d\uc5c6\uc74c",
                }
            )

    def test_register_candidate_persists_complex_row(self) -> None:
        service = self._service({})

        complex_id = service.register_candidate(
            candidate={
                "apt_name": "\uc11c\uc6b8\uc2321\ucc28\ud478\ub974\uc9c0\uc624",
                "sido": "\uc11c\uc6b8\uc2dc",
                "sigungu": "\uc131\ub3d9\uad6c",
                "dong": "\uae08\ud638\ub3d94\uac00",
            }
        )

        created = self.complex_repository.get(complex_id)
        self.assertIsNotNone(created)
        assert created is not None
        self.assertEqual(created["name"], "\uc11c\uc6b8\uc2321\ucc28\ud478\ub974\uc9c0\uc624")
        self.assertEqual(created["molit_lawd_cd"], "11200")
        self.assertEqual(created["molit_apt_name"], "\uc11c\uc6b8\uc2321\ucc28\ud478\ub974\uc9c0\uc624")
        self.assertEqual(created["molit_umd_name"], "\uae08\ud638\ub3d94\uac00")
        self.assertEqual(created["memo"], "MOLIT raw candidate registration")

    def _service(
        self,
        responses_by_key: dict[tuple[str, str], list[dict]],
        *,
        errors_by_key: dict[tuple[str, str], Exception] | None = None,
    ) -> MolitComplexSearchService:
        return MolitComplexSearchService(
            complex_repository=self.complex_repository,
            molit_sale_collector=_FakeMolitSaleCollector(
                responses_by_key,
                errors_by_key=errors_by_key,
            ),
            lawd_code_service=self.lawd_code_service,
        )

    @staticmethod
    def _molit_row(
        *,
        apt_name: str,
        dong: str,
        day: int = 1,
        price: str = "200,000",
        area_m2: str = "84.98",
    ) -> dict:
        return {
            "aptNm": apt_name,
            "umdNm": dong,
            "jibun": "100",
            "dealYear": "2026",
            "dealMonth": "7",
            "dealDay": str(day),
            "dealAmount": price,
            "excluUseAr": area_m2,
            "floor": "12",
        }


if __name__ == "__main__":
    unittest.main()
