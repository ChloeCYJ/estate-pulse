from __future__ import annotations

from pathlib import Path


class TransactionRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def bulk_upsert_sale_transactions(self, payload: list[dict]) -> None:
        raise NotImplementedError("Public transaction ingestion is not implemented in Phase 1.")

    def bulk_upsert_rent_transactions(self, payload: list[dict]) -> None:
        raise NotImplementedError("Public rent ingestion is not implemented in Phase 1.")
