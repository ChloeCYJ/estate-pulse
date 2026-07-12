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
from modules.repositories.policy_event_repository import PolicyEventRepository
from modules.repositories.region_policy_repository import RegionPolicyRepository
from modules.repositories.rent_transaction_repository import RentTransactionRepository
from modules.repositories.sale_transaction_repository import SaleTransactionRepository
from modules.services.analysis_service import AnalysisService, BenchmarkInputs
from modules.services.policy_event_service import PolicyEventService
from modules.services.region_policy_service import RegionPolicyService
from modules.utils.date_utils import utc_now_iso


class SellOwnedRealEstateBuyerTypeTests(unittest.TestCase):
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
        self.policy_event_repository = PolicyEventRepository(self.database_path)
        self.region_policy_repository = RegionPolicyRepository(self.database_path)
        self.region_policy_service = RegionPolicyService(
            region_policy_repository=self.region_policy_repository,
        )
        self.policy_event_service = PolicyEventService(
            policy_event_repository=self.policy_event_repository,
        )
        self.analysis_service = AnalysisService(
            settings=self.settings,
            listing_repository=self.listing_repository,
            finance_repository=self.finance_repository,
            analysis_repository=self.analysis_repository,
            sale_transaction_repository=self.sale_repository,
            rent_transaction_repository=self.rent_repository,
            complex_repository=self.complex_repository,
            region_policy_service=self.region_policy_service,
            policy_event_service=self.policy_event_service,
        )

        self.complex_id = self.complex_repository.create(
            name="Test Complex",
            sido="Seoul",
            sigungu="Seocho-gu",
            dong="Banpo-dong",
            address="Seoul Seocho-gu Banpo-dong",
            build_year=2020,
            household_count=None,
            lat=None,
            lng=None,
            memo=None,
        )
        self.listing_id = self.listing_repository.create(
            complex_id=self.complex_id,
            area_m2=84.9,
            sale_price=900_000_000,
            expected_jeonse_price=0,
            investment_type="GAP_INVESTMENT",
            floor="10",
            direction="South",
            condition_memo="",
            source_memo="",
            checked_at="2026-05-27",
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

    def test_sell_owned_real_estate_treats_one_home_profile_as_no_home_for_loan_rules(self) -> None:
        profile_id = self.finance_repository.create(
            cash_amount=200_000_000,
            annual_income=None,
            existing_debt=400_000_000,
            interest_rate=None,
            ltv_limit=None,
            dsr_limit=None,
            home_count=1,
            owned_real_estate_value=1_400_000_000,
            owned_real_estate_debt=400_000_000,
        )

        result = self.analysis_service.run_analysis(
            listing_id=self.listing_id,
            finance_profile_id=profile_id,
            benchmarks=BenchmarkInputs(
                reference_date=date(2026, 5, 27),
                funding_mode="SELL_OWNED_REAL_ESTATE",
            ),
            save_result=False,
        )

        self.assertEqual(result["resolved_buyer_type"], "NO_HOME")
        self.assertEqual(result["loan_terms"]["buyer_type"], "NO_HOME")
        self.assertEqual(result["expected_loan_amount"], 540_000_000)

    def test_sell_owned_real_estate_reduces_multi_home_profile_by_one_for_loan_rules(self) -> None:
        self.region_policy_service.create_region_policy_status(
            region_level="SIGUNGU",
            sido="Seoul",
            sigungu="Seocho-gu",
            dong=None,
            policy_type="REGULATED_AREA",
            effective_from="2026-05-01",
            effective_to=None,
            notes="test",
        )
        profile_id = self.finance_repository.create(
            cash_amount=200_000_000,
            annual_income=None,
            existing_debt=400_000_000,
            interest_rate=None,
            ltv_limit=None,
            dsr_limit=None,
            home_count=2,
            owned_real_estate_value=1_400_000_000,
            owned_real_estate_debt=400_000_000,
        )

        result = self.analysis_service.run_analysis(
            listing_id=self.listing_id,
            finance_profile_id=profile_id,
            benchmarks=BenchmarkInputs(
                reference_date=date(2026, 5, 27),
                funding_mode="SELL_OWNED_REAL_ESTATE",
            ),
            save_result=False,
        )

        self.assertEqual(result["resolved_buyer_type"], "ONE_HOME")
        self.assertEqual(result["loan_terms"]["buyer_type"], "ONE_HOME")
        self.assertEqual(result["expected_loan_amount"], 180_000_000)

    def _sale_tx(self, deal_date: str, price: int) -> dict:
        year, month, day = (int(part) for part in deal_date.split("-"))
        return {
            "complex_id": self.complex_id,
            "complex_name": "Test Complex",
            "area_m2": 84.9,
            "deal_year": year,
            "deal_month": month,
            "deal_day": day,
            "price": price,
            "floor": 10,
            "raw_address": "Seoul Seocho-gu Banpo-dong",
            "created_at": utc_now_iso(),
        }

    def _rent_tx(self, deal_date: str, deposit: int) -> dict:
        year, month, day = (int(part) for part in deal_date.split("-"))
        return {
            "complex_id": self.complex_id,
            "complex_name": "Test Complex",
            "area_m2": 84.9,
            "deal_year": year,
            "deal_month": month,
            "deal_day": day,
            "deposit": deposit,
            "monthly_rent": 0,
            "floor": 10,
            "raw_address": "Seoul Seocho-gu Banpo-dong",
            "created_at": utc_now_iso(),
        }


if __name__ == "__main__":
    unittest.main()
