from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RebStatsCollector:
    service_key: str | None

    def collect(self, *, region_code: str) -> list[dict]:
        raise NotImplementedError(
            "Public API integration is not implemented in Phase 1. "
            "Wire the official REB statistics API here in a later phase."
        )
