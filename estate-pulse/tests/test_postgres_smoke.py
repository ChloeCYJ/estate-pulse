from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import unittest
from urllib.parse import unquote, urlsplit

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

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency for env-gated smoke tests
    psycopg = None


class PostgreSQLSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_database_url = os.getenv("TEST_DATABASE_URL")
        if not self.base_database_url:
            raise RuntimeError("TEST_DATABASE_URL is required for PostgreSQL smoke tests.")
        if psycopg is None:
            raise RuntimeError("psycopg is required for PostgreSQL smoke tests.")
        _assert_safe_test_database_url(self.base_database_url)
        self.database_url = self.base_database_url
        initialize_database(self.database_url)
        self._reset_test_database()

        self.settings = AppSettings(
            app_name="Test",
            database_path=Path("postgres-smoke.db"),
            acquisition_tax_rate=0.011,
            brokerage_fee_rate=0.004,
            legal_fee_fixed=300000,
            contingency_rate=0.005,
            default_ltv_limit=0.6,
            molit_service_key=None,
            reb_service_key=None,
            database_url=self.database_url,
        )
        self.complex_repository = ApartmentComplexRepository(self.database_url)
        self.listing_repository = ManualListingRepository(self.database_url)
        self.finance_repository = UserFinanceProfileRepository(self.database_url)
        self.analysis_repository = AnalysisRepository(self.database_url)
        self.sale_repository = SaleTransactionRepository(self.database_url)
        self.rent_repository = RentTransactionRepository(self.database_url)
        self.analysis_service = AnalysisService(
            settings=self.settings,
            listing_repository=self.listing_repository,
            finance_repository=self.finance_repository,
            analysis_repository=self.analysis_repository,
            sale_transaction_repository=self.sale_repository,
            rent_transaction_repository=self.rent_repository,
            complex_repository=self.complex_repository,
        )

    def tearDown(self) -> None:
        if self.base_database_url and psycopg is not None:
            self._reset_test_database()

    def test_analysis_history_snapshot_round_trip(self) -> None:
        complex_id = self.complex_repository.create(
            name="Postgres Complex",
            sido="Seoul",
            sigungu="Seocho-gu",
            dong="Banpo-dong",
            address="Seoul Seocho-gu Banpo-dong",
            build_year=2020,
            household_count=1200,
            lat=None,
            lng=None,
            memo=None,
        )
        listing_id = self.listing_repository.create(
            complex_id=complex_id,
            area_m2=84.9,
            sale_price=900_000_000,
            expected_jeonse_price=0,
            investment_type="GAP_INVESTMENT",
            floor="10",
            direction="SOUTH",
            condition_memo="",
            source_memo="",
            checked_at="2026-06-13",
        )
        finance_profile_id = self.finance_repository.create(
            cash_amount=300_000_000,
            annual_income=120_000_000,
            existing_debt=0,
            interest_rate=0.04,
            ltv_limit=0.6,
            dsr_limit=0.4,
        )

        self.sale_repository.bulk_create(
            [
                self._sale_tx(complex_id, "2025-11-15", 930_000_000),
                self._sale_tx(complex_id, "2026-01-15", 950_000_000),
                self._sale_tx(complex_id, "2026-03-15", 970_000_000),
                self._sale_tx(complex_id, "2026-04-15", 990_000_000),
                self._sale_tx(complex_id, "2026-05-15", 1_010_000_000),
            ]
        )
        self.rent_repository.bulk_create(
            [
                self._rent_tx(complex_id, "2026-02-15", 520_000_000),
                self._rent_tx(complex_id, "2026-04-15", 540_000_000),
                self._rent_tx(complex_id, "2026-05-10", 560_000_000),
            ]
        )

        result = self.analysis_service.run_analysis(
            listing_id=listing_id,
            finance_profile_id=finance_profile_id,
            benchmarks=BenchmarkInputs(reference_date=date(2026, 6, 13)),
            save_result=True,
        )

        rows = self.analysis_repository.list_recent(limit=5)
        self.assertEqual(len(rows), 1)
        latest = rows[0]

        self.assertEqual(latest["finance_profile_id"], finance_profile_id)
        self.assertEqual(latest["sale_price_snapshot"], 900_000_000)
        self.assertEqual(latest["jeonse_price_snapshot"], 540_000_000)
        self.assertAlmostEqual(latest["area_m2_snapshot"], 84.9)
        self.assertEqual(latest["complex_name_snapshot"], "Postgres Complex")
        self.assertEqual(latest["expected_loan_amount"], result["expected_loan_amount"])
        self.assertEqual(latest["monthly_repayment"], result["monthly_repayment"])
        self.assertEqual(latest["sale_price"], 900_000_000)
        self.assertEqual(latest["expected_jeonse_price"], 540_000_000)
        self.assertEqual(latest["complex_name"], "Postgres Complex")

    def _sale_tx(self, complex_id: int, deal_date: str, price: int) -> dict:
        year, month, day = (int(part) for part in deal_date.split("-"))
        return {
            "complex_id": complex_id,
            "complex_name": "Postgres Complex",
            "area_m2": 84.9,
            "deal_year": year,
            "deal_month": month,
            "deal_day": day,
            "price": price,
            "floor": 10,
            "raw_address": "Seoul Seocho-gu Banpo-dong",
            "created_at": utc_now_iso(),
        }

    def _rent_tx(self, complex_id: int, deal_date: str, deposit: int) -> dict:
        year, month, day = (int(part) for part in deal_date.split("-"))
        return {
            "complex_id": complex_id,
            "complex_name": "Postgres Complex",
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

    def _reset_test_database(self) -> None:
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            connection.execute(
                """
                TRUNCATE TABLE
                    analysis_result,
                    watchlist,
                    manual_listing,
                    apartment_complex,
                    user_finance_profile,
                    sale_transaction,
                    rent_transaction,
                    policy_event,
                    policy_event_candidate,
                    region_policy_status,
                    rule_candidate,
                    policy_import,
                    interest_area
                RESTART IDENTITY CASCADE
                """
            )


class PostgreSQLSmokeGuardTests(unittest.TestCase):
    def test_accepts_test_database_url(self) -> None:
        _assert_safe_test_database_url("postgresql://estate:estate@localhost:5432/estate_pulse_test")

    def test_rejects_non_test_database_url(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "must target a .*_test database"):
            _assert_safe_test_database_url(
                "postgresql://estate:estate@localhost:5432/estate_pulse"
            )

def _assert_safe_test_database_url(database_url: str) -> None:
    database_name = _database_name_from_url(database_url)
    if not database_name.endswith("_test"):
        raise RuntimeError(
            "TEST_DATABASE_URL must target a dedicated *_test database before destructive cleanup can run."
        )


def _database_name_from_url(database_url: str) -> str:
    path = unquote(urlsplit(database_url).path).lstrip("/")
    if not path:
        raise RuntimeError("TEST_DATABASE_URL must include a database name.")
    return path


if __name__ == "__main__":
    unittest.main()
