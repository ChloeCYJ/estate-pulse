from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

from modules.repositories.complex_repository import ApartmentComplexRepository
from modules.repositories.rent_transaction_repository import RentTransactionRepository
from modules.repositories.sale_transaction_repository import SaleTransactionRepository
from modules.utils.date_utils import utc_now_iso


@dataclass(frozen=True)
class SeedComplex:
    name: str
    sido: str
    sigungu: str
    dong: str
    address: str
    build_year: int
    base_sale_price: int
    base_rent_deposit: int
    areas: tuple[float, ...]


class MockTransactionSeedService:
    def __init__(
        self,
        *,
        complex_repository: ApartmentComplexRepository,
        sale_transaction_repository: SaleTransactionRepository,
        rent_transaction_repository: RentTransactionRepository,
    ) -> None:
        self.complex_repository = complex_repository
        self.sale_transaction_repository = sale_transaction_repository
        self.rent_transaction_repository = rent_transaction_repository

    def seed(self) -> dict:
        seed_complexes = [
            SeedComplex(
                name="샘플리버파크",
                sido="서울",
                sigungu="마포구",
                dong="염리동",
                address="서울 마포구 염리동 101",
                build_year=2018,
                base_sale_price=930_000_000,
                base_rent_deposit=520_000_000,
                areas=(59.8, 84.9),
            ),
            SeedComplex(
                name="샘플센트럴자이",
                sido="서울",
                sigungu="동작구",
                dong="상도동",
                address="서울 동작구 상도동 202",
                build_year=2020,
                base_sale_price=1_080_000_000,
                base_rent_deposit=610_000_000,
                areas=(84.9, 114.2),
            ),
            SeedComplex(
                name="샘플레이크뷰",
                sido="경기",
                sigungu="하남시",
                dong="망월동",
                address="경기 하남시 망월동 303",
                build_year=2021,
                base_sale_price=870_000_000,
                base_rent_deposit=470_000_000,
                areas=(59.6, 84.7),
            ),
        ]

        complex_ids: list[int] = []
        sale_payload: list[dict] = []
        rent_payload: list[dict] = []
        today = date.today()

        for index, seed_complex in enumerate(seed_complexes):
            complex_id = self._get_or_create_complex(seed_complex)
            complex_ids.append(complex_id)

            for area_index, area_m2 in enumerate(seed_complex.areas):
                area_sale_adjustment = area_index * 140_000_000
                area_rent_adjustment = area_index * 90_000_000

                for month_offset in range(12):
                    deal_date = _subtract_months(today, month_offset)
                    safe_day = min(15, calendar.monthrange(deal_date.year, deal_date.month)[1])
                    final_date = deal_date.replace(day=safe_day)
                    seasonal_adjustment = (11 - month_offset) * 7_500_000
                    complex_adjustment = index * 35_000_000

                    sale_payload.append(
                        {
                            "complex_id": complex_id,
                            "complex_name": seed_complex.name,
                            "area_m2": area_m2,
                            "deal_year": final_date.year,
                            "deal_month": final_date.month,
                            "deal_day": final_date.day,
                            "price": seed_complex.base_sale_price
                            + area_sale_adjustment
                            + seasonal_adjustment
                            + complex_adjustment,
                            "floor": 8 + month_offset % 10,
                            "raw_address": seed_complex.address,
                            "created_at": utc_now_iso(),
                        }
                    )
                    rent_payload.append(
                        {
                            "complex_id": complex_id,
                            "complex_name": seed_complex.name,
                            "area_m2": area_m2,
                            "deal_year": final_date.year,
                            "deal_month": final_date.month,
                            "deal_day": final_date.day,
                            "deposit": seed_complex.base_rent_deposit
                            + area_rent_adjustment
                            + seasonal_adjustment
                            + complex_adjustment,
                            "monthly_rent": 0,
                            "floor": 8 + month_offset % 10,
                            "raw_address": seed_complex.address,
                            "created_at": utc_now_iso(),
                        }
                    )

        self.sale_transaction_repository.delete_by_complex_ids(complex_ids)
        self.rent_transaction_repository.delete_by_complex_ids(complex_ids)
        self.sale_transaction_repository.bulk_create(sale_payload)
        self.rent_transaction_repository.bulk_create(rent_payload)

        return {
            "complex_count": len(seed_complexes),
            "sale_transaction_count": len(sale_payload),
            "rent_transaction_count": len(rent_payload),
        }

    def _get_or_create_complex(self, seed_complex: SeedComplex) -> int:
        existing = self.complex_repository.get_by_name(seed_complex.name)
        if existing:
            return int(existing["id"])

        return self.complex_repository.create(
            name=seed_complex.name,
            sido=seed_complex.sido,
            sigungu=seed_complex.sigungu,
            dong=seed_complex.dong,
            address=seed_complex.address,
            build_year=seed_complex.build_year,
            household_count=None,
            lat=None,
            lng=None,
            memo="Phase 2 mock transaction seed",
        )


def _subtract_months(target_date: date, months: int) -> date:
    month_index = target_date.month - months
    year = target_date.year
    while month_index <= 0:
        month_index += 12
        year -= 1

    day = min(target_date.day, calendar.monthrange(year, month_index)[1])
    return date(year, month_index, day)
