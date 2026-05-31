from __future__ import annotations

from datetime import date, timedelta


POLICY_EVENT_TYPES = (
    "LOAN",
    "TAX",
    "REGULATION",
    "TRANSACTION",
    "PERMISSION",
    "CONTRACT",
    "INFO",
)
BUYER_TYPES = ("NO_HOME", "ONE_HOME", "MULTI_HOME", "ANY")
INVESTMENT_PURPOSES = ("OWNER_OCCUPIED", "INVESTMENT", "ANY")
IMPACT_LEVELS = ("HIGH", "MEDIUM", "LOW")
POLICY_EVENT_STATUSES = ("ACTIVE", "FUTURE", "EXPIRED")

_IMPACT_PRIORITY = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
_STATUS_PRIORITY = {"ACTIVE": 2, "FUTURE": 1, "EXPIRED": 0}


class PolicyEventService:
    def __init__(self, *, policy_event_repository) -> None:
        self.policy_event_repository = policy_event_repository

    def list_policy_types(self) -> list[str]:
        return list(POLICY_EVENT_TYPES)

    def list_buyer_types(self) -> list[str]:
        return list(BUYER_TYPES)

    def list_investment_purposes(self) -> list[str]:
        return list(INVESTMENT_PURPOSES)

    def list_impact_levels(self) -> list[str]:
        return list(IMPACT_LEVELS)

    def list_statuses(self) -> list[str]:
        return list(POLICY_EVENT_STATUSES)

    def create_policy_event(self, **payload) -> int:
        normalized = self.normalize_policy_event(payload)
        return self.policy_event_repository.create(**normalized)

    def update_policy_event(self, policy_event_id: int, **payload) -> None:
        if not self.policy_event_repository.get(policy_event_id):
            raise ValueError("Policy event not found.")
        normalized = self.normalize_policy_event(payload)
        self.policy_event_repository.update(policy_event_id, **normalized)

    def expire_policy_event(self, policy_event_id: int, *, expired_on: str | None = None) -> None:
        event = self.policy_event_repository.get(policy_event_id)
        if not event:
            raise ValueError("Policy event not found.")
        target_end = expired_on or (date.today() - timedelta(days=1)).isoformat()
        self.policy_event_repository.expire(
            policy_event_id,
            effective_to=target_end,
            status="EXPIRED",
        )

    def get_policy_event(
        self,
        policy_event_id: int,
        *,
        reference_date: date | None = None,
    ) -> dict | None:
        event = self.policy_event_repository.get(policy_event_id)
        if not event:
            return None
        decorated = self._decorate_event(event, reference_date=reference_date)
        self._persist_status_if_needed(event, decorated["status"])
        return decorated

    def list_policy_events(
        self,
        *,
        policy_type: str | None = None,
        status: str | None = None,
        impact_level: str | None = None,
        reference_date: date | None = None,
    ) -> list[dict]:
        rows = self.policy_event_repository.list_all(
            policy_type=policy_type,
            status=None,
            impact_level=impact_level,
        )
        decorated_rows: list[dict] = []
        for row in rows:
            decorated = self._decorate_event(row, reference_date=reference_date)
            self._persist_status_if_needed(row, decorated["status"])
            if status and decorated["status"] != status:
                continue
            decorated_rows.append(decorated)
        return sorted(decorated_rows, key=self._event_sort_key, reverse=True)

    def find_relevant_policy_events(
        self,
        *,
        reference_date: date | None,
        region_sido: str | None,
        region_sigungu: str | None,
        region_dong: str | None,
        buyer_type: str,
        investment_purpose: str,
        include_future: bool = True,
        policy_types: list[str] | None = None,
        impact_levels: list[str] | None = None,
    ) -> list[dict]:
        allowed_statuses = {"ACTIVE", "FUTURE"} if include_future else {"ACTIVE"}
        allowed_policy_types = set(policy_types or POLICY_EVENT_TYPES)
        allowed_impact_levels = set(impact_levels or IMPACT_LEVELS)

        relevant: list[dict] = []
        for event in self.list_policy_events(reference_date=reference_date):
            if event["status"] not in allowed_statuses:
                continue
            if event["policy_type"] not in allowed_policy_types:
                continue
            if event["impact_level"] not in allowed_impact_levels:
                continue
            if not self._matches_region(
                event,
                sido=region_sido,
                sigungu=region_sigungu,
                dong=region_dong,
            ):
                continue
            if not self._matches_buyer_type(event, buyer_type):
                continue
            if not self._matches_investment_purpose(event, investment_purpose):
                continue
            relevant.append(
                {
                    **event,
                    "reference_mode": self._reference_mode(event),
                }
            )
        return sorted(relevant, key=self._event_sort_key, reverse=True)

    def list_high_impact_events(
        self,
        *,
        reference_date: date | None = None,
        include_future: bool = True,
        limit: int = 10,
    ) -> list[dict]:
        statuses = {"ACTIVE", "FUTURE"} if include_future else {"ACTIVE"}
        rows = [
            {
                **event,
                "reference_mode": self._reference_mode(event),
            }
            for event in self.list_policy_events(reference_date=reference_date)
            if event["impact_level"] == "HIGH" and event["status"] in statuses
        ]
        return rows[:limit]

    def normalize_policy_event(self, payload: dict) -> dict:
        normalized = {
            "policy_type": str(payload.get("policy_type") or "").strip().upper(),
            "title": str(payload.get("title") or "").strip(),
            "summary": str(payload.get("summary") or "").strip(),
            "detail": str(payload.get("detail") or payload.get("source_text") or "").strip(),
            "effective_from": str(payload.get("effective_from") or "").strip(),
            "effective_to": self._optional_text(payload.get("effective_to")),
            "affected_region_sido": self._optional_text(payload.get("affected_region_sido")),
            "affected_region_sigungu": self._optional_text(
                payload.get("affected_region_sigungu")
            ),
            "affected_region_dong": self._optional_text(payload.get("affected_region_dong")),
            "affected_buyer_type": str(
                payload.get("affected_buyer_type") or "ANY"
            ).strip().upper(),
            "affected_investment_purpose": str(
                payload.get("affected_investment_purpose") or "ANY"
            ).strip().upper(),
            "impact_level": str(payload.get("impact_level") or "").strip().upper(),
            "calculation_supported": bool(payload.get("calculation_supported")),
            "action_required": bool(payload.get("action_required")),
            "source_text": str(payload.get("source_text") or "").strip(),
            "source_name": self._optional_text(payload.get("source_name")),
            "status": "ACTIVE",
        }

        if normalized["policy_type"] not in POLICY_EVENT_TYPES:
            raise ValueError(f"Unsupported policy event type: {normalized['policy_type']}")
        if not normalized["title"]:
            raise ValueError("Policy event title is required.")
        if not normalized["summary"]:
            raise ValueError("Policy event summary is required.")
        if not normalized["detail"]:
            raise ValueError("Policy event detail is required.")
        if normalized["affected_buyer_type"] not in BUYER_TYPES:
            raise ValueError(
                f"Unsupported affected buyer type: {normalized['affected_buyer_type']}"
            )
        if normalized["affected_investment_purpose"] not in INVESTMENT_PURPOSES:
            raise ValueError(
                "Unsupported affected investment purpose: "
                f"{normalized['affected_investment_purpose']}"
            )
        if normalized["impact_level"] not in IMPACT_LEVELS:
            raise ValueError(f"Unsupported impact level: {normalized['impact_level']}")
        if not normalized["source_text"]:
            raise ValueError("Policy event source text is required.")

        try:
            effective_from_date = date.fromisoformat(normalized["effective_from"])
        except ValueError as exc:
            raise ValueError(f"Invalid effective_from date: {exc}") from exc
        if normalized["effective_to"] is not None:
            try:
                effective_to_date = date.fromisoformat(normalized["effective_to"])
            except ValueError as exc:
                raise ValueError(f"Invalid effective_to date: {exc}") from exc
            if effective_to_date < effective_from_date:
                normalized["effective_from"] = normalized["effective_to"]
                effective_from_date = effective_to_date

        normalized["status"] = self.calculate_status(
            effective_from=normalized["effective_from"],
            effective_to=normalized["effective_to"],
        )
        return normalized

    def calculate_status(
        self,
        *,
        effective_from: str,
        effective_to: str | None,
        reference_date: date | None = None,
    ) -> str:
        target_date = reference_date or date.today()
        start_date = date.fromisoformat(effective_from)
        if target_date < start_date:
            return "FUTURE"
        if effective_to and target_date > date.fromisoformat(effective_to):
            return "EXPIRED"
        return "ACTIVE"

    def _decorate_event(self, event: dict, *, reference_date: date | None = None) -> dict:
        decorated = dict(event)
        decorated["status"] = self.calculate_status(
            effective_from=str(event["effective_from"]),
            effective_to=event.get("effective_to"),
            reference_date=reference_date,
        )
        return decorated

    def _persist_status_if_needed(self, event: dict, calculated_status: str) -> None:
        if str(event.get("status")) == calculated_status:
            return
        self.policy_event_repository.update(
            int(event["policy_event_id"]),
            policy_type=str(event["policy_type"]),
            title=str(event["title"]),
            summary=str(event["summary"]),
            detail=str(event["detail"]),
            effective_from=str(event["effective_from"]),
            effective_to=event.get("effective_to"),
            affected_region_sido=event.get("affected_region_sido"),
            affected_region_sigungu=event.get("affected_region_sigungu"),
            affected_region_dong=event.get("affected_region_dong"),
            affected_buyer_type=str(event["affected_buyer_type"]),
            affected_investment_purpose=str(event["affected_investment_purpose"]),
            impact_level=str(event["impact_level"]),
            calculation_supported=bool(event.get("calculation_supported")),
            action_required=bool(event.get("action_required")),
            source_text=str(event["source_text"]),
            source_name=event.get("source_name"),
            status=calculated_status,
        )

    def _matches_region(
        self,
        event: dict,
        *,
        sido: str | None,
        sigungu: str | None,
        dong: str | None,
    ) -> bool:
        event_sido = self._optional_text(event.get("affected_region_sido"))
        event_sigungu = self._optional_text(event.get("affected_region_sigungu"))
        event_dong = self._optional_text(event.get("affected_region_dong"))
        target_sido = self._optional_text(sido)
        target_sigungu = self._optional_text(sigungu)
        target_dong = self._optional_text(dong)

        if event_sido and event_sido != target_sido:
            return False
        if event_sigungu and event_sigungu != target_sigungu:
            return False
        if event_dong and event_dong != target_dong:
            return False
        return True

    def _matches_buyer_type(self, event: dict, buyer_type: str) -> bool:
        return event["affected_buyer_type"] in {"ANY", buyer_type}

    def _matches_investment_purpose(self, event: dict, investment_purpose: str) -> bool:
        return event["affected_investment_purpose"] in {"ANY", investment_purpose}

    def _reference_mode(self, event: dict) -> str:
        if event.get("calculation_supported"):
            return "CALCULATION_SUPPORTED_REFERENCE"
        return "REFERENCE_ONLY"

    def _event_sort_key(self, event: dict) -> tuple[int, int, str, int]:
        region_specificity = sum(
            1
            for key in (
                "affected_region_sido",
                "affected_region_sigungu",
                "affected_region_dong",
            )
            if event.get(key)
        )
        return (
            _IMPACT_PRIORITY.get(str(event["impact_level"]), 0),
            _STATUS_PRIORITY.get(str(event["status"]), 0),
            str(event["effective_from"]),
            region_specificity,
        )

    def _optional_text(self, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
