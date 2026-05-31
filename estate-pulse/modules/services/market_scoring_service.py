from __future__ import annotations

from datetime import date

from modules.analyzers.complex_grade_analyzer import calculate_complex_grade
from modules.analyzers.liquidity_analyzer import calculate_liquidity_score
from modules.analyzers.transaction_analyzer import calculate_recent_12_month_sale_average


class MarketScoringService:
    def __init__(
        self,
        *,
        complex_repository,
        sale_transaction_repository,
        rent_transaction_repository,
    ) -> None:
        self.complex_repository = complex_repository
        self.sale_transaction_repository = sale_transaction_repository
        self.rent_transaction_repository = rent_transaction_repository

    def analyze_complex(
        self,
        *,
        complex_id: int,
        reference_date: date | None = None,
    ) -> dict:
        complex_row = self.complex_repository.get(complex_id)
        if not complex_row:
            raise ValueError("Apartment complex not found.")

        target_date = reference_date or date.today()
        sale_transactions = [
            item
            for item in self.sale_transaction_repository.list_all()
            if int(item.get("complex_id") or 0) == int(complex_id)
        ]
        rent_transactions = [
            item
            for item in self.rent_transaction_repository.list_all()
            if int(item.get("complex_id") or 0) == int(complex_id)
        ]
        liquidity_result = calculate_liquidity_score(
            sale_transactions=sale_transactions,
            rent_transactions=rent_transactions,
            reference_date=target_date,
        )

        region_complexes = [
            item
            for item in self.complex_repository.list_all()
            if item.get("sido") == complex_row.get("sido")
            and item.get("sigungu") == complex_row.get("sigungu")
        ]
        average_sale_rank, price_per_area_rank = self._resolve_region_ranks(
            complex_id=complex_id,
            region_complexes=region_complexes,
            reference_date=target_date,
        )
        building_age = (
            max(target_date.year - int(complex_row["build_year"]), 0)
            if complex_row.get("build_year")
            else None
        )
        grade_result = calculate_complex_grade(
            household_count=complex_row.get("household_count"),
            building_age=building_age,
            recent_sale_transaction_count=liquidity_result["recent_sale_transaction_count"],
            recent_rent_transaction_count=liquidity_result["recent_rent_transaction_count"],
            average_sale_price_rank=average_sale_rank,
            price_per_area_rank=price_per_area_rank,
            region_complex_count=max(len(region_complexes), 1),
            liquidity_score=liquidity_result["score"],
        )
        self.complex_repository.update_complex_grade(
            complex_id,
            grade_result["grade"],
        )

        return {
            "complex_id": complex_id,
            "complex_grade": grade_result["grade"],
            "complex_grade_label": grade_result["label"],
            "complex_grade_score": grade_result["score"],
            "liquidity_score": liquidity_result["score"],
            "liquidity_band": liquidity_result["band"],
            "liquidity_label": liquidity_result["label"],
            "recent_sale_transaction_count": liquidity_result["recent_sale_transaction_count"],
            "recent_rent_transaction_count": liquidity_result["recent_rent_transaction_count"],
            "transaction_frequency": liquidity_result["transaction_frequency"],
            "average_sale_price_rank": average_sale_rank,
            "price_per_area_rank": price_per_area_rank,
            "region_complex_count": max(len(region_complexes), 1),
            "rule_versions": {
                "liquidity": liquidity_result["rule_version"],
                "complex_grade": grade_result["rule_version"],
            },
        }

    def _resolve_region_ranks(
        self,
        *,
        complex_id: int,
        region_complexes: list[dict],
        reference_date: date,
    ) -> tuple[int | None, int | None]:
        peer_metrics = []
        all_sale_transactions = self.sale_transaction_repository.list_all()
        for peer in region_complexes:
            peer_sales = [
                item
                for item in all_sale_transactions
                if int(item.get("complex_id") or 0) == int(peer["id"])
            ]
            recent_average = calculate_recent_12_month_sale_average(
                peer_sales,
                reference_date=reference_date,
            )
            if not recent_average:
                continue
            recent_areas = [float(item["area_m2"]) for item in peer_sales if item.get("area_m2")]
            average_area = sum(recent_areas) / len(recent_areas) if recent_areas else 0.0
            price_per_area = recent_average / average_area if average_area > 0 else 0.0
            peer_metrics.append(
                {
                    "complex_id": int(peer["id"]),
                    "average_sale_price": recent_average,
                    "price_per_area": price_per_area,
                }
            )

        average_rank = self._resolve_rank(
            complex_id=complex_id,
            peer_metrics=peer_metrics,
            key="average_sale_price",
        )
        price_per_area_rank = self._resolve_rank(
            complex_id=complex_id,
            peer_metrics=peer_metrics,
            key="price_per_area",
        )
        return average_rank, price_per_area_rank

    def _resolve_rank(
        self,
        *,
        complex_id: int,
        peer_metrics: list[dict],
        key: str,
    ) -> int | None:
        if not peer_metrics:
            return None
        ranked_peers = sorted(peer_metrics, key=lambda item: item[key], reverse=True)
        for index, peer in enumerate(ranked_peers, start=1):
            if peer["complex_id"] == int(complex_id):
                return index
        return len(ranked_peers)
