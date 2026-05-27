from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MolitSaleCollector:
    service_key: str | None

    def collect(self, *, complex_name: str, year_month: str) -> list[dict]:
        raise NotImplementedError(
            "Public API integration is not implemented in Phase 1. "
            "Wire the official MOLIT sale API here in a later phase."
        )
