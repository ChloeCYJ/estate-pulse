from __future__ import annotations

import unittest

from modules.collectors.molit_sale_collector import MolitSaleCollector, SALE_API_URL


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _FakeSession:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    def get(self, url: str, *, params: dict, timeout: int):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        if not self.responses:
            raise AssertionError("No fake response prepared.")
        return _FakeResponse(self.responses.pop(0))


class MolitSaleCollectorTests(unittest.TestCase):
    def test_collect_parses_items_from_xml_response(self) -> None:
        session = _FakeSession(
            [
                """
                <response>
                  <header>
                    <resultCode>00</resultCode>
                    <resultMsg>NORMAL SERVICE.</resultMsg>
                  </header>
                  <body>
                    <items>
                      <item>
                        <aptNm>River Park</aptNm>
                        <umdNm>Banpo-dong</umdNm>
                        <jibun>10</jibun>
                        <dealYear>2026</dealYear>
                        <dealMonth>6</dealMonth>
                        <dealDay>14</dealDay>
                        <dealAmount>950,000</dealAmount>
                        <excluUseAr>84.98</excluUseAr>
                        <floor>12</floor>
                      </item>
                    </items>
                    <numOfRows>1000</numOfRows>
                    <pageNo>1</pageNo>
                    <totalCount>1</totalCount>
                  </body>
                </response>
                """
            ]
        )
        collector = MolitSaleCollector(
            service_key="test-key",
            session=session,
        )

        rows = collector.collect(lawd_code="11680", year_month="202606")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["aptNm"], "River Park")
        self.assertEqual(rows[0]["dealAmount"], "950,000")
        self.assertEqual(session.calls[0]["url"], SALE_API_URL)
        self.assertEqual(session.calls[0]["params"]["LAWD_CD"], "11680")
        self.assertEqual(session.calls[0]["params"]["DEAL_YMD"], "202606")

    def test_collect_parses_general_service_xml_with_namespace(self) -> None:
        session = _FakeSession(
            [
                """
                <ns2:response xmlns:ns2="http://openapi.data.go.kr/service/rest/RTMSDataSvcAptTrade">
                  <ns2:header>
                    <ns2:resultCode>000</ns2:resultCode>
                    <ns2:resultMsg>OK</ns2:resultMsg>
                  </ns2:header>
                  <ns2:body>
                    <ns2:items>
                      <ns2:item>
                        <ns2:aptNm>River Park</ns2:aptNm>
                        <ns2:umdNm>Banpo-dong</ns2:umdNm>
                        <ns2:jibun>10</ns2:jibun>
                        <ns2:dealYear>2026</ns2:dealYear>
                        <ns2:dealMonth>6</ns2:dealMonth>
                        <ns2:dealDay>14</ns2:dealDay>
                        <ns2:dealAmount>950,000</ns2:dealAmount>
                        <ns2:excluUseAr>84.98</ns2:excluUseAr>
                        <ns2:floor>12</ns2:floor>
                      </ns2:item>
                    </ns2:items>
                    <ns2:totalCount>1</ns2:totalCount>
                  </ns2:body>
                </ns2:response>
                """
            ]
        )
        collector = MolitSaleCollector(
            service_key="test-key",
            session=session,
        )

        rows = collector.collect(lawd_code="11680", year_month="202606")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["aptNm"], "River Park")
        self.assertEqual(rows[0]["excluUseAr"], "84.98")

    def test_collect_raises_when_api_returns_error(self) -> None:
        session = _FakeSession(
            [
                """
                <response>
                  <header>
                    <resultCode>30</resultCode>
                    <resultMsg>SERVICE KEY IS NOT REGISTERED ERROR.</resultMsg>
                  </header>
                  <body>
                    <items />
                    <totalCount>0</totalCount>
                  </body>
                </response>
                """
            ]
        )
        collector = MolitSaleCollector(
            service_key="bad-key",
            session=session,
        )

        with self.assertRaisesRegex(ValueError, "MOLIT sale API request failed"):
            collector.collect(lawd_code="11680", year_month="202606")


if __name__ == "__main__":
    unittest.main()
