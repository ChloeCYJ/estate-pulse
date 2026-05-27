from __future__ import annotations


class RegulationCollector:
    def collect(self, *, region_name: str) -> list[dict]:
        raise NotImplementedError(
            "Public regulation data collection is not implemented in Phase 1."
        )
