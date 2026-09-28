from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, TypedDict, cast


COMMERCIAL_PAGE_STATE_KEY = "commercial_page_state"


class ResolvedAnalysisResultDict(TypedDict, total=False):
    analysis_id: int
    listing_id: int | None
    complex_id: int
    complex_name: str
    area_bucket: float
    sale_price: int
    price_source: str
    required_cash: int
    shortage_cash: int
    expected_loan_amount: int
    monthly_repayment: int | None
    decision: str
    summary: str


class PendingAnalysisRequestDict(TypedDict):
    request_kind: Literal["complex_area_analysis"]
    complex_id: int
    area_bucket: float
    listing_id: int | None


class PageNoticeDict(TypedDict):
    level: Literal["info", "warning", "error"]
    code: str
    message: str


@dataclass(frozen=True)
class CommercialPageState:
    commercial_page: Literal["search_home", "analysis_dashboard", "legacy_comparison"] = (
        "search_home"
    )
    analysis_source: Literal["live", "saved"] | None = None
    active_analysis_id: int | None = None
    active_analysis_result: ResolvedAnalysisResultDict | None = None
    pending_analysis_request: PendingAnalysisRequestDict | None = None
    page_notice: PageNoticeDict | None = None
    last_trigger: str | None = None


def load_commercial_page_state(session_state: dict[str, object]) -> CommercialPageState:
    payload = cast(dict[str, object], session_state.get(COMMERCIAL_PAGE_STATE_KEY) or {})
    return CommercialPageState(
        commercial_page=cast(
            Literal["search_home", "analysis_dashboard", "legacy_comparison"],
            payload.get("commercial_page") or "search_home",
        ),
        analysis_source=cast(Literal["live", "saved"] | None, payload.get("analysis_source")),
        active_analysis_id=_to_optional_int(payload.get("active_analysis_id")),
        active_analysis_result=cast(
            ResolvedAnalysisResultDict | None,
            payload.get("active_analysis_result"),
        ),
        pending_analysis_request=cast(
            PendingAnalysisRequestDict | None,
            payload.get("pending_analysis_request"),
        ),
        page_notice=cast(PageNoticeDict | None, payload.get("page_notice")),
        last_trigger=_to_optional_str(payload.get("last_trigger")),
    )


def save_commercial_page_state(
    session_state: dict[str, object],
    state: CommercialPageState,
) -> None:
    session_state[COMMERCIAL_PAGE_STATE_KEY] = asdict(state)


def _to_optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_optional_str(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
