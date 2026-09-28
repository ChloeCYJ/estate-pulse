from __future__ import annotations

from modules.utils.money_utils import format_compact_won


def build_analysis_dashboard_view_model_from_live_result(result: dict) -> dict[str, object]:
    analysis_id = result.get("analysis_id")
    return {
        "page_status": "ready",
        "display_error": None,
        "active_section": "decision",
        "property": {
            "analysis_id": str(analysis_id) if analysis_id not in (None, "") else "",
            "complex_name": str(result.get("complex_name") or "-"),
            "area_label": _format_area_label(result.get("area_bucket")),
            "reference_price_label": _format_money(result.get("sale_price")),
        },
        "decision": {
            "decision_status": "shortfall" if int(result.get("shortage_cash") or 0) > 0 else "affordable",
            "decision_title": str(result.get("decision") or "-"),
            "decision_description": str(result.get("summary") or ""),
        },
        "financing": {
            "required_cash": {
                "label": "총 필요 현금",
                "value": _to_optional_int(result.get("required_cash")),
                "formatted": _format_money(result.get("required_cash")),
            },
            "cash_shortfall": {
                "label": "부족 자금",
                "value": _to_optional_int(result.get("shortage_cash")),
                "formatted": _format_money(result.get("shortage_cash")),
            },
            "expected_loan": {
                "label": "예상 대출",
                "value": _to_optional_int(result.get("expected_loan_amount")),
                "formatted": _format_money(result.get("expected_loan_amount")),
            },
            "monthly_payment": {
                "label": "월 상환액",
                "value": _to_optional_int(result.get("monthly_repayment")),
                "formatted": _format_money(result.get("monthly_repayment")),
            },
        },
        "risks": {
            "items": list(result.get("risks") or []),
        },
    }


def build_analysis_dashboard_view_model_from_saved_row(row: dict) -> dict[str, object]:
    return build_analysis_dashboard_view_model_from_live_result(
        {
            "analysis_id": row.get("id"),
            "complex_name": row.get("complex_name_snapshot"),
            "area_bucket": row.get("area_bucket") or row.get("area_m2_snapshot"),
            "sale_price": row.get("sale_price_snapshot") or row.get("effective_price_snapshot"),
            "required_cash": row.get("required_cash"),
            "shortage_cash": row.get("shortage_cash"),
            "expected_loan_amount": row.get("expected_loan_amount"),
            "monthly_repayment": row.get("monthly_repayment"),
            "decision": row.get("decision"),
            "summary": row.get("summary"),
            "risks": [],
        }
    )


def _format_money(value: object) -> str:
    if value in (None, ""):
        return "-"
    return format_compact_won(int(value))


def _format_area_label(value: object) -> str:
    if value in (None, ""):
        return "-"
    return f"{float(value):.1f}m²"


def _to_optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
