from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from config.settings import AppSettings
from modules.analyzers.bargain_analyzer import calculate_bargain_score
from modules.analyzers.brokerage_analyzer import calculate_brokerage_breakdown
from modules.analyzers.cash_flow_analyzer import (
    calculate_acquisition_cost_total,
    calculate_jeonse_ratio,
    calculate_shortage_cash,
)
from modules.analyzers.investment_analyzer import calculate_investment_metrics
from modules.analyzers.loan_analyzer import calculate_loan_terms
from modules.analyzers.owner_occupied_analyzer import calculate_owner_occupied_metrics
from modules.analyzers.ranking_analyzer import calculate_overall_investment_score
from modules.analyzers.risk_analyzer import summarize_risk
from modules.analyzers.tax_analyzer import calculate_tax_breakdown
from modules.analyzers.transaction_analyzer import (
    calculate_latest_rent_deposit_average,
    calculate_one_year_high_sale_price,
    calculate_one_year_low_sale_price,
    calculate_recent_12_month_sale_average,
    calculate_recent_3_month_sale_average,
    calculate_recent_6_month_sale_average,
)
from modules.services.report_service import build_analysis_summary

OWNER_OCCUPIED = "OWNER_OCCUPIED"
CASH_ONLY = "CASH_ONLY"
SELL_OWNED_REAL_ESTATE = "SELL_OWNED_REAL_ESTATE"
FUNDING_MODES = (CASH_ONLY, SELL_OWNED_REAL_ESTATE)


@dataclass
class BenchmarkInputs:
    repair_cost: int = 0
    expected_loan_amount: int | None = None
    ltv_rate_override: float | None = None
    recent_avg_price_override: int | None = None
    one_year_high_price_override: int | None = None
    expected_jeonse_price_override: int | None = None
    analysis_mode: str | None = None
    reference_date: date | None = None
    region_type: str | None = None
    buyer_type: str = "NO_HOME"
    purpose: str = "INVESTMENT"
    tax_rule_version: str | None = None
    brokerage_rule_version: str | None = None
    acquisition_tax_override: int | None = None
    local_education_tax_override: int | None = None
    brokerage_fee_override: int | None = None
    legal_fee_override: int | None = None
    reserve_cost_override: int | None = None
    funding_mode: str = CASH_ONLY


