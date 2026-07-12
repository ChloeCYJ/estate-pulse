from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


JUSO_API_URL = "https://business.juso.go.kr/addrlink/addrLinkApi.do"
SUCCESS_ERROR_CODE = "0"


class JusoAddressApiError(ValueError):
    """Base application error for Juso API calls."""


class JusoAddressApiConfigurationError(JusoAddressApiError):
    """Raised when JUSO_API_KEY is not configured."""


class JusoAddressApiConnectionError(JusoAddressApiError):
    """Raised when the Juso API is temporarily unavailable."""


class JusoAddressApiBusinessError(JusoAddressApiError):
    """Raised when the Juso API returns a business-level error."""


@dataclass
class JusoAddressClient:
    service_key: str | None
    api_url: str = JUSO_API_URL
    session: requests.Session | None = None
    connect_timeout_seconds: int = 2
    read_timeout_seconds: int = 5

    def search(
        self,
        *,
        keyword: str,
        current_page: int = 1,
        count_per_page: int = 20,
    ) -> list[dict[str, Any]]:
        if not self.service_key:
            raise JusoAddressApiConfigurationError("JUSO_API_KEY is required for address search.")

        request_params = {
            "confmKey": self.service_key,
            "keyword": keyword,
            "currentPage": current_page,
            "countPerPage": count_per_page,
            "resultType": "json",
            "hstryYn": "N",
            "firstSort": "none",
            "addInfoYn": "Y",
        }
        session = self.session or requests.Session()

        attempt = 0
        while True:
            try:
                response = session.get(
                    self.api_url,
                    params=request_params,
                    timeout=(self.connect_timeout_seconds, self.read_timeout_seconds),
                )
                response.raise_for_status()
                payload = response.json()
                return _parse_juso_payload(payload)
            except requests.Timeout as exc:
                if attempt >= 1:
                    raise JusoAddressApiConnectionError(
                        "Juso address API is temporarily unavailable."
                    ) from exc
                attempt += 1
                continue
            except requests.HTTPError as exc:
                status_code = int(getattr(getattr(exc, "response", None), "status_code", 0) or 0)
                if status_code >= 500 and attempt < 1:
                    attempt += 1
                    continue
                raise JusoAddressApiConnectionError(
                    "Juso address API is temporarily unavailable."
                ) from exc
            except requests.RequestException as exc:
                raise JusoAddressApiConnectionError(
                    "Juso address API is temporarily unavailable."
                ) from exc


def _parse_juso_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results")
    if not isinstance(results, dict):
        raise JusoAddressApiBusinessError("Juso address API returned an invalid response.")

    common = results.get("common")
    if not isinstance(common, dict):
        raise JusoAddressApiBusinessError("Juso address API returned an invalid response.")

    error_code = str(common.get("errorCode") or "").strip()
    error_message = str(common.get("errorMessage") or "").strip()
    if error_code != SUCCESS_ERROR_CODE:
        raise JusoAddressApiBusinessError(error_message or f"Juso address API error: {error_code}")

    raw_rows = results.get("juso") or []
    if not isinstance(raw_rows, list):
        return []
    return [row for row in raw_rows if isinstance(row, dict)]
