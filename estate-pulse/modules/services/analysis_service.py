from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from config.settings import AppSettings
from modules.analyzers.bargain_analyzer import calculate_bargain_score
from modules.analyzers.cash_flow_analyzer import (
    calculate_jeonse_ratio,
    calculate_required_cash,
    calculate_shortage_cash,
)
from modules.analyzers.loan_analyzer import estimate_loan_amount
from modules.analyzers.risk_analyzer import summarize_risk
from modules.analyzers.tax_analyzer import (
    calculate_acquisition_tax,
    calculate_brokerage_fee,
    calculate_contingency_fee,
)
from modules.analyzers.transaction_analyzer import (
    calculate_latest_rent_deposit_average,
    calculate_one_year_high_sale_price,
    calculate_one_year_low_sale_price,
    calculate_recent_12_month_sale_average,
    calculate_recent_3_month_sale_average,
    calculate_recent_6_month_sale_average,
)
from modules.repositories.analysis_repository import AnalysisRepository
from modules.repositories.finance_profile_repository import UserFinanceProfileRepository
from modules.repositories.listing_repository import ManualListingRepository
from modules.repositories.rent_transaction_repository import RentTransactionRepository
from modules.repositories.sale_transaction_repository import SaleTransactionRepository
from modules.services.report_service import build_analysis_summary


@dataclass
class BenchmarkInputs:
    repair_cost: int = 0
    expected_loan_amount: int | None = None
    recent_avg_price_override: int | None = None
    one_year_high_price_override: int | None = None
    expected_jeonse_price_override: int | None = None
    reference_date: date | None = None


