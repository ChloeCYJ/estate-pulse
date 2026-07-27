from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from modules.utils.money_utils import format_compact_won


SEARCH_STATUS_IDLE = "idle"
SEARCH_STATUS_LOADING = "loading"
SEARCH_STATUS_SUCCESS = "success"
SEARCH_STATUS_NO_RESULTS = "no_results"
SEARCH_STATUS_ERROR = "error"


class DisplayError(TypedDict):
    code: str
    message: str


def build_search_home_view_model(
    *,
    search_query: str,
    search_status: str,
    recent_analyses: list[dict],
    search_results: list[dict] | None,
    display_error: DisplayError | None,
) -> dict[str, object]:
    normalized_results = list(search_results or [])
    recent_cards = [_recent_analysis_card_payload(item) for item in recent_analyses]
    normalized_query = str(search_query or "").strip()
    empty_state = (
        search_status == SEARCH_STATUS_IDLE
        and not normalized_query
        and not normalized_results
        and not recent_cards
    )

    return {
        "service_title": "Estate Plus",
        "service_description": [
            "서울 아파트를 숫자로 판단하세요",
            "거래가와 자금 조건을 함께 반영해 바로 검토할 대상을 빠르게 좁혀드립니다.",
        ],
        "search_query": normalized_query,
        "search_status": search_status,
        "navigation": [
            {"id": "search", "label": "단지 검색", "active": True},
            {"id": "comparison", "label": "단지 비교", "active": False},
            {"id": "saved_analyses", "label": "저장한 분석", "active": False},
        ],
        "empty_state": empty_state,
        "display_error": display_error,
        "recent_analyses": recent_cards,
        "search_results": normalized_results,
    }


def _recent_analysis_card_payload(item: dict) -> dict[str, str]:
    area_value = item.get("area_m2")
    if area_value in (None, ""):
        area_value = item.get("area_bucket")
    price_value = item.get("sale_price")
    if price_value in (None, ""):
        price_value = item.get("reference_price")

    return {
        "analysis_id": str(item.get("id") or ""),
        "complex_name": str(item.get("complex_name") or "-"),
        "area_label": _format_area_label(area_value),
        "reference_price_label": _format_money_label(price_value),
        "analyzed_at_label": _format_datetime_label(item.get("created_at")),
        "location_label": str(item.get("location_label") or "-"),
    }


def _format_area_label(value: object) -> str:
    if value in (None, ""):
        return "-"
    return f"{float(value):.1f}m²"


def _format_money_label(value: object) -> str:
    if value in (None, ""):
        return "-"
    return format_compact_won(int(value))


def _format_datetime_label(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "-"
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return text.replace("T", " ")[:16]
