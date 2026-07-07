from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any
from xml.etree import ElementTree

import requests


SALE_API_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
SUCCESS_RESULT_CODES = {"00", "000"}


@dataclass
class MolitSaleCollector:
    service_key: str | None
    api_url: str = SALE_API_URL
    timeout_seconds: int = 15
    session: requests.Session | None = None

    def collect(self, *, lawd_code: str, year_month: str) -> list[dict]:
        if not self.service_key:
            raise ValueError("MOLIT_SERVICE_KEY is required for MOLIT sale import.")
        if not re.fullmatch(r"\d{5}", lawd_code.strip()):
            raise ValueError("LAWD_CD must be a 5-digit lawd code.")
        if not re.fullmatch(r"\d{6}", year_month.strip()):
            raise ValueError("year_month must be in YYYYMM format.")

        page_no = 1
        num_of_rows = 1000
        collected_items: list[dict[str, str]] = []
        session = self.session or requests.Session()

        while True:
            response = session.get(
                self.api_url,
                params={
                    "serviceKey": self.service_key,
                    "LAWD_CD": lawd_code,
                    "DEAL_YMD": year_month,
                    "pageNo": page_no,
                    "numOfRows": num_of_rows,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()

            payload = _parse_response_xml(response.text)
            result_code = payload["result_code"]
            if not _is_success_result_code(result_code):
                result_message = payload["result_message"] or "Unknown MOLIT API error."
                raise ValueError(f"MOLIT sale API request failed: {result_code} {result_message}")

            items = payload["items"]
            collected_items.extend(items)
            total_count = int(payload["total_count"] or 0)
            if not items or len(collected_items) >= total_count:
                break
            page_no += 1

        return collected_items


def _parse_response_xml(xml_text: str) -> dict[str, Any]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise ValueError("Failed to parse MOLIT sale API response.") from exc

    items: list[dict[str, str]] = []
    for item_element in _find_elements(root, "item"):
        item: dict[str, str] = {}
        for child in list(item_element):
            key = _local_name(child.tag)
            value = (child.text or "").strip()
            item[key] = value
        if item:
            items.append(item)

    return {
        "result_code": _find_first_text(root, "resultCode"),
        "result_message": _find_first_text(root, "resultMsg"),
        "total_count": _find_first_text(root, "totalCount"),
        "items": items,
    }


def _find_first_text(root: ElementTree.Element, *tag_names: str) -> str | None:
    target_names = set(tag_names)
    for element in root.iter():
        if _local_name(element.tag) not in target_names:
            continue
        value = (element.text or "").strip()
        if value:
            return value
    return None


def _find_elements(root: ElementTree.Element, tag_name: str) -> list[ElementTree.Element]:
    return [element for element in root.iter() if _local_name(element.tag) == tag_name]


def _is_success_result_code(result_code: str | None) -> bool:
    return str(result_code or "").strip() in SUCCESS_RESULT_CODES


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag
