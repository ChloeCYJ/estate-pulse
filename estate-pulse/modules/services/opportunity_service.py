from __future__ import annotations

from config.scoring_rules import RANKING_TYPES
from modules.services.analysis_service import BenchmarkInputs


class OpportunityService:
    def __init__(
        self,
        *,
        complex_repository,
        listing_repository,
        analysis_repository,
        watchlist_repository,
        analysis_service,
    ) -> None:
        self.complex_repository = complex_repository
        self.listing_repository = listing_repository
        self.analysis_repository = analysis_repository
        self.watchlist_repository = watchlist_repository
        self.analysis_service = analysis_service

    def compare_listings(
        self,
        *,
        listing_ids: list[int],
        finance_profile_id: int,
        sort_field: str = "investment_score",
        ascending: bool = False,
    ) -> list[dict]:
        rows = []
        for listing_id in dict.fromkeys(listing_ids):
            listing = self.listing_repository.get(int(listing_id))
            if not listing:
                continue
            rows.append(
                self._build_listing_row(
                    listing=listing,
                    finance_profile_id=finance_profile_id,
                )
            )
        return self._sort_rows(rows, sort_field=sort_field, ascending=ascending)

    def build_watchlist(
        self,
        *,
        finance_profile_id: int,
    ) -> list[dict]:
        rows = []
        for item in self.watchlist_repository.list_all():
            if item.get("listing_id"):
                listing = self.listing_repository.get(int(item["listing_id"]))
                if not listing:
                    continue
                row = self._build_listing_row(
                    listing=listing,
                    finance_profile_id=finance_profile_id,
                )
                row["watchlist_id"] = int(item["id"])
                row["watch_target"] = "LISTING"
                row["summary_basis"] = "개별 매물"
                row["representative_listing_id"] = int(item["listing_id"])
                row["complex_listing_count"] = len(
                    self.listing_repository.list_by_complex(int(row["complex_id"]))
                )
                rows.append(row)
                continue

            candidate_rows = self._build_complex_candidate_rows(
                complex_id=int(item["effective_complex_id"]),
                finance_profile_id=finance_profile_id,
            )
            if candidate_rows:
                row = dict(candidate_rows[0])
                row["watchlist_id"] = int(item["id"])
                row["watch_target"] = "COMPLEX"
                row["summary_basis"] = (
                    "단지 대표 매물"
                    if row.get("listing_id") is not None
                    else "실거래 기준 후보"
                )
                row["representative_listing_id"] = row.get("listing_id")
                row["complex_listing_count"] = len(
                    self.listing_repository.list_by_complex(int(item["effective_complex_id"]))
                )
                row["latest_analysis_date"] = self.analysis_repository.get_latest_created_at_by_complex_area(
                    complex_id=int(item["effective_complex_id"]),
                    area_bucket=float(row["area_bucket"]),
                )
                rows.append(row)
                continue

            rows.append(
                {
                    "watchlist_id": int(item["id"]),
                    "watch_target": "COMPLEX",
                    "summary_basis": "분석 불가",
                    "representative_listing_id": None,
                    "complex_listing_count": 0,
                    "complex_id": int(item["effective_complex_id"]),
                    "area_bucket": None,
                    "listing_id": None,
                    "complex_name": item["complex_name"],
                    "sale_price": None,
                    "required_cash": None,
                    "shortage_cash": None,
                    "expected_loan_amount": None,
                    "total_transaction_cost": None,
                    "bargain_score": None,
                    "jeonse_ratio": None,
                    "liquidity_score": None,
                    "investment_score": None,
                    "complex_grade": None,
                    "complex_grade_label": None,
                    "price_source": None,
                    "relevant_policy_event_count": 0,
                    "relevant_policy_event_titles": "",
                    "relevant_policy_events": [],
                    "analysis_available": False,
                    "analysis_status": "분석 불가",
                    "analysis_error": "분석 가능한 실거래 또는 등록 매물이 없습니다.",
                    "latest_analysis_date": self.analysis_repository.get_latest_created_at_by_complex(
                        int(item["effective_complex_id"])
                    ),
                }
            )
        return rows

    def rank_listings(
        self,
        *,
        finance_profile_id: int,
        ranking_type: str,
    ) -> list[dict]:
        ranking_rule = RANKING_TYPES[ranking_type]
        rows: list[dict] = []
        for complex_row in self.complex_repository.list_all():
            rows.extend(
                self._build_complex_candidate_rows(
                    complex_id=int(complex_row["id"]),
                    finance_profile_id=finance_profile_id,
                )
            )
        return self._sort_rows(
            rows,
            sort_field=ranking_rule["field"],
            ascending=bool(ranking_rule["ascending"]),
        )

    def _build_complex_candidate_rows(
        self,
        *,
        complex_id: int,
        finance_profile_id: int,
    ) -> list[dict]:
        rows: list[dict] = []
        for area_option in self.analysis_service.list_complex_area_options(complex_id=complex_id):
            area_bucket = float(area_option["area_bucket"])
            listings = self.analysis_service.list_matching_listings(
                complex_id=complex_id,
                area_m2=area_bucket,
            )
            if listings:
                listing_rows = [
                    self._build_listing_row(
                        listing=listing,
                        finance_profile_id=finance_profile_id,
                    )
                    for listing in listings
                ]
                row = self._best_candidate_row(listing_rows)
                row["summary_basis"] = "호가 기준 후보"
                rows.append(row)
                continue

            rows.append(
                self._build_reference_row(
                    complex_id=complex_id,
                    complex_name=str(area_option.get("complex_name") or "-"),
                    area_bucket=area_bucket,
                    finance_profile_id=finance_profile_id,
                )
            )
        return rows

    def _build_reference_row(
        self,
        *,
        complex_id: int,
        complex_name: str,
        area_bucket: float,
        finance_profile_id: int,
    ) -> dict:
        try:
            analysis_result = self.analysis_service.run_complex_area_analysis(
                complex_id=complex_id,
                area_m2=area_bucket,
                finance_profile_id=finance_profile_id,
                benchmarks=BenchmarkInputs(),
                save_result=False,
            )
        except ValueError as exc:
            return {
                "listing_id": None,
                "complex_id": complex_id,
                "area_bucket": area_bucket,
                "complex_name": complex_name,
                "sale_price": None,
                "required_cash": None,
                "shortage_cash": None,
                "expected_loan_amount": None,
                "total_transaction_cost": None,
                "bargain_score": None,
                "jeonse_ratio": None,
                "liquidity_score": None,
                "investment_score": None,
                "complex_grade": None,
                "complex_grade_label": None,
                "price_source": "TRANSACTION_REFERENCE",
                "relevant_policy_event_count": 0,
                "relevant_policy_event_titles": "",
                "relevant_policy_events": [],
                "analysis_available": False,
                "analysis_status": "분석 불가",
                "analysis_error": str(exc),
                "summary_basis": "실거래 기준 후보",
                "representative_listing_id": None,
                "complex_listing_count": len(self.listing_repository.list_by_complex(complex_id)),
                "latest_analysis_date": self.analysis_repository.get_latest_created_at_by_complex_area(
                    complex_id=complex_id,
                    area_bucket=area_bucket,
                ),
            }

        return {
            "listing_id": None,
            "complex_id": complex_id,
            "area_bucket": area_bucket,
            "complex_name": analysis_result["complex_name"],
            "sale_price": analysis_result["sale_price"],
            "required_cash": analysis_result["required_cash"],
            "shortage_cash": analysis_result["shortage_cash"],
            "expected_loan_amount": analysis_result["expected_loan_amount"],
            "total_transaction_cost": analysis_result["costs"]["total_transaction_cost"],
            "bargain_score": analysis_result["bargain_score"],
            "jeonse_ratio": round(analysis_result["jeonse_ratio"], 2),
            "liquidity_score": analysis_result["liquidity_score"],
            "investment_score": analysis_result["investment_score"],
            "complex_grade": analysis_result["complex_grade"],
            "complex_grade_label": analysis_result["complex_grade_label"],
            "price_source": analysis_result["price_source"],
            "relevant_policy_event_count": len(analysis_result["relevant_policy_events"]),
            "relevant_policy_event_titles": ", ".join(
                event["title"] for event in analysis_result["relevant_policy_events"][:2]
            ),
            "relevant_policy_events": analysis_result["relevant_policy_events"],
            "analysis_available": True,
            "analysis_status": "분석 완료",
            "analysis_error": None,
            "summary_basis": "실거래 기준 후보",
            "representative_listing_id": None,
            "complex_listing_count": len(self.listing_repository.list_by_complex(complex_id)),
            "latest_analysis_date": self.analysis_repository.get_latest_created_at_by_complex_area(
                complex_id=complex_id,
                area_bucket=area_bucket,
            ),
        }

    def _build_listing_row(
        self,
        *,
        listing: dict,
        finance_profile_id: int,
    ) -> dict:
        try:
            analysis_result = self.analysis_service.run_analysis(
                listing_id=int(listing["id"]),
                finance_profile_id=finance_profile_id,
                benchmarks=BenchmarkInputs(),
                save_result=False,
            )
        except ValueError as exc:
            return {
                "listing_id": int(listing["id"]),
                "complex_id": int(listing["complex_id"]),
                "area_bucket": float(listing["area_m2"]),
                "complex_name": listing["complex_name"],
                "sale_price": int(listing["sale_price"]),
                "required_cash": None,
                "shortage_cash": None,
                "expected_loan_amount": None,
                "total_transaction_cost": None,
                "bargain_score": None,
                "jeonse_ratio": None,
                "liquidity_score": None,
                "investment_score": None,
                "complex_grade": None,
                "complex_grade_label": None,
                "price_source": "LISTING",
                "relevant_policy_event_count": 0,
                "relevant_policy_event_titles": "",
                "relevant_policy_events": [],
                "analysis_available": False,
                "analysis_status": "분석 불가",
                "analysis_error": str(exc),
                "summary_basis": "개별 매물",
                "representative_listing_id": int(listing["id"]),
                "complex_listing_count": None,
                "latest_analysis_date": self.analysis_repository.get_latest_created_at_by_listing(
                    int(listing["id"])
                ),
            }

        return {
            "listing_id": int(listing["id"]),
            "complex_id": int(listing["complex_id"]),
            "area_bucket": float(listing["area_m2"]),
            "complex_name": analysis_result["complex_name"],
            "sale_price": analysis_result["sale_price"],
            "required_cash": analysis_result["required_cash"],
            "shortage_cash": analysis_result["shortage_cash"],
            "expected_loan_amount": analysis_result["expected_loan_amount"],
            "total_transaction_cost": analysis_result["costs"]["total_transaction_cost"],
            "bargain_score": analysis_result["bargain_score"],
            "jeonse_ratio": round(analysis_result["jeonse_ratio"], 2),
            "liquidity_score": analysis_result["liquidity_score"],
            "investment_score": analysis_result["investment_score"],
            "complex_grade": analysis_result["complex_grade"],
            "complex_grade_label": analysis_result["complex_grade_label"],
            "price_source": analysis_result["price_source"],
            "relevant_policy_event_count": len(analysis_result["relevant_policy_events"]),
            "relevant_policy_event_titles": ", ".join(
                event["title"] for event in analysis_result["relevant_policy_events"][:2]
            ),
            "relevant_policy_events": analysis_result["relevant_policy_events"],
            "analysis_available": True,
            "analysis_status": "분석 완료",
            "analysis_error": None,
            "summary_basis": "개별 매물",
            "representative_listing_id": int(listing["id"]),
            "complex_listing_count": None,
            "latest_analysis_date": self.analysis_repository.get_latest_created_at_by_listing(
                int(listing["id"])
            ),
        }

    def _best_candidate_row(self, rows: list[dict]) -> dict:
        analyzed_rows = [row for row in rows if row.get("analysis_available")]
        if analyzed_rows:
            return max(
                analyzed_rows,
                key=lambda row: float(row.get("investment_score") or 0),
            )
        return rows[0]

    def _sort_rows(
        self,
        rows: list[dict],
        *,
        sort_field: str,
        ascending: bool,
    ) -> list[dict]:
        def _sort_value(row: dict):
            value = row.get(sort_field)
            if value is None:
                return float("inf") if ascending else float("-inf")
            return value

        return sorted(
            rows,
            key=lambda row: (
                0 if row.get("analysis_available") else 1,
                _sort_value(row),
            ),
            reverse=False if ascending else False,
        ) if ascending else sorted(
            rows,
            key=lambda row: (
                0 if row.get("analysis_available") else 1,
                -_sort_value(row) if row.get(sort_field) is not None else float("inf"),
            ),
        )
