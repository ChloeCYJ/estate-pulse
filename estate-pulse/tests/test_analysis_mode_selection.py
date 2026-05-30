from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from config.settings import AppSettings
from modules.repositories.analysis_repository import AnalysisRepository
from modules.repositories.complex_repository import ApartmentComplexRepository
from modules.repositories.database import initialize_database
from modules.repositories.finance_profile_repository import UserFinanceProfileRepository
from modules.repositories.listing_repository import ManualListingRepository
from modules.repositories.rent_transaction_repository import RentTransactionRepository
from modules.repositories.sale_transaction_repository import SaleTransactionRepository
from modules.services.analysis_service import AnalysisService, BenchmarkInputs
from modules.utils.date_utils import utc_now_iso


class AnalysisModeSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)

        self.settings = AppSettings(
            app_name="Test",
            database_path=self.database_path,
            acquisition_tax_rate=0.011,
            brokerage_fee_rate=0.004,
            legal_fee_fixed=300000,
            contingency_rate=0.005,
            default_ltv_limit=0.6,
            molit_service_key=None,
            reb_service_key=None,
        )
        self.complex_repository = ApartmentComplexRepository(self.database_path)
        self.listing_repository = ManualListingRepository(self.database_path)
        self.finance_repository = UserFinanceProfileRepository(self.database_path)
        self.analysis_repository = AnalysisRepository(self.database_path)
        self.sale_repository = SaleTransactionRepository(self.database_path)
        self.rent_repository = RentTransactionRepository(self.database_path)
        self.analysis_service = AnalysisService(
            settings=self.settings,
            listing_repository=self.listing_repository,
            finance_repository=self.finance_repository,
            analysis_repository=self.analysis_repository,
            sale_transaction_repository=self.sale_repository,
            rent_transaction_repository=self.rent_repository,
        )

        self.complex_id = self.complex_repository.create(
            name="테스트단지",
            sido="서울",
            sigungu="서초구",
            dong="반포동",
            address="서울 서초구 반포동",
            build_year=2020,
            household_count=None,
            lat=None,
            lng=None,
            memo=None,
        )
        self.owner_listing_id = self.listing_repository.create(
            complex_id=self.complex_id,
            area_m2=84.9,
            sale_price=900_000_000,
            expected_jeonse_price=0,
            investment_type="OWNER_OCCUPIED",
            floor="10",
            direction="남향",
            condition_memo="",
            source_memo="",
            checked_at="2026-05-30",
        )
        self.gap_listing_id = self.listing_repository.create(
            complex_id=self.complex_id,
            area_m2=84.9,
            sale_price=900_000_000,
            expected_jeonse_price=520_000_000,
            investment_type="GAP_INVESTMENT",
            floor="10",
            direction="남향",
            condition_memo="",
            source_memo="",
            checked_at="2026-05-30",
        )
        self.profile_id = self.finance_repository.create(
            cash_amount=300_000_000,
            annual_income=120_000_000,
            existing_debt=0,
            interest_rate=0.04,
            ltv_limit=0.6,
            dsr_limit=None,
        )

        self.sale_repository.bulk_create(
            [
                self._sale_tx("2025-11-15", 930_000_000),
                self._sale_tx("2026-01-15", 950_000_000),
                self._sale_tx("2026-03-15", 970_000_000),
                self._sale_tx("2026-04-15", 990_000_000),
                self._sale_tx("2026-05-15", 1_010_000_000),
            ]
        )
        self.rent_repository.bulk_create(
            [
                self._rent_tx("2026-02-15", 520_000_000),
                self._rent_tx("2026-04-15", 540_000_000),
                self._rent_tx("2026-05-10", 560_000_000),
            ]
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_owner_listing_can_be_analyzed_with_investment_view(self) -> None:
        result = self.analysis_service.run_analysis(
            listing_id=self.owner_listing_id,
            finance_profile_id=self.profile_id,
            benchmarks=BenchmarkInputs(
                reference_date=date(2026, 5, 30),
                analysis_mode="INVESTMENT",
            ),
            save_result=False,
        )

        self.assertEqual(result["primary_user_mode"], "INVESTMENT")
        self.assertEqual(result["investment_type"], "GAP_INVESTMENT")
        self.assertEqual(result["gap_amount"], 360_000_000)
        self.assertAlmostEqual(result["jeonse_ratio"], 60.0)

    def test_gap_listing_can_be_analyzed_with_owner_view(self) -> None:
        result = self.analysis_service.run_analysis(
            listing_id=self.gap_listing_id,
            finance_profile_id=self.profile_id,
            benchmarks=BenchmarkInputs(
                reference_date=date(2026, 5, 30),
                analysis_mode="OWNER_OCCUPIED",
            ),
            save_result=False,
        )

        self.assertEqual(result["primary_user_mode"], "OWNER_OCCUPIED")
        self.assertEqual(result["investment_type"], "OWNER_OCCUPIED")
        self.assertEqual(result["required_cash"], 288_300_000)
        self.assertEqual(result["shortage_cash"], -11_700_000)
        self.assertIsNotNone(result["monthly_repayment"])

    def _sale_tx(self, deal_date: str, price: int) -> dict:
        year, month, day = (int(part) for part in deal_date.split("-"))
        return {
            "complex_id": self.complex_id,
            "complex_name": "테스트단지",
            "area_m2": 84.9,
            "deal_year": year,
            "deal_month": month,
            "deal_day": day,
            "price": price,
            "floor": 10,
            "raw_address": "서울 서초구 반포동",
            "created_at": utc_now_iso(),
        }

    def _rent_tx(self, deal_date: str, deposit: int) -> dict:
        year, month, day = (int(part) for part in deal_date.split("-"))
        return {
            "complex_id": self.complex_id,
            "complex_name": "테스트단지",
            "area_m2": 84.9,
            "deal_year": year,
            "deal_month": month,
            "deal_day": day,
            "deposit": deposit,
            "monthly_rent": 0,
            "floor": 10,
            "raw_address": "서울 서초구 반포동",
            "created_at": utc_now_iso(),
        }


if __name__ == "__main__":
    unittest.main()
