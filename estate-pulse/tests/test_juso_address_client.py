from __future__ import annotations

import unittest

import requests

from modules.collectors.juso_address_client import (
    JusoAddressApiBusinessError,
    JusoAddressApiConfigurationError,
    JusoAddressApiConnectionError,
    JusoAddressClient,
)


class _FakeResponse:
    def __init__(
        self,
        *,
        json_data: dict | None = None,
        status_code: int = 200,
        http_error: Exception | None = None,
    ) -> None:
        self._json_data = json_data or {}
        self.status_code = status_code
        self._http_error = http_error

    def raise_for_status(self) -> None:
        if self._http_error is not None:
            raise self._http_error

    def json(self) -> dict:
        return self._json_data


class _FakeSession:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    def get(self, url: str, *, params: dict, timeout: tuple[int, int]):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        if not self.responses:
            raise AssertionError("No fake response prepared.")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class JusoAddressClientTests(unittest.TestCase):
    def test_search_returns_raw_juso_rows_for_normal_response(self) -> None:
        session = _FakeSession(
            [
                _FakeResponse(
                    json_data={
                        "results": {
                            "common": {"errorCode": "0", "errorMessage": "정상"},
                            "juso": [{"bdNm": "행당한진타운"}],
                        }
                    }
                )
            ]
        )
        client = JusoAddressClient(
            service_key="test-key",
            session=session,
        )

        rows = client.search(keyword="행당")

        self.assertEqual(rows, [{"bdNm": "행당한진타운"}])
        self.assertEqual(session.calls[0]["params"]["keyword"], "행당")
        self.assertEqual(session.calls[0]["params"]["resultType"], "json")
        self.assertEqual(session.calls[0]["timeout"], (2, 5))

    def test_search_raises_for_missing_service_key(self) -> None:
        client = JusoAddressClient(service_key=None)

        with self.assertRaisesRegex(JusoAddressApiConfigurationError, "JUSO_API_KEY"):
            client.search(keyword="행당")

    def test_search_raises_for_api_business_error(self) -> None:
        session = _FakeSession(
            [
                _FakeResponse(
                    json_data={
                        "results": {
                            "common": {
                                "errorCode": "E0006",
                                "errorMessage": "검색어가 없습니다.",
                            },
                            "juso": [],
                        }
                    }
                )
            ]
        )
        client = JusoAddressClient(
            service_key="test-key",
            session=session,
        )

        with self.assertRaisesRegex(JusoAddressApiBusinessError, "검색어가 없습니다"):
            client.search(keyword="행당")

    def test_search_retries_once_for_timeout(self) -> None:
        session = _FakeSession(
            [
                requests.Timeout("connect timeout"),
                _FakeResponse(
                    json_data={
                        "results": {
                            "common": {"errorCode": "0", "errorMessage": "정상"},
                            "juso": [{"bdNm": "행당한진타운"}],
                        }
                    }
                ),
            ]
        )
        client = JusoAddressClient(
            service_key="test-key",
            session=session,
        )

        rows = client.search(keyword="행당")

        self.assertEqual(rows, [{"bdNm": "행당한진타운"}])
        self.assertEqual(len(session.calls), 2)

    def test_search_retries_once_for_http_5xx(self) -> None:
        request = requests.Request("GET", "https://example.com").prepare()
        first_error = requests.HTTPError("502 Server Error")
        first_error.response = requests.Response()
        first_error.response.status_code = 502
        first_error.request = request
        session = _FakeSession(
            [
                _FakeResponse(http_error=first_error, status_code=502),
                _FakeResponse(
                    json_data={
                        "results": {
                            "common": {"errorCode": "0", "errorMessage": "정상"},
                            "juso": [{"bdNm": "행당한진타운"}],
                        }
                    }
                ),
            ]
        )
        client = JusoAddressClient(
            service_key="test-key",
            session=session,
        )

        rows = client.search(keyword="행당")

        self.assertEqual(rows, [{"bdNm": "행당한진타운"}])
        self.assertEqual(len(session.calls), 2)

    def test_search_raises_connection_error_after_retry_exhausted(self) -> None:
        session = _FakeSession(
            [
                requests.Timeout("connect timeout"),
                requests.Timeout("connect timeout"),
            ]
        )
        client = JusoAddressClient(
            service_key="test-key",
            session=session,
        )

        with self.assertRaisesRegex(JusoAddressApiConnectionError, "temporarily unavailable"):
            client.search(keyword="행당")


if __name__ == "__main__":
    unittest.main()
