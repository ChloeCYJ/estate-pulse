from __future__ import annotations

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
from modules.repositories.watchlist_repository import WatchlistRepository
from modules.services.analysis_service import AnalysisService
from modules.services.market_scoring_service import MarketScoringService
from modules.services.opportunity_service import OpportunityService
from modules.utils.date_utils import utc_now_iso


class OpportunityServicePhase2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)

        settings = AppSettings(
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
        self.watchlist_repository = WatchlistRepository(self.database_path)
        self.market_scoring_service = MarketScoringService(
            complex_repository=self.complex_repository,
            sale_transaction_repository=self.sale_repository,
            rent_transaction_repository=self.rent_repository,
        )
        self.analysis_service = AnalysisService(
            settings=settings,
            listing_repository=self.listing_repository,
            finance_repository=self.finance_repository,
            analysis_repository=self.analysis_repository,
            sale_transaction_repository=self.sale_repository,
            rent_transaction_repository=self.rent_repository,
            market_scoring_service=self.market_scoring_service,
        )
        self.opportunity_service = OpportunityService(
            listing_repository=self.listing_repository,
            analysis_repository=self.analysis_repository,
            watchlist_repository=self.watchlist_repository,
            analysis_service=self.analysis_service,
        )

        self.finance_profile_id = self.finance_repository.create(
            cash_amount=250_000_000,
            annual_income=120_000_000,
            existing_debt=0,
            interest_rate=0.04,
            ltv_limit=0.6,
            dsr_limit=None,
        )

        self.alpha_complex_id = self.complex_repository.create(
            name="Alpha Palace",
            sido="Seoul",
            sigungu="Gangnam",
            dong="Yeoksam",
            address="Yeoksam",
            build_year=2019,
            household_count=1800,
            lat=None,
            lng=None,
            memo=None,
        )
        self.beta_complex_id = self.complex_repository.create(
            name="Beta Hills",
            sido="Seoul",
            sigungu="Gangnam",
            dong="Yeoksam",
            address="Yeoksam",
            build_year=2003,
            household_count=180,
            lat=None,
            lng=None,
            memo=None,
        )
        self.alpha_listing_id = self.listing_repository.create(
            complex_id=self.alpha_complex_id,
            area_m2=84.9,
            sale_price=900_000_000,
            expected_jeonse_price=0,
            investment_type="GAP_INVESTMENT",
            floor="10",
            direction="S",
            condition_memo="",
            source_memo="",
            checked_at="2026-05-30",
        )
        self.beta_listing_id = self.listing_repository.create(
            complex_id=self.beta_complex_id,
            area_m2=84.9,
            sale_price=800_000_000,
            expected_jeonse_price=0,
            investment_type="GAP_INVESTMENT",
            floor="10",
            direction="S",
            condition_memo="",
            source_memo="",
            checked_at="2026-05-30",
        )

        self.sale_repository.bulk_create(
            [
                self._sale_tx(self.alpha_complex_id, "Alpha Palace", "2025-11-15", 950_000_000),
                self._sale_tx(self.alpha_complex_id, "Alpha Palace", "2026-01-15", 960_000_000),
                self._sale_tx(self.alpha_complex_id, "Alpha Palace", "2026-02-15", 970_000_000),
                self._sale_tx(self.alpha_complex_id, "Alpha Palace", "2026-03-15", 980_000_000),
                self._sale_tx(self.alpha_complex_id, "Alpha Palace", "2026-04-15", 990_000_000),
                self._sale_tx(self.alpha_complex_id, "Alpha Palace", "2026-05-15", 1_000_000_000),
                self._sale_tx(self.beta_complex_id, "Beta Hills", "2026-01-20", 810_000_000),
                self._sale_tx(self.beta_complex_id, "Beta Hills", "2026-05-20", 820_000_000),
            ]
        )
        self.rent_repository.bulk_create(
            [
                self._rent_tx(self.alpha_complex_id, "Alpha Palace", "2026-01-10", 340_000_000),
                self._rent_tx(self.alpha_complex_id, "Alpha Palace", "2026-02-10", 350_000_000),
                self._rent_tx(self.alpha_complex_id, "Alpha Palace", "2026-03-10", 360_000_000),
                self._rent_tx(self.alpha_complex_id, "Alpha Palace", "2026-04-10", 370_000_000),
                self._rent_tx(self.alpha_complex_id, "Alpha Palace", "2026-05-10", 380_000_000),
                self._rent_tx(self.beta_complex_id, "Beta Hills", "2026-02-10", 180_000_000),
                self._rent_tx(self.beta_complex_id, "Beta Hills", "2026-05-10", 200_000_000),
            ]
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_comparison_logic_sorts_by_required_cash(self) -> None:
        rows = self.opportunity_service.compare_listings(
            listing_ids=[self.beta_listing_id, self.alpha_listing_id],
            finance_profile_id=self.finance_profile_id,
            sort_field="required_cash",
            ascending=True,
        )

        self.assertEqual(rows[0]["listing_id"], self.alpha_listing_id)
        self.assertLess(rows[0]["required_cash"], rows[1]["required_cash"])
        self.assertIn("complex_grade_label", rows[0])

    def test_ranking_logic_prefers_better_overall_investment_score(self) -> None:
        rows = self.opportunity_service.rank_listings(
            finance_profile_id=self.finance_profile_id,
            ranking_type="investment_score",
        )

        self.assertEqual(rows[0]["listing_id"], self.alpha_listing_id)
        self.assertGreater(rows[0]["investment_score"], rows[1]["investment_score"])

    def test_comparison_handles_listing_without_transaction_data(self) -> None:
        orphan_listing_id = self.listing_repository.create(
            complex_id=self.beta_complex_id,
            area_m2=59.9,
            sale_price=700_000_000,
            expected_jeonse_price=0,
            investment_type="GAP_INVESTMENT",
            floor="5",
            direction="E",
            condition_memo="",
            source_memo="",
            checked_at="2026-05-30",
        )

        rows = self.opportunity_service.compare_listings(
            listing_ids=[self.alpha_listing_id, orphan_listing_id],
            finance_profile_id=self.finance_profile_id,
            sort_field="investment_score",
            ascending=False,
        )

        self.assertEqual(rows[0]["listing_id"], self.alpha_listing_id)
        self.assertFalse(rows[1]["analysis_available"])
        self.assertEqual(rows[1]["analysis_status"], "분석 불가")
        self.assertIn("Recent sale average", rows[1]["analysis_error"])

    def test_watchlist_distinguishes_complex_summary_from_listing_detail(self) -> None:
        self.watchlist_repository.add_complex(self.alpha_complex_id)
        self.watchlist_repository.add_listing(self.alpha_listing_id)

        rows = self.opportunity_service.build_watchlist(
            finance_profile_id=self.finance_profile_id,
        )

        complex_row = next(item for item in rows if item["watch_target"] == "COMPLEX")
        listing_row = next(item for item in rows if item["watch_target"] == "LISTING")

        self.assertEqual(complex_row["summary_basis"], "단지 대표 매물")
        self.assertEqual(listing_row["summary_basis"], "개별 매물")
        self.assertEqual(complex_row["representative_listing_id"], self.alpha_listing_id)
        self.assertEqual(listing_row["representative_listing_id"], self.alpha_listing_id)
        self.assertEqual(complex_row["complex_listing_count"], 1)
        self.assertEqual(listing_row["complex_listing_count"], 1)

    def _sale_tx(self, complex_id: int, complex_name: str, deal_date: str, price: int) -> dict:
        year, month, day = (int(part) for part in deal_date.split("-"))
        return {
            "complex_id": complex_id,
            "complex_name": complex_name,
            "area_m2": 84.9,
            "deal_year": year,
            "deal_month": month,
            "deal_day": day,
            "price": price,
            "floor": 10,
            "raw_address": "Seoul",
            "created_at": utc_now_iso(),
        }

    def _rent_tx(self, complex_id: int, complex_name: str, deal_date: str, deposit: int) -> dict:
        year, month, day = (int(part) for part in deal_date.split("-"))
        return {
            "complex_id": complex_id,
            "complex_name": complex_name,
            "area_m2": 84.9,
            "deal_year": year,
            "deal_month": month,
            "deal_day": day,
            "deposit": deposit,
            "monthly_rent": 0,
            "floor": 10,
            "raw_address": "Seoul",
            "created_at": utc_now_iso(),
        }


if __name__ == "__main__":
    unittest.main()
