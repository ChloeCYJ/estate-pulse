from __future__ import annotations

from datetime import date


REGION_LEVELS = ("SIDO", "SIGUNGU", "DONG")
POLICY_TYPES = (
    "REGULATED_AREA",
    "NON_REGULATED_AREA",
    "LAND_TRANSACTION_PERMISSION",
    "SPECULATION_OVERHEATED_DISTRICT",
    "ADJUSTMENT_TARGET_AREA",
)
CREATABLE_POLICY_TYPES = (
    "NON_REGULATED_AREA",
    "LAND_TRANSACTION_PERMISSION",
    "SPECULATION_OVERHEATED_DISTRICT",
    "ADJUSTMENT_TARGET_AREA",
)
LOAN_REGION_TYPES = ("REGULATED", "NON_REGULATED")
_LOAN_POLICY_TO_REGION_TYPE = {
    "REGULATED_AREA": "REGULATED",
    "NON_REGULATED_AREA": "NON_REGULATED",
    "LAND_TRANSACTION_PERMISSION": "LAND_TRANSACTION_PERMISSION",
    "SPECULATION_OVERHEATED_DISTRICT": "SPECULATION_OVERHEATED_DISTRICT",
    "ADJUSTMENT_TARGET_AREA": "ADJUSTMENT_TARGET_AREA",
}
_POSITIVE_LOAN_POLICY_TYPES = {
    "REGULATED_AREA",
    "LAND_TRANSACTION_PERMISSION",
    "SPECULATION_OVERHEATED_DISTRICT",
    "ADJUSTMENT_TARGET_AREA",
}
_SPECIFICITY_SCORE = {
    "SIDO": 1,
    "SIGUNGU": 2,
    "DONG": 3,
}


