from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from modules.repositories.complex_repository import ApartmentComplexRepository
from modules.repositories.database import initialize_database
from modules.repositories.sale_transaction_repository import SaleTransactionRepository
from modules.services.molit_sale_import_service import (
    MolitSaleImportNoMatchError,
    MolitSaleImportService,
)
from modules.utils.date_utils import utc_now_iso


class _FakeMolitSaleCollector:
    def __init__(self, responses_by_year_month: dict[str, list[dict]]) -> None:
        self.responses_by_year_month = responses_by_year_month
        self.calls: list[tuple[str, str]] = []

    def collect(self, *, lawd_code: str, year_month: str) -> list[dict]:
        self.calls.append((lawd_code, year_month))
        return list(self.responses_by_year_month.get(year_month, []))


class MolitSaleImportServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)

        self.complex_repository = ApartmentComplexRepository(self.database_path)
        self.sale_transaction_repository = SaleTransactionRepository(self.database_path)
        self.complex_id = self._create_complex(
            name="River Park",
            dong="Banpo-dong",
            address="Seoul Seocho-gu Banpo-dong 100",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_import_recent_transactions_replaces_recent_window_only(self) -> None:
        self.sale_transaction_repository.bulk_create(
            [
                self._tx("2025-06-13", 88.1, 810_000_000),
                self._tx("2026-01-15", 84.9, 900_000_000),
            ]
        )
        expected_year_months = [
            "202507",
            "202508",
            "202509",
            "202510",
            "202511",
            "202512",
            "202601",
            "202602",
            "202603",
            "202604",
            "202605",
            "202606",
        ]
        fake_collector = _FakeMolitSaleCollector(
            {
                year_month: [
                    {
                        "aptNm": "River Park",
                        "umdNm": "Banpo-dong",
                        "jibun": f"{index + 1}",
                        "dealYear": year_month[:4],
                        "dealMonth": str(int(year_month[4:])),
                        "dealDay": "14",
                        "dealAmount": f"{900_000 + index * 10_000:,}",
                        "excluUseAr": "84.90",
                        "floor": "12",
                    },
                    {
                        "aptNm": "Other Complex",
                        "umdNm": "Banpo-dong",
                        "jibun": "99",
                        "dealYear": year_month[:4],
                        "dealMonth": str(int(year_month[4:])),
                        "dealDay": "20",
                        "dealAmount": "999,999",
                        "excluUseAr": "84.90",
                        "floor": "15",
                    },
                ]
                for index, year_month in enumerate(expected_year_months)
            }
        )
        service = MolitSaleImportService(
            complex_repository=self.complex_repository,
            sale_transaction_repository=self.sale_transaction_repository,
            molit_sale_collector=fake_collector,
        )

        result = service.import_recent_transactions(
            complex_id=self.complex_id,
            lawd_code="11680",
            months=12,
            reference_date=date(2026, 6, 14),
        )

        rows = [
            row
            for row in self.sale_transaction_repository.list_all()
            if int(row["complex_id"]) == self.complex_id
        ]

        self.assertEqual(result["deleted_row_count"], 1)
        self.assertEqual(result["imported_row_count"], 12)
        self.assertEqual(result["raw_row_count"], 24)
        self.assertEqual(result["skipped_row_count"], 0)
        self.assertEqual(fake_collector.calls, [("11680", item) for item in expected_year_months])
        self.assertEqual(len(rows), 13)
        self.assertTrue(any(int(row["price"]) == 810_000_000 for row in rows))
        self.assertFalse(any(int(row["price"]) == 900_000_000 for row in rows if row["deal_date"] == "2026-01-15"))

    def test_import_recent_transactions_converts_molit_deal_amount_from_manwon_to_won(self) -> None:
        service = self._build_service(
            {
                "202606": [
                    self._molit_row(
                        apt_name="River Park",
                        umd_name="Banpo-dong",
                        deal_amount="230,000",
                    )
                ]
            }
        )

        service.import_recent_transactions(
            complex_id=self.complex_id,
            lawd_code="11680",
            months=1,
            reference_date=date(2026, 6, 14),
        )

        rows = self.sale_transaction_repository.list_all()

        self.assertEqual(len(rows), 1)
        self.assertEqual(int(rows[0]["price"]), 2_300_000_000)

    def test_import_recent_transactions_returns_candidates_when_no_exact_match_exists(self) -> None:
        service = MolitSaleImportService(
            complex_repository=self.complex_repository,
            sale_transaction_repository=self.sale_transaction_repository,
            molit_sale_collector=_FakeMolitSaleCollector(
                {
                    "202606": [
                        {
                            "aptNm": "Different Complex",
                            "umdNm": "Banpo-dong",
                            "jibun": "1",
                            "dealYear": "2026",
                            "dealMonth": "6",
                            "dealDay": "14",
                            "dealAmount": "950,000",
                            "excluUseAr": "84.90",
                            "floor": "12",
                        },
                        {
                            "aptNm": "River Park 2",
                            "umdNm": "Banpo-dong",
                            "jibun": "2",
                            "dealYear": "2026",
                            "dealMonth": "6",
                            "dealDay": "15",
                            "dealAmount": "960,000",
                            "excluUseAr": "84.90",
                            "floor": "13",
                        },
                        {
                            "aptNm": "Different Complex",
                            "umdNm": "Banpo-dong",
                            "jibun": "3",
                            "dealYear": "2026",
                            "dealMonth": "6",
                            "dealDay": "16",
                            "dealAmount": "970,000",
                            "excluUseAr": "84.90",
                            "floor": "14",
                        }
                    ]
                }
            ),
        )

        with self.assertRaises(MolitSaleImportNoMatchError) as context:
            service.import_recent_transactions(
                complex_id=self.complex_id,
                lawd_code="11680",
                months=1,
                reference_date=date(2026, 6, 14),
            )

        exc = context.exception
        self.assertEqual(exc.message, "No matching MOLIT sale transactions were found.")
        self.assertEqual(
            exc.candidates,
            [
                {"aptNm": "Different Complex", "umdNm": "Banpo-dong", "count": 2},
                {"aptNm": "River Park 2", "umdNm": "Banpo-dong", "count": 1},
            ],
        )
        self.assertIn("API candidates:", str(exc))
        self.assertIn("aptNm=Different Complex, umdNm=Banpo-dong, count=2", str(exc))

    def test_import_recent_transactions_prefers_saved_molit_mapping(self) -> None:
        complex_id = self._create_complex(
            name="\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc6241\ucc28",
            dong="\uae08\ud638\ub3d94\uac00",
            address="\uc11c\uc6b8 \uc131\ub3d9\uad6c \uae08\ud638\ub3d94\uac00 100",
            molit_lawd_cd="11200",
            molit_apt_name="\uc11c\uc6b8\uc2321\ucc28\ud478\ub974\uc9c0\uc624",
            molit_umd_name="\uae08\ud638\ub3d94\uac00",
        )
        fake_collector = _FakeMolitSaleCollector(
            {
                "202606": [
                    self._molit_row(
                        apt_name="\uc11c\uc6b8\uc2321\ucc28\ud478\ub974\uc9c0\uc624",
                        umd_name="\uae08\ud638\ub3d94\uac00",
                    )
                ]
            }
        )
        service = MolitSaleImportService(
            complex_repository=self.complex_repository,
            sale_transaction_repository=self.sale_transaction_repository,
            molit_sale_collector=fake_collector,
        )

        result = service.import_recent_transactions(
            complex_id=complex_id,
            lawd_code="",
            months=1,
            reference_date=date(2026, 6, 14),
        )

        self.assertEqual(result["imported_row_count"], 1)
        self.assertEqual(result["lawd_code"], "11200")
        self.assertEqual(fake_collector.calls, [("11200", "202606")])

    def test_import_recent_transactions_matches_whitespace_difference_after_normalization(self) -> None:
        complex_id = self._create_complex(
            name="\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc6241\ucc28",
            dong="\uae08\ud638\ub3d94\uac00",
            address="\uc11c\uc6b8 \uc131\ub3d9\uad6c \uae08\ud638\ub3d94\uac00 100",
        )

        result = self._import_single_row(
            complex_id=complex_id,
            apt_name="\uc11c\uc6b8\uc232 \ud478\ub974\uc9c0\uc624 1\ucc28",
            umd_name="\uae08\ud638\ub3d94\uac00",
        )

        self.assertEqual(result["imported_row_count"], 1)

    def test_import_recent_transactions_matches_parentheses_difference_after_normalization(self) -> None:
        complex_id = self._create_complex(
            name="\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc6241\ucc28",
            dong="\uae08\ud638\ub3d94\uac00",
            address="\uc11c\uc6b8 \uc131\ub3d9\uad6c \uae08\ud638\ub3d94\uac00 100",
        )

        result = self._import_single_row(
            complex_id=complex_id,
            apt_name="\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc624(1\ucc28)",
            umd_name="\uae08\ud638\ub3d94\uac00",
        )

        self.assertEqual(result["imported_row_count"], 1)

    def test_import_recent_transactions_matches_punctuation_difference_after_normalization(self) -> None:
        complex_id = self._create_complex(
            name="\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc6241\ucc28",
            dong="\uae08\ud638\ub3d94\uac00",
            address="\uc11c\uc6b8 \uc131\ub3d9\uad6c \uae08\ud638\ub3d94\uac00 100",
        )

        for apt_name in [
            "\uc11c\uc6b8\uc232-\ud478\ub974\uc9c0\uc6241\ucc28",
            "\uc11c\uc6b8\uc232.\ud478\ub974\uc9c0\uc6241\ucc28",
            "\uc11c\uc6b8\uc232\u00b7\ud478\ub974\uc9c0\uc6241\ucc28",
        ]:
            with self.subTest(apt_name=apt_name):
                result = self._import_single_row(
                    complex_id=complex_id,
                    apt_name=apt_name,
                    umd_name="\uae08\ud638\ub3d94\uac00",
                )
                self.assertEqual(result["imported_row_count"], 1)

    def test_import_recent_transactions_does_not_match_complexes_with_different_number_suffix(self) -> None:
        complex_id = self._create_complex(
            name="\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc6241\ucc28",
            dong="\uae08\ud638\ub3d94\uac00",
            address="\uc11c\uc6b8 \uc131\ub3d9\uad6c \uae08\ud638\ub3d94\uac00 100",
        )
        service = self._build_service(
            {
                "202606": [
                    self._molit_row(
                        apt_name="\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc624",
                        umd_name="\uae08\ud638\ub3d94\uac00",
                    )
                ]
            }
        )

        with self.assertRaises(MolitSaleImportNoMatchError) as context:
            service.import_recent_transactions(
                complex_id=complex_id,
                lawd_code="11200",
                months=1,
                reference_date=date(2026, 6, 14),
            )

        self.assertEqual(
            context.exception.candidates,
            [{"aptNm": "\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc624", "umdNm": "\uae08\ud638\ub3d94\uac00", "count": 1}],
        )

    def test_import_recent_transactions_does_not_partially_match_dong_name(self) -> None:
        complex_id = self._create_complex(
            name="\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc6241\ucc28",
            dong="\uae08\ud638\ub3d94\uac00",
            address="\uc11c\uc6b8 \uc131\ub3d9\uad6c \uae08\ud638\ub3d94\uac00 100",
        )
        service = self._build_service(
            {
                "202606": [
                    self._molit_row(
                        apt_name="\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc6241\ucc28",
                        umd_name="\uae08\ud6384\uac00",
                    )
                ]
            }
        )

        with self.assertRaises(MolitSaleImportNoMatchError) as context:
            service.import_recent_transactions(
                complex_id=complex_id,
                lawd_code="11200",
                months=1,
                reference_date=date(2026, 6, 14),
            )

        self.assertEqual(
            context.exception.candidates,
            [{"aptNm": "\uc11c\uc6b8\uc232\ud478\ub974\uc9c0\uc6241\ucc28", "umdNm": "\uae08\ud6384\uac00", "count": 1}],
        )

    def test_import_recent_transactions_prioritizes_same_dong_candidates_in_no_match_output(self) -> None:
        complex_id = self._create_complex(
            name="\uc625\uc218\uc0bc\uc131\uc544\ud30c\ud2b8",
            dong="\uc625\uc218\ub3d9",
            address="\uc11c\uc6b8 \uc131\ub3d9\uad6c \uc625\uc218\ub3d9 250",
        )
        service = self._build_service(
            {
                "202606": [
                    self._molit_row(apt_name="센트라스", umd_name="행당동", jibun="1"),
                    self._molit_row(apt_name="센트라스", umd_name="행당동", jibun="2"),
                    self._molit_row(apt_name="센트라스", umd_name="행당동", jibun="3"),
                    self._molit_row(apt_name="옥수삼성", umd_name="옥수동", jibun="250"),
                ]
            }
        )

        with self.assertRaises(MolitSaleImportNoMatchError) as context:
            service.import_recent_transactions(
                complex_id=complex_id,
                lawd_code="11200",
                months=1,
                reference_date=date(2026, 6, 14),
            )

        self.assertEqual(context.exception.candidates[0]["aptNm"], "옥수삼성")
        self.assertEqual(context.exception.candidates[0]["umdNm"], "옥수동")

    def test_import_recent_transactions_returns_more_than_twenty_candidates_when_available(self) -> None:
        service = self._build_service(
            {
                "202606": [
                    self._molit_row(
                        apt_name=f"Different Complex {index}",
                        umd_name="Banpo-dong",
                        jibun=str(index),
                    )
                    for index in range(25)
                ]
            }
        )

        with self.assertRaises(MolitSaleImportNoMatchError) as context:
            service.import_recent_transactions(
                complex_id=self.complex_id,
                lawd_code="11680",
                months=1,
                reference_date=date(2026, 6, 14),
            )

        self.assertEqual(len(context.exception.candidates), 25)

    def _build_service(self, responses_by_year_month: dict[str, list[dict]]) -> MolitSaleImportService:
        return MolitSaleImportService(
            complex_repository=self.complex_repository,
            sale_transaction_repository=self.sale_transaction_repository,
            molit_sale_collector=_FakeMolitSaleCollector(responses_by_year_month),
        )

    def _create_complex(
        self,
        *,
        name: str,
        dong: str,
        address: str,
        molit_lawd_cd: str | None = None,
        molit_apt_name: str | None = None,
        molit_umd_name: str | None = None,
    ) -> int:
        return self.complex_repository.create(
            name=name,
            sido="Seoul",
            sigungu="Seocho-gu",
            dong=dong,
            address=address,
            build_year=2020,
            household_count=800,
            lat=None,
            lng=None,
            molit_lawd_cd=molit_lawd_cd,
            molit_apt_name=molit_apt_name,
            molit_umd_name=molit_umd_name,
            memo=None,
        )

    def _import_single_row(self, *, complex_id: int, apt_name: str, umd_name: str) -> dict:
        service = self._build_service(
            {
                "202606": [
                    self._molit_row(
                        apt_name=apt_name,
                        umd_name=umd_name,
                    )
                ]
            }
        )
        return service.import_recent_transactions(
            complex_id=complex_id,
            lawd_code="11200",
            months=1,
            reference_date=date(2026, 6, 14),
        )

    def _molit_row(
        self,
        *,
        apt_name: str,
        umd_name: str,
        jibun: str = "1",
        deal_day: str = "14",
        deal_amount: str = "950,000",
        area_m2: str = "84.90",
        floor: str = "12",
    ) -> dict:
        return {
            "aptNm": apt_name,
            "umdNm": umd_name,
            "jibun": jibun,
            "dealYear": "2026",
            "dealMonth": "6",
            "dealDay": deal_day,
            "dealAmount": deal_amount,
            "excluUseAr": area_m2,
            "floor": floor,
        }

    def _tx(self, deal_date: str, area_m2: float, price: int) -> dict:
        year, month, day = (int(part) for part in deal_date.split("-"))
        return {
            "complex_id": self.complex_id,
            "complex_name": "River Park",
            "area_m2": area_m2,
            "deal_year": year,
            "deal_month": month,
            "deal_day": day,
            "price": price,
            "floor": 10,
            "raw_address": "Seoul Seocho-gu Banpo-dong 100",
            "created_at": utc_now_iso(),
        }


if __name__ == "__main__":
    unittest.main()
