from __future__ import annotations

from datetime import date, datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_date_or_today(value: str | None) -> date:
    if not value:
        return date.today()
    return datetime.fromisoformat(value).date()