class AnalysisService:
    def __init__(
        self,
        *,
        settings: AppSettings,
        listing_repository,
        finance_repository,
        analysis_repository,
        sale_transaction_repository,
        rent_transaction_repository,
        market_scoring_service=None,
        rule_runtime_service=None,
        complex_repository=None,
        region_policy_service=None,
        policy_event_service=None,
    ) -> None:
        self.settings = settings
        self.listing_repository = listing_repository
        self.finance_repository = finance_repository
        self.analysis_repository = analysis_repository
        self.sale_transaction_repository = sale_transaction_repository
        self.rent_transaction_repository = rent_transaction_repository
        self.market_scoring_service = market_scoring_service
        self.rule_runtime_service = rule_runtime_service
        self.complex_repository = complex_repository
        self.region_policy_service = region_policy_service
        self.policy_event_service = policy_event_service

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
            raise ValueError("Listing not found.")
        if not finance_profile:
            raise ValueError("Finance profile not found.")
        funding_mode = _normalize_funding_mode(benchmarks.funding_mode)
        purchase_power = _calculate_purchase_power(
            finance_profile=finance_profile,
            funding_mode=funding_mode,
        )

        stored_investment_type = (
            listing.get("effective_investment_type")
            or listing.get("investment_type")
            or OWNER_OCCUPIED
        )
        primary_user_mode = benchmarks.analysis_mode or _to_primary_user_mode(
            stored_investment_type
        )
        investment_type = _resolve_analysis_investment_type(
            stored_investment_type=stored_investment_type,
            primary_user_mode=primary_user_mode,
        )
        market_context = self.get_transaction_context(
            listing_id=listing_id,
            benchmarks=benchmarks,
            reference_date=benchmarks.reference_date,
        )

        complex_row = (
            self.complex_repository.get(int(listing["complex_id"]))
            if self.complex_repository is not None
            else None
        )
        region_context = self._resolve_region_context(
            listing=listing,
            complex_row=complex_row,
            manual_region_type=benchmarks.region_type,
            reference_date=benchmarks.reference_date,
        )
        relevant_policy_events = self._resolve_relevant_policy_events(
            complex_row=complex_row,
            buyer_type=benchmarks.buyer_type,
            investment_purpose=(
                OWNER_OCCUPIED if primary_user_mode == OWNER_OCCUPIED else benchmarks.purpose
            ),
            reference_date=benchmarks.reference_date,
        )

        active_loan_rules = (
            self.rule_runtime_service.get_active_loan_rules()
            if self.rule_runtime_service is not None
            else None
        )
        loan_terms = calculate_loan_terms(
            sale_price=listing["sale_price"],
            region_type=region_context["region_type"],
            buyer_type=benchmarks.buyer_type,
            purpose=OWNER_OCCUPIED if primary_user_mode == OWNER_OCCUPIED else benchmarks.purpose,
            reference_date=benchmarks.reference_date,
            ltv_rate_override=_resolve_ltv_rate_override(
                analysis_override=benchmarks.ltv_rate_override,
                finance_profile=finance_profile,
            ),
            final_loan_amount_override=benchmarks.expected_loan_amount,
            annual_income=finance_profile.get("annual_income"),
            existing_debt=int(purchase_power["existing_debt_for_loan_screening"]),
            annual_interest_rate=finance_profile.get("interest_rate"),
            rules=active_loan_rules,
        )
        expected_loan_amount = int(loan_terms["final_loan_amount"])

        active_tax_rule = (
            self.rule_runtime_service.get_active_tax_rule(
                rule_version=benchmarks.tax_rule_version,
                reference_date=benchmarks.reference_date,
            )
            if self.rule_runtime_service is not None
            else None
        )
        tax_breakdown = calculate_tax_breakdown(
            sale_price=int(listing["sale_price"]),
            rule_version=benchmarks.tax_rule_version,
            rule=active_tax_rule,
            acquisition_tax_override=benchmarks.acquisition_tax_override,
            local_education_tax_override=benchmarks.local_education_tax_override,
        )
        active_brokerage_rule = (
            self.rule_runtime_service.get_active_brokerage_rule(
                rule_version=benchmarks.brokerage_rule_version,
                reference_date=benchmarks.reference_date,
            )
            if self.rule_runtime_service is not None
            else None
        )
        brokerage_breakdown = calculate_brokerage_breakdown(
            sale_price=int(listing["sale_price"]),
            rule_version=benchmarks.brokerage_rule_version,
            rule=active_brokerage_rule,
            brokerage_fee_override=benchmarks.brokerage_fee_override,
            legal_fee_override=benchmarks.legal_fee_override,
            reserve_cost_override=benchmarks.reserve_cost_override,
        )
        total_transaction_cost = (
            tax_breakdown["total_tax"] + brokerage_breakdown["total_brokerage_cost"]
        )
        acquisition_cost_total = calculate_acquisition_cost_total(
            acquisition_tax=tax_breakdown["acquisition_tax"] + tax_breakdown["local_education_tax"],
            brokerage_fee=brokerage_breakdown["brokerage_fee"],
            legal_fee=brokerage_breakdown["legal_fee"],
            repair_cost=benchmarks.repair_cost,
            contingency_fee=brokerage_breakdown["reserve_cost"],
        )

        if primary_user_mode == OWNER_OCCUPIED:
            mode_metrics = calculate_owner_occupied_metrics(
                sale_price=listing["sale_price"],
                estimated_loan=expected_loan_amount,
                acquisition_cost_total=acquisition_cost_total,
                cash_amount=int(purchase_power["available_cash_for_purchase"]),
                annual_income=finance_profile.get("annual_income"),
                annual_interest_rate=finance_profile.get("interest_rate"),
            )
            required_cash = int(mode_metrics["required_cash"])
            shortage_cash = int(mode_metrics["shortage_cash"])
            current_required_cash = required_cash
            future_required_cash = None
            monthly_cash_flow = None
            gap_amount = None
            estimated_investment_efficiency = None
        else:
            mode_metrics = calculate_investment_metrics(
                investment_type=investment_type,
                sale_price=listing["sale_price"],
                estimated_loan=expected_loan_amount,
                acquisition_cost_total=acquisition_cost_total,
                expected_jeonse_price=market_context["derived_inputs"]["expected_jeonse_price"],
                takeover_jeonse_deposit=int(listing.get("takeover_jeonse_deposit") or 0),
                rent_deposit=int(listing.get("rent_deposit") or 0),
                expected_monthly_rent=int(listing.get("expected_monthly_rent") or 0),
            )
            required_cash = int(mode_metrics["required_cash"])
            shortage_cash = calculate_shortage_cash(
                required_cash,
                int(purchase_power["available_cash_for_purchase"]),
            )
            current_required_cash = mode_metrics["current_required_cash"]
            future_required_cash = mode_metrics["future_required_cash"]
            monthly_cash_flow = mode_metrics["monthly_cash_flow"]
            gap_amount = mode_metrics["gap_amount"]
            estimated_investment_efficiency = mode_metrics["estimated_investment_efficiency"]

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
            user_cash=int(purchase_power["available_cash_for_purchase"]),
        )
        complex_profile = self._get_complex_profile(
            complex_id=int(listing["complex_id"]),
            reference_date=benchmarks.reference_date,
        )
        investment_score_result = calculate_overall_investment_score(
            bargain_score=int(bargain_result["score"]),
            liquidity_score=int(complex_profile["liquidity_score"]),
            complex_grade=str(complex_profile["complex_grade"]),
            required_cash=required_cash,
            sale_price=int(listing["sale_price"]),
            shortage_cash=shortage_cash,
        )
        risks = summarize_risk(
            shortage_cash=shortage_cash,
            jeonse_ratio=jeonse_ratio if primary_user_mode != OWNER_OCCUPIED else 0.0,
        )
        decision = _build_decision(
            primary_user_mode=primary_user_mode,
            shortage_cash=shortage_cash,
        )
        summary = build_analysis_summary(
            primary_user_mode=primary_user_mode,
            complex_name=listing["complex_name"],
            listing=listing,
            finance_profile=finance_profile,
            expected_jeonse_price=market_context["derived_inputs"]["expected_jeonse_price"],
            required_cash=required_cash,
            shortage_cash=shortage_cash,
            bargain_result=bargain_result,
            decision=decision,
            monthly_repayment=mode_metrics.get("monthly_repayment"),
            dsr=mode_metrics.get("dsr"),
            remaining_cash_after_purchase=mode_metrics.get("remaining_cash_after_purchase"),
            gap_amount=gap_amount,
            estimated_investment_efficiency=estimated_investment_efficiency,
            jeonse_ratio=jeonse_ratio,
            liquidity_score=complex_profile["liquidity_score"],
            complex_grade_label=complex_profile["complex_grade_label"],
            investment_score=investment_score_result["investment_score"],
        )
        applied_rules = _build_applied_rules_trace(
            listing=listing,
            finance_profile=finance_profile,
            benchmarks=benchmarks,
            loan_terms=loan_terms,
            region_context=region_context,
            tax_breakdown=tax_breakdown,
            brokerage_breakdown=brokerage_breakdown,
            mode_metrics=mode_metrics,
            expected_loan_amount=expected_loan_amount,
        )

        result = {
            "listing_id": listing_id,
            "investment_type": investment_type,
            "primary_user_mode": primary_user_mode,
            "complex_name": listing["complex_name"],
            "sale_price": listing["sale_price"],
            "expected_jeonse_price": market_context["derived_inputs"]["expected_jeonse_price"],
            "expected_loan_amount": expected_loan_amount,
            "loan_rule_version": loan_terms["rule_version"],
            "loan_terms": loan_terms,
            "resolved_region_type": region_context["region_type"],
            "region_policy_source": region_context["source"],
            "active_region_policies": region_context["active_policies"],
            "relevant_policy_events": relevant_policy_events,
            "funding_mode": funding_mode,
            "purchase_power": purchase_power,
            "required_cash": required_cash,
            "shortage_cash": shortage_cash,
            "current_required_cash": current_required_cash,
            "future_required_cash": future_required_cash,
            "monthly_cash_flow": monthly_cash_flow,
            "monthly_repayment": mode_metrics.get("monthly_repayment"),
            "dsr": mode_metrics.get("dsr"),
            "remaining_cash_after_purchase": mode_metrics.get("remaining_cash_after_purchase"),
            "gap_amount": gap_amount,
            "estimated_investment_efficiency": estimated_investment_efficiency,
            "jeonse_ratio": jeonse_ratio,
            "discount_vs_recent_avg": bargain_result["discount_rate"],
            "recent_avg_change_rate": -bargain_result["discount_rate"],
            "drop_from_high": bargain_result["drop_from_high"],
            "high_price_change_rate": -bargain_result["drop_from_high"],
            "bargain_score": bargain_result["score"],
            "bargain_grade": bargain_result["grade"],
            "reasons": bargain_result["reasons"],
            "risks": risks,
            "decision": decision,
            "summary": summary,
            "scenario_explanation": mode_metrics["scenario_explanation"],
            "scenario_inputs": {
                "expected_jeonse_price": market_context["derived_inputs"]["expected_jeonse_price"],
                "takeover_jeonse_deposit": int(listing.get("takeover_jeonse_deposit") or 0),
                "rent_deposit": int(listing.get("rent_deposit") or 0),
                "expected_monthly_rent": int(listing.get("expected_monthly_rent") or 0),
            },
            "costs": {
                "acquisition_tax": tax_breakdown["acquisition_tax"],
                "local_education_tax": tax_breakdown["local_education_tax"],
                "brokerage_fee": brokerage_breakdown["brokerage_fee"],
                "legal_fee": brokerage_breakdown["legal_fee"],
                "repair_cost": benchmarks.repair_cost,
                "reserve_cost": brokerage_breakdown["reserve_cost"],
                "total_transaction_cost": total_transaction_cost,
                "total_acquisition_cost": acquisition_cost_total,
            },
            "applied_tax_rule_version": tax_breakdown["applied_tax_rule_version"],
            "applied_brokerage_rule_version": brokerage_breakdown[
                "applied_brokerage_rule_version"
            ],
            "applied_rules": applied_rules,
            "market_metrics": market_context["market_metrics"],
            "derived_inputs": market_context["derived_inputs"],
            "sale_history": market_context["sale_history"],
            "rent_history": market_context["rent_history"],
            "sources": market_context["sources"],
            "liquidity_score": complex_profile["liquidity_score"],
            "liquidity_label": complex_profile["liquidity_label"],
            "complex_grade": complex_profile["complex_grade"],
            "complex_grade_label": complex_profile["complex_grade_label"],
            "complex_profile": complex_profile,
            "investment_score": investment_score_result["investment_score"],
            "required_cash_efficiency_score": investment_score_result[
                "required_cash_efficiency_score"
            ],
            "investment_score_rule_version": investment_score_result["rule_version"],
        }

        if save_result:
            analysis_id = self.analysis_repository.create(
                {
                    "listing_id": listing_id,
                    "investment_type": investment_type,
                    "required_cash": required_cash,
                    "shortage_cash": shortage_cash,
                    "current_required_cash": current_required_cash,
                    "future_required_cash": future_required_cash,
                    "monthly_cash_flow": monthly_cash_flow,
                    "acquisition_tax": tax_breakdown["acquisition_tax"],
                    "local_education_tax": tax_breakdown["local_education_tax"],
                    "brokerage_fee": brokerage_breakdown["brokerage_fee"],
                    "legal_fee": brokerage_breakdown["legal_fee"],
                    "reserve_cost": brokerage_breakdown["reserve_cost"],
                    "total_transaction_cost": total_transaction_cost,
                    "applied_tax_rule_version": tax_breakdown["applied_tax_rule_version"],
                    "applied_brokerage_rule_version": brokerage_breakdown[
                        "applied_brokerage_rule_version"
                    ],
                    "liquidity_score": complex_profile["liquidity_score"],
                    "investment_score": investment_score_result["investment_score"],
                    "complex_grade": complex_profile["complex_grade"],
                    "jeonse_ratio": jeonse_ratio,
                    "discount_vs_recent_avg": bargain_result["discount_rate"],
                    "drop_from_high": bargain_result["drop_from_high"],
                    "bargain_score": bargain_result["score"],
                    "loan_rule_version": loan_terms["rule_version"],
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
            raise ValueError("Listing not found.")

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

        sale_avg_3m = calculate_recent_3_month_sale_average(
            sale_history,
            reference_date=target_date,
        )
        sale_avg_6m = calculate_recent_6_month_sale_average(
            sale_history,
            reference_date=target_date,
        )
        sale_avg_12m = calculate_recent_12_month_sale_average(
            sale_history,
            reference_date=target_date,
        )
        one_year_high = calculate_one_year_high_sale_price(
            sale_history,
            reference_date=target_date,
        )
        one_year_low = calculate_one_year_low_sale_price(
            sale_history,
            reference_date=target_date,
        )
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
            raise ValueError("Recent sale average is unavailable for this listing.")
        if one_year_high_price is None:
            raise ValueError("One-year high sale price is unavailable for this listing.")

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

    def _get_complex_profile(
        self,
        *,
        complex_id: int,
        reference_date: date | None,
    ) -> dict:
        if self.market_scoring_service is None:
            return {
                "complex_id": complex_id,
                "complex_grade": "NORMAL",
                "complex_grade_label": "일반",
                "liquidity_score": 60,
                "liquidity_label": "normal liquidity",
                "recent_sale_transaction_count": 0,
                "recent_rent_transaction_count": 0,
                "transaction_frequency": 0.0,
                "average_sale_price_rank": None,
                "price_per_area_rank": None,
            }
        return self.market_scoring_service.analyze_complex(
            complex_id=complex_id,
            reference_date=reference_date,
        )

    def _resolve_region_context(
        self,
        *,
        listing: dict,
        complex_row: dict | None,
        manual_region_type: str | None,
        reference_date: date | None,
    ) -> dict:
        if manual_region_type:
            return {
                "region_type": manual_region_type,
                "source": "manual override",
                "active_policies": [],
            }
        if self.complex_repository is None or self.region_policy_service is None:
            return {
                "region_type": "NON_REGULATED",
                "source": "default",
                "active_policies": [],
            }

        if not complex_row:
            return {
                "region_type": "NON_REGULATED",
                "source": "default",
                "active_policies": [],
            }

        return self.region_policy_service.resolve_region_context(
            sido=complex_row.get("sido"),
            sigungu=complex_row.get("sigungu"),
            dong=complex_row.get("dong"),
            reference_date=reference_date,
        )

    def _resolve_relevant_policy_events(
        self,
        *,
        complex_row: dict | None,
        buyer_type: str,
        investment_purpose: str,
        reference_date: date | None,
    ) -> list[dict]:
        if self.policy_event_service is None:
            return []
        return self.policy_event_service.find_relevant_policy_events(
            reference_date=reference_date,
            region_sido=complex_row.get("sido") if complex_row else None,
            region_sigungu=complex_row.get("sigungu") if complex_row else None,
            region_dong=complex_row.get("dong") if complex_row else None,
            buyer_type=buyer_type,
            investment_purpose=investment_purpose,
            include_future=True,
        )


def _to_primary_user_mode(investment_type: str) -> str:
    return OWNER_OCCUPIED if investment_type == OWNER_OCCUPIED else "INVESTMENT"


def _resolve_analysis_investment_type(
    *,
    stored_investment_type: str,
    primary_user_mode: str,
) -> str:
    if primary_user_mode == OWNER_OCCUPIED:
        return OWNER_OCCUPIED
    if stored_investment_type == OWNER_OCCUPIED:
        return "GAP_INVESTMENT"
    return stored_investment_type


def _resolve_ltv_rate_override(
    *,
    analysis_override: float | None,
    finance_profile: dict,
) -> float | None:
    if analysis_override is not None:
        return analysis_override
    if not finance_profile.get("use_manual_ltv"):
        return None
    manual_ltv_rate = finance_profile.get("manual_ltv_rate")
    if manual_ltv_rate is None:
        return None
    return float(manual_ltv_rate)


def _build_applied_rules_trace(
    *,
    listing: dict,
    finance_profile: dict,
    benchmarks: BenchmarkInputs,
    loan_terms: dict,
    region_context: dict,
    tax_breakdown: dict,
    brokerage_breakdown: dict,
    mode_metrics: dict,
    expected_loan_amount: int,
) -> dict:
    """Build display-only rule trace data for the current analysis result."""
    ltv_source = str(loan_terms.get("ltv_source") or "")
    loan_amount_source = str(loan_terms.get("loan_amount_source") or "")
    manual_ltv_enabled = ltv_source == "manual override"
    manual_override_items = _build_manual_override_items(benchmarks)

    return {
        "loan_ltv": {
            "base_price": int(listing["sale_price"]),
            "applied_ltv_rate": loan_terms.get("applied_ltv_rate"),
            "loan_amount_by_ltv": loan_terms.get("loan_amount_by_ltv"),
            "dsr_based_loan_limit": loan_terms.get("dsr_based_loan_limit"),
            "max_loan_amount": loan_terms.get("max_loan_amount"),
            "policy_capped_loan_amount": loan_terms.get("policy_capped_loan_amount"),
            "expected_loan_amount": int(expected_loan_amount),
            "ltv_method": "MANUAL_OVERRIDE" if manual_ltv_enabled else "AUTO_RULE",
            "ltv_source": ltv_source or None,
            "manual_ltv_used": manual_ltv_enabled,
            "manual_ltv_source": _manual_ltv_source(
                benchmarks=benchmarks,
                finance_profile=finance_profile,
            )
            if manual_ltv_enabled
            else None,
            "loan_amount_method": (
                "MANUAL_OVERRIDE" if loan_amount_source == "manual override" else "AUTO_RULE"
            ),
            "loan_amount_source": loan_amount_source or None,
            "applied_region_type": region_context.get("region_type"),
            "region_policy_source": region_context.get("source"),
            "active_region_policies": region_context.get("active_policies") or [],
            "matched_rule_version": loan_terms.get("rule_version"),
            "matched_rule_description": loan_terms.get("rule_description"),
            "calculation_formula": "base_price * applied_ltv_rate = expected_loan_amount",
        },
        "dsr": {
            "annual_income": finance_profile.get("annual_income"),
            "dsr": mode_metrics.get("dsr"),
            "applied_dsr_rate": loan_terms.get("applied_dsr_rate"),
            "dsr_based_loan_limit": loan_terms.get("dsr_based_loan_limit"),
            "missing_reason": (
                "연소득 정보가 없어 계산하지 않았습니다."
                if mode_metrics.get("dsr") is None
                else None
            ),
        },
        "monthly_repayment": {
            "annual_interest_rate": finance_profile.get("interest_rate"),
            "loan_term_years": 30,
            "monthly_repayment": mode_metrics.get("monthly_repayment"),
            "missing_reason": (
                "금리 또는 대출기간 정보가 없어 계산하지 않았습니다."
                if mode_metrics.get("monthly_repayment") is None
                else None
            ),
        },
        "transaction_costs": {
            "tax_rule_version": tax_breakdown.get("applied_tax_rule_version"),
            "tax_rule_description": tax_breakdown.get("rule_description"),
            "tax_manual_override": bool(tax_breakdown.get("manual_override")),
            "brokerage_rule_version": brokerage_breakdown.get(
                "applied_brokerage_rule_version"
            ),
            "brokerage_rule_description": brokerage_breakdown.get("rule_description"),
            "brokerage_manual_override": bool(brokerage_breakdown.get("manual_override")),
            "repair_cost_manual_override": benchmarks.repair_cost > 0,
            "manual_override_used": bool(manual_override_items),
            "manual_override_items": manual_override_items,
        },
    }


def _manual_ltv_source(*, benchmarks: BenchmarkInputs, finance_profile: dict) -> str:
    if benchmarks.ltv_rate_override is not None:
        return "ANALYSIS_INPUT"
    if finance_profile.get("use_manual_ltv"):
        return "FINANCE_PROFILE"
    return "UNKNOWN"


def _build_manual_override_items(benchmarks: BenchmarkInputs) -> list[str]:
    items: list[str] = []
    override_fields = (
        ("acquisition_tax_override", "취득세"),
        ("local_education_tax_override", "지방교육세"),
        ("brokerage_fee_override", "중개보수"),
        ("legal_fee_override", "법무비"),
        ("reserve_cost_override", "예비비"),
    )
    for field_name, label in override_fields:
        if getattr(benchmarks, field_name) is not None:
            items.append(label)
    if benchmarks.repair_cost > 0:
        items.append("수리비")
    return items


def _normalize_funding_mode(value: str | None) -> str:
    normalized = str(value or CASH_ONLY).strip().upper()
    if normalized not in FUNDING_MODES:
        return CASH_ONLY
    return normalized


def _calculate_purchase_power(*, finance_profile: dict, funding_mode: str) -> dict:
    cash_amount = int(finance_profile.get("cash_amount") or 0)
    owned_real_estate_value = int(finance_profile.get("owned_real_estate_value") or 0)
    owned_real_estate_debt = int(finance_profile.get("owned_real_estate_debt") or 0)
    credit_loan_balance = int(finance_profile.get("credit_loan_balance") or 0)
    other_loan_balance = int(finance_profile.get("other_loan_balance") or 0)
    stored_existing_debt = int(finance_profile.get("existing_debt") or 0)
    component_debt_total = owned_real_estate_debt + credit_loan_balance + other_loan_balance
    existing_debt_total = stored_existing_debt or component_debt_total

    sale_net_cash = 0
    existing_debt_for_loan_screening = existing_debt_total
    if funding_mode == SELL_OWNED_REAL_ESTATE:
        sale_net_cash = max(owned_real_estate_value - owned_real_estate_debt, 0)
        existing_debt_for_loan_screening = max(existing_debt_total - owned_real_estate_debt, 0)

    available_cash_for_purchase = cash_amount + sale_net_cash
    return {
        "cash_amount": cash_amount,
        "funding_mode": funding_mode,
        "owned_real_estate_value": owned_real_estate_value,
        "owned_real_estate_debt": owned_real_estate_debt,
        "sale_net_cash": sale_net_cash,
        "available_cash_for_purchase": available_cash_for_purchase,
        "existing_debt_total": existing_debt_total,
        "existing_debt_for_loan_screening": existing_debt_for_loan_screening,
    }


def _build_decision(*, primary_user_mode: str, shortage_cash: int) -> str:
    if primary_user_mode == OWNER_OCCUPIED:
        return (
            "현재 자금 기준으로 실거주 매수가 가능합니다."
            if shortage_cash <= 0
            else "실거주 매수를 위해 추가 현금이 필요합니다."
        )
    return (
        "현재 자금 기준으로 투자 검토가 가능합니다."
        if shortage_cash <= 0
        else "투자 검토를 위해 추가 현금이 필요합니다."
    )