class RegionPolicyService:
    def __init__(self, *, region_policy_repository) -> None:
        self.region_policy_repository = region_policy_repository

    def list_region_levels(self) -> list[str]:
        return list(REGION_LEVELS)

    def list_policy_types(self) -> list[str]:
        return list(CREATABLE_POLICY_TYPES)

    def create_region_policy_status(
        self,
        *,
        region_level: str,
        sido: str,
        sigungu: str | None,
        dong: str | None,
        policy_type: str,
        effective_from: str,
        effective_to: str | None,
        notes: str | None,
        source_policy_import_id: int | None = None,
    ) -> int:
        normalized = self._normalize_status_payload(
            region_level=region_level,
            sido=sido,
            sigungu=sigungu,
            dong=dong,
            policy_type=policy_type,
            effective_from=effective_from,
            effective_to=effective_to,
            notes=notes,
            source_policy_import_id=source_policy_import_id,
        )
        self._raise_if_scope_conflicts(normalized)
        return self.region_policy_repository.create(**normalized)

    def delete_region_policy_status(self, status_id: int) -> None:
        if not self.region_policy_repository.get(status_id):
            raise ValueError("Region policy status not found.")
        self.region_policy_repository.delete(status_id)

    def list_region_policy_statuses(self) -> list[dict]:
        rows: list[dict] = []
        for item in self.region_policy_repository.list_all():
            rows.append(
                {
                    **item,
                    "region_scope": self._region_scope_label(item),
                    "specificity_score": _SPECIFICITY_SCORE.get(str(item["region_level"]), 0),
                    "loan_region_type": _LOAN_POLICY_TO_REGION_TYPE.get(str(item["policy_type"])),
                }
            )
        return rows

    def resolve_region_context(
        self,
        *,
        sido: str | None,
        sigungu: str | None,
        dong: str | None,
        reference_date: date | None = None,
    ) -> dict:
        target_date = reference_date or date.today()
        normalized_address = {
            "sido": (sido or "").strip(),
            "sigungu": (sigungu or "").strip(),
            "dong": (dong or "").strip(),
        }
        matching_statuses = [
            item
            for item in self.list_region_policy_statuses()
            if self._matches_scope(item, normalized_address)
            and self._is_effective(item, target_date)
        ]
        matching_statuses.sort(
            key=lambda item: (
                int(item["specificity_score"]),
                str(item["effective_from"]),
                int(item["id"]),
            ),
            reverse=True,
        )

        loan_policy = next(
            (
                item
                for item in matching_statuses
                if str(item["policy_type"]) in _LOAN_POLICY_TO_REGION_TYPE
            ),
            None,
        )
        resolved_region_type = (
            _LOAN_POLICY_TO_REGION_TYPE[str(loan_policy["policy_type"])]
            if loan_policy is not None
            else "NON_REGULATED"
        )

        return {
            "region_type": resolved_region_type,
            "source": "region_policy_status" if loan_policy is not None else "default",
            "matched_loan_policy": loan_policy,
            "active_policies": matching_statuses,
        }

    def _normalize_status_payload(
        self,
        *,
        region_level: str,
        sido: str,
        sigungu: str | None,
        dong: str | None,
        policy_type: str,
        effective_from: str,
        effective_to: str | None,
        notes: str | None,
        source_policy_import_id: int | None,
    ) -> dict:
        normalized = {
            "region_level": str(region_level).strip().upper(),
            "sido": str(sido).strip(),
            "sigungu": (sigungu or "").strip() or None,
            "dong": (dong or "").strip() or None,
            "policy_type": str(policy_type).strip().upper(),
            "effective_from": str(effective_from).strip(),
            "effective_to": (str(effective_to).strip() if effective_to else None),
            "notes": (str(notes).strip() if notes else None),
            "source_policy_import_id": source_policy_import_id,
        }
        if normalized["dong"]:
            normalized["region_level"] = "DONG"
        elif normalized["sigungu"]:
            normalized["region_level"] = "SIGUNGU"

        if normalized["region_level"] not in REGION_LEVELS:
            raise ValueError(f"Unsupported region level: {normalized['region_level']}")
        if normalized["policy_type"] not in POLICY_TYPES:
            raise ValueError(f"Unsupported policy type: {normalized['policy_type']}")
        if not normalized["sido"]:
            raise ValueError("sido is required.")
        if normalized["region_level"] in {"SIGUNGU", "DONG"} and not normalized["sigungu"]:
            raise ValueError("sigungu is required for SIGUNGU or DONG level.")
        if normalized["region_level"] == "DONG" and not normalized["dong"]:
            raise ValueError("dong is required for DONG level.")
        if normalized["region_level"] == "SIDO":
            normalized["sigungu"] = None
            normalized["dong"] = None
        elif normalized["region_level"] == "SIGUNGU":
            normalized["dong"] = None

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
                raise ValueError("effective_from must be earlier than or equal to effective_to.")

        return normalized

    def _raise_if_scope_conflicts(self, normalized: dict) -> None:
        for item in self.region_policy_repository.list_all():
            if not self._same_scope(item, normalized):
                continue
            if self._date_ranges_overlap(item, normalized):
                existing_policy_type = str(item["policy_type"])
                new_policy_type = str(normalized["policy_type"])
                if existing_policy_type == new_policy_type:
                    raise ValueError(
                        "An overlapping region policy already exists for the same scope and type."
                    )
                if self._is_non_regulated_conflict(existing_policy_type, new_policy_type):
                    raise ValueError(
                        "A non-regulated status cannot overlap with an active regulated status for the same scope."
                    )

    def _is_non_regulated_conflict(self, left_policy_type: str, right_policy_type: str) -> bool:
        left_is_non_regulated = left_policy_type == "NON_REGULATED_AREA"
        right_is_non_regulated = right_policy_type == "NON_REGULATED_AREA"
        left_is_regulated = left_policy_type in _POSITIVE_LOAN_POLICY_TYPES
        right_is_regulated = right_policy_type in _POSITIVE_LOAN_POLICY_TYPES
        return (left_is_non_regulated and right_is_regulated) or (
            right_is_non_regulated and left_is_regulated
        )

    def _same_scope(self, left: dict, right: dict) -> bool:
        return (
            str(left["region_level"]) == str(right["region_level"])
            and str(left["sido"]) == str(right["sido"])
            and (left.get("sigungu") or None) == (right.get("sigungu") or None)
            and (left.get("dong") or None) == (right.get("dong") or None)
        )

    def _date_ranges_overlap(self, left: dict, right: dict) -> bool:
        left_start = date.fromisoformat(str(left["effective_from"]))
        right_start = date.fromisoformat(str(right["effective_from"]))
        left_end = (
            date.max
            if left.get("effective_to") in (None, "")
            else date.fromisoformat(str(left["effective_to"]))
        )
        right_end = (
            date.max
            if right.get("effective_to") in (None, "")
            else date.fromisoformat(str(right["effective_to"]))
        )
        return left_start <= right_end and right_start <= left_end

    def _is_effective(self, item: dict, target_date: date) -> bool:
        effective_from = date.fromisoformat(str(item["effective_from"]))
        if target_date < effective_from:
            return False
        effective_to = item.get("effective_to")
        if not effective_to:
            return True
        return target_date <= date.fromisoformat(str(effective_to))

    def _matches_scope(self, item: dict, normalized_address: dict) -> bool:
        if str(item["sido"]) != normalized_address["sido"]:
            return False
        if str(item["region_level"]) == "SIDO":
            return True
        if (item.get("sigungu") or "") != normalized_address["sigungu"]:
            return False
        if str(item["region_level"]) == "SIGUNGU":
            return True
        return (item.get("dong") or "") == normalized_address["dong"]

    def _region_scope_label(self, item: dict) -> str:
        if str(item["region_level"]) == "SIDO":
            return str(item["sido"])
        if str(item["region_level"]) == "SIGUNGU":
            return f"{item['sido']} {item['sigungu']}"
        return f"{item['sido']} {item['sigungu']} {item['dong']}"