class AnalysisService:
    def __init__(
        self,
        *,
        settings: AppSettings,
        listing_repository: ManualListingRepository,
        finance_repository: UserFinanceProfileRepository,
        analysis_repository: AnalysisRepository,
        sale_transaction_repository: SaleTransactionRepository,
        rent_transaction_repository: RentTransactionRepository,
    ) -> None:
        self.settings = settings
        self.listing_repository = listing_repository
        self.finance_repository = finance_repository
        self.analysis_repository = analysis_repository
        self.sale_transaction_repository = sale_transaction_repository
        self.rent_transaction_repository = rent_transaction_repository

    def run_analysis(
        self,
        *,
        listing_id: int,
        finance_profile_id: int,
        benchmarks: BenchmarkInputs,
        save_result: bool = True,
    ) -> dict:
        listing = self.listing_repository.get(listing_id)
        finance_profile = self.finance_repository.get(finance_profile_id)

        if not listing:
            raise ValueError("매물을 찾을 수 없습니다.")
        if not finance_profile:
            raise ValueError("자금 프로필을 찾을 수 없습니다.")

        market_context = self.get_transaction_context(
            listing_id=listing_id,
            benchmarks=benchmarks,
            reference_date=benchmarks.reference_date,
        )

        ltv_limit = finance_profile["ltv_limit"] or self.settings.default_ltv_limit
        expected_loan_amount = benchmarks.expected_loan_amount
        if expected_loan_amount is None:
            expected_loan_amount = estimate_loan_amount(listing["sale_price"], ltv_limit)

        acquisition_tax = calculate_acquisition_tax(
            listing["sale_price"], self.settings.acquisition_tax_rate
        )
        brokerage_fee = calculate_brokerage_fee(
            listing["sale_price"], self.settings.brokerage_fee_rate
        )
        contingency_fee = calculate_contingency_fee(
            listing["sale_price"], self.settings.contingency_rate
        )

        required_cash = calculate_required_cash(
            sale_price=listing["sale_price"],
            expected_loan_amount=expected_loan_amount,
            expected_jeonse_price=market_context["derived_inputs"]["expected_jeonse_price"],
            acquisition_tax=acquisition_tax,
            brokerage_fee=brokerage_fee,
            legal_fee=self.settings.legal_fee_fixed,
            repair_cost=benchmarks.repair_cost,
            contingency_fee=contingency_fee,
        )
        shortage_cash = calculate_shortage_cash(required_cash, finance_profile["cash_amount"])
        jeonse_ratio = calculate_jeonse_ratio(
            market_context["derived_inputs"]["expected_jeonse_price"],
            listing["sale_price"],
        )
        bargain_result = calculate_bargain_score(
            sale_price=listing["sale_price"],
            recent_avg_price=market_context["derived_inputs"]["recent_avg_price"],
            one_year_high_price=market_context["derived_inputs"]["one_year_high_price"],
            expected_jeonse_price=market_context["derived_inputs"]["expected_jeonse_price"],
            required_cash=required_cash,
            user_cash=finance_profile["cash_amount"],
        )
        risks = summarize_risk(shortage_cash=shortage_cash, jeonse_ratio=jeonse_ratio)
        decision = "현재 보유 현금으로 투자 가능" if shortage_cash <= 0 else "추가 현금이 필요합니다"
        summary = build_analysis_summary(
            complex_name=listing["complex_name"],
            listing=listing,
            finance_profile=finance_profile,
            expected_jeonse_price=market_context["derived_inputs"]["expected_jeonse_price"],
            required_cash=required_cash,
            shortage_cash=shortage_cash,
            bargain_result=bargain_result,
            decision=decision,
        )

        result = {
            "listing_id": listing_id,
            "complex_name": listing["complex_name"],
            "sale_price": listing["sale_price"],
            "expected_jeonse_price": market_context["derived_inputs"]["expected_jeonse_price"],
            "expected_loan_amount": expected_loan_amount,
            "required_cash": required_cash,
            "shortage_cash": shortage_cash,
            "jeonse_ratio": jeonse_ratio,
            "discount_vs_recent_avg": bargain_result["discount_rate"],
            "drop_from_high": bargain_result["drop_from_high"],
            "bargain_score": bargain_result["score"],
            "bargain_grade": bargain_result["grade"],
            "reasons": bargain_result["reasons"],
            "risks": risks,
            "decision": decision,
            "summary": summary,
            "costs": {
                "acquisition_tax": acquisition_tax,
                "brokerage_fee": brokerage_fee,
                "legal_fee": self.settings.legal_fee_fixed,
                "repair_cost": benchmarks.repair_cost,
                "contingency_fee": contingency_fee,
            },
            "market_metrics": market_context["market_metrics"],
            "derived_inputs": market_context["derived_inputs"],
            "sale_history": market_context["sale_history"],
            "rent_history": market_context["rent_history"],
            "sources": market_context["sources"],
        }

        if save_result:
            analysis_id = self.analysis_repository.create(
                {
                    "listing_id": listing_id,
                    "required_cash": required_cash,
                    "shortage_cash": shortage_cash,
                    "jeonse_ratio": jeonse_ratio,
                    "discount_vs_recent_avg": bargain_result["discount_rate"],
                    "drop_from_high": bargain_result["drop_from_high"],
                    "bargain_score": bargain_result["score"],
                    "decision": decision,
                    "summary": summary,
                }
            )
            result["analysis_id"] = analysis_id

        return result

    def get_transaction_context(
        self,
        *,
        listing_id: int,
        benchmarks: BenchmarkInputs | None = None,
        reference_date: date | None = None,
    ) -> dict:
        listing = self.listing_repository.get(listing_id)
        if not listing:
            raise ValueError("매물을 찾을 수 없습니다.")

        benchmarks = benchmarks or BenchmarkInputs()
        target_date = reference_date or date.today()
        sale_history = self.sale_transaction_repository.list_by_complex_area(
            complex_id=int(listing["complex_id"]),
            area_m2=float(listing["area_m2"]),
        )
        rent_history = self.rent_transaction_repository.list_by_complex_area(
            complex_id=int(listing["complex_id"]),
            area_m2=float(listing["area_m2"]),
        )

        sale_avg_3m = calculate_recent_3_month_sale_average(sale_history, reference_date=target_date)
        sale_avg_6m = calculate_recent_6_month_sale_average(sale_history, reference_date=target_date)
        sale_avg_12m = calculate_recent_12_month_sale_average(sale_history, reference_date=target_date)
        one_year_high = calculate_one_year_high_sale_price(sale_history, reference_date=target_date)
        one_year_low = calculate_one_year_low_sale_price(sale_history, reference_date=target_date)
        latest_rent_deposit_avg = calculate_latest_rent_deposit_average(
            rent_history,
            reference_date=target_date,
        )

        recent_avg_price, recent_avg_source = self._resolve_recent_avg_price(
            override=benchmarks.recent_avg_price_override,
            sale_avg_6m=sale_avg_6m,
            sale_avg_12m=sale_avg_12m,
        )
        one_year_high_price, one_year_high_source = self._resolve_one_year_high_price(
            override=benchmarks.one_year_high_price_override,
            one_year_high=one_year_high,
        )
        expected_jeonse_price, expected_jeonse_source = self._resolve_expected_jeonse_price(
            listing=listing,
            override=benchmarks.expected_jeonse_price_override,
            latest_rent_deposit_avg=latest_rent_deposit_avg,
        )

        if recent_avg_price is None:
            raise ValueError("최근 매매 실거래 데이터가 없어 최근 평균가를 계산할 수 없습니다.")
        if one_year_high_price is None:
            raise ValueError("최근 1년 매매 실거래 데이터가 없어 최고가를 계산할 수 없습니다.")

        return {
            "market_metrics": {
                "sale_avg_3m": sale_avg_3m,
                "sale_avg_6m": sale_avg_6m,
                "sale_avg_12m": sale_avg_12m,
                "one_year_high": one_year_high,
                "one_year_low": one_year_low,
                "latest_rent_deposit_avg": latest_rent_deposit_avg,
                "sale_transaction_count": len(sale_history),
                "rent_transaction_count": len(rent_history),
            },
            "derived_inputs": {
                "recent_avg_price": recent_avg_price,
                "one_year_high_price": one_year_high_price,
                "expected_jeonse_price": expected_jeonse_price,
            },
            "sources": {
                "recent_avg_price": recent_avg_source,
                "one_year_high_price": one_year_high_source,
                "expected_jeonse_price": expected_jeonse_source,
            },
            "sale_history": sale_history,
            "rent_history": rent_history,
        }

    def _resolve_recent_avg_price(
        self,
        *,
        override: int | None,
        sale_avg_6m: int | None,
        sale_avg_12m: int | None,
    ) -> tuple[int | None, str]:
        if override:
            return override, "수동 입력"
        if sale_avg_6m:
            return sale_avg_6m, "자동 계산 · 최근 6개월 평균"
        if sale_avg_12m:
            return sale_avg_12m, "자동 계산 · 최근 12개월 평균"
        return None, "자동 계산 실패"

    def _resolve_one_year_high_price(
        self,
        *,
        override: int | None,
        one_year_high: int | None,
    ) -> tuple[int | None, str]:
        if override:
            return override, "수동 입력"
        if one_year_high:
            return one_year_high, "자동 계산 · 최근 1년 최고가"
        return None, "자동 계산 실패"

    def _resolve_expected_jeonse_price(
        self,
        *,
        listing: dict,
        override: int | None,
        latest_rent_deposit_avg: int | None,
    ) -> tuple[int, str]:
        if override:
            return override, "수동 입력"
        if listing.get("expected_jeonse_price"):
            return int(listing["expected_jeonse_price"]), "매물 입력값"
        if latest_rent_deposit_avg:
            return latest_rent_deposit_avg, "자동 계산 · 최근 전세 거래 평균"
        return 0, "데이터 없음"
