from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class AppSettings:
    app_name: str
    database_path: Path
    acquisition_tax_rate: float
    brokerage_fee_rate: float
    legal_fee_fixed: int
    contingency_rate: float
    default_ltv_limit: float
    molit_service_key: str | None
    reb_service_key: str | None
    database_url: str | None = None

    @property
    def database_target(self) -> Path | str:
        return self.database_url or self.database_path


def _get_env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value is not None else default


def _get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    database_url = os.getenv("DATABASE_URL")
    database_path = Path(os.getenv("DATABASE_PATH", BASE_DIR / "data" / "app.db"))
    if not database_url:
        database_path.parent.mkdir(parents=True, exist_ok=True)

    return AppSettings(
        app_name=os.getenv("APP_NAME", "Estate Pulse"),
        database_path=database_path,
        acquisition_tax_rate=_get_env_float("ACQUISITION_TAX_RATE", 0.011),
        brokerage_fee_rate=_get_env_float("BROKERAGE_FEE_RATE", 0.004),
        legal_fee_fixed=_get_env_int("LEGAL_FEE_FIXED", 300000),
        contingency_rate=_get_env_float("CONTINGENCY_RATE", 0.005),
        default_ltv_limit=_get_env_float("DEFAULT_LTV_LIMIT", 0.6),
        molit_service_key=os.getenv("MOLIT_SERVICE_KEY"),
        reb_service_key=os.getenv("REB_SERVICE_KEY"),
        database_url=database_url,
    )
