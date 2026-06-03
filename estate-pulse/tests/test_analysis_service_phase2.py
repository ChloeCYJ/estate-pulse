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


class Phase2AnalysisServiceTests(unittest.TestCase):
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
        self.listing_id = self.listing_repository.create(
            complex_id=self.complex_id,
            area_m2=84.9,
            sale_price=900_000_000,
            expected_jeonse_price=0,
            investment_type="GAP_INVESTMENT",
            floor="10",
            direction="남향",
            condition_memo="",
            source_memo="",
            checked_at="2026-05-27",
        )
        self.profile_id = self.finance_repository.create(
            cash_amount=250_000_000,
            annual_income=None,
            existing_debt=0,
            interest_rate=None,
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

    def test_bargain_score_uses_transaction_derived_values(self) -> None:
        result = self.analysis_service.run_analysis(
            listing_id=self.listing_id,
            finance_profile_id=self.profile_id,
            benchmarks=BenchmarkInputs(reference_date=date(2026, 5, 27)),
            save_result=False,
        )

        self.assertEqual(result["market_metrics"]["sale_avg_6m"], 980_000_000)
        self.assertEqual(result["derived_inputs"]["one_year_high_price"], 1_010_000_000)
        self.assertEqual(result["bargain_score"], 55)
        self.assertEqual(result["region_policy_source"], "default")

    def test_analysis_result_includes_applied_rules_trace(self) -> None:
        result = self.analysis_service.run_analysis(
            listing_id=self.listing_id,
            finance_profile_id=self.profile_id,
            benchmarks=BenchmarkInputs(reference_date=date(2026, 5, 27)),
            save_result=False,
        )

        applied_rules = result["applied_rules"]
        loan_ltv = applied_rules["loan_ltv"]
        self.assertEqual(loan_ltv["base_price"], 900_000_000)
        self.assertEqual(loan_ltv["ltv_method"], "AUTO_RULE")
        self.assertFalse(loan_ltv["manual_ltv_used"])
        self.assertEqual(loan_ltv["applied_region_type"], "NON_REGULATED")
        self.assertIsNotNone(loan_ltv["matched_rule_version"])
        self.assertEqual(loan_ltv["loan_amount_by_ltv"], 540_000_000)
        self.assertEqual(loan_ltv["expected_loan_amount"], 540_000_000)
        self.assertEqual(
            applied_rules["dsr"]["missing_reason"],
            "연소득 정보가 없어 계산하지 않았습니다.",
        )
        self.assertEqual(
            applied_rules["monthly_repayment"]["missing_reason"],
            "금리 또는 대출기간 정보가 없어 계산하지 않았습니다.",
        )

    def test_jeonse_ratio_fallback_uses_rent_transactions(self) -> None:
        result = self.analysis_service.run_analysis(
            listing_id=self.listing_id,
            finance_profile_id=self.profile_id,
            benchmarks=BenchmarkInputs(reference_date=date(2026, 5, 27)),
            save_result=False,
        )

        self.assertEqual(result["expected_jeonse_price"], 540_000_000)
        self.assertAlmostEqual(result["jeonse_ratio"], 60.0)

    def test_finance_profile_manual_ltv_is_used_only_when_enabled(self) -> None:
        manual_profile_id = self.finance_repository.create(
            cash_amount=250_000_000,
            annual_income=None,
            existing_debt=0,
            interest_rate=None,
            ltv_limit=None,
            dsr_limit=None,
            use_manual_ltv=True,
            manual_ltv_rate=0.2,
        )

        result = self.analysis_service.run_analysis(
            listing_id=self.listing_id,
            finance_profile_id=manual_profile_id,
            benchmarks=BenchmarkInputs(reference_date=date(2026, 5, 27)),
            save_result=False,
        )

        self.assertEqual(result["loan_terms"]["ltv_source"], "manual override")
        self.assertEqual(result["loan_terms"]["applied_ltv_rate"], 0.2)
        self.assertEqual(result["expected_loan_amount"], 180_000_000)
        self.assertEqual(result["applied_rules"]["loan_ltv"]["ltv_method"], "MANUAL_OVERRIDE")
        self.assertTrue(result["applied_rules"]["loan_ltv"]["manual_ltv_used"])
        self.assertEqual(
            result["applied_rules"]["loan_ltv"]["manual_ltv_source"],
            "FINANCE_PROFILE",
        )

    def test_sell_owned_real_estate_funding_mode_uses_net_sale_cash(self) -> None:
        replacement_profile_id = self.finance_repository.create(
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
            finance_profile_id=replacement_profile_id,
            benchmarks=BenchmarkInputs(
                reference_date=date(2026, 5, 27),
                funding_mode="SELL_OWNED_REAL_ESTATE",
            ),
            save_result=False,
        )

        self.assertEqual(result["purchase_power"]["sale_net_cash"], 1_000_000_000)
        self.assertEqual(result["purchase_power"]["available_cash_for_purchase"], 1_200_000_000)
        self.assertEqual(result["purchase_power"]["existing_debt_for_loan_screening"], 0)
        self.assertLessEqual(result["shortage_cash"], 0)

    def test_region_policy_auto_resolves_loan_region_type(self) -> None:
        self.region_policy_service.create_region_policy_status(
            region_level="SIGUNGU",
            sido="서울",
            sigungu="서초구",
            dong=None,
            policy_type="REGULATED_AREA",
            effective_from="2026-05-01",
            effective_to=None,
            notes="test",
        )

        result = self.analysis_service.run_analysis(
            listing_id=self.listing_id,
            finance_profile_id=self.profile_id,
            benchmarks=BenchmarkInputs(reference_date=date(2026, 5, 27)),
            save_result=False,
        )

        self.assertEqual(result["resolved_region_type"], "REGULATED")
        self.assertEqual(result["region_policy_source"], "region_policy_status")
        self.assertEqual(result["loan_terms"]["region_type"], "REGULATED")
        self.assertEqual(result["expected_loan_amount"], 270_000_000)

    def test_analysis_returns_active_region_regulation_list(self) -> None:
        complex_row = self.complex_repository.get(self.complex_id)
        for policy_type in (
            "LAND_TRANSACTION_PERMISSION",
            "ADJUSTMENT_TARGET_AREA",
        ):
            self.region_policy_service.create_region_policy_status(
                region_level="SIGUNGU",
                sido=complex_row["sido"],
                sigungu=complex_row["sigungu"],
                dong=None,
                policy_type=policy_type,
                effective_from="2026-05-01",
                effective_to=None,
                notes="test",
            )

        result = self.analysis_service.run_analysis(
            listing_id=self.listing_id,
            finance_profile_id=self.profile_id,
            benchmarks=BenchmarkInputs(reference_date=date(2026, 5, 27)),
            save_result=False,
        )

        policy_types = {item["policy_type"] for item in result["active_region_policies"]}
        self.assertEqual(result["resolved_region_type"], "ADJUSTMENT_TARGET_AREA")
        self.assertEqual(
            policy_types,
            {"LAND_TRANSACTION_PERMISSION", "ADJUSTMENT_TARGET_AREA"},
        )

    def test_analysis_returns_relevant_policy_events(self) -> None:
        self.policy_event_service.create_policy_event(
            policy_type="TAX",
            title="Multi-home tax relief sunset",
            summary="Multi-home tax relief ends soon.",
            detail="Detailed tax guidance",
            effective_from="2026-05-01",
            effective_to="2026-06-30",
            affected_region_sido=None,
            affected_region_sigungu=None,
            affected_region_dong=None,
            affected_buyer_type="NO_HOME",
            affected_investment_purpose="INVESTMENT",
            impact_level="HIGH",
            calculation_supported=False,
            action_required=True,
            source_text="다주택자 양도세 중과 유예 종료 안내",
            source_name="Policy Memo",
        )

        result = self.analysis_service.run_analysis(
            listing_id=self.listing_id,
            finance_profile_id=self.profile_id,
            benchmarks=BenchmarkInputs(reference_date=date(2026, 5, 27)),
            save_result=False,
        )

        self.assertEqual(len(result["relevant_policy_events"]), 1)
        self.assertEqual(result["relevant_policy_events"][0]["title"], "Multi-home tax relief sunset")

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
            "raw_address": "서울 서초구 반포동",
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
            "raw_address": "서울 서초구 반포동",
            "created_at": utc_now_iso(),
        }


if __name__ == "__main__":
    unittest.main()
