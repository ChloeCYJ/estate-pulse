from __future__ import annotations

import unittest

from modules.services.address_search_service import AddressCandidate, AddressSearchService


class _StubJusoAddressClient:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.calls: list[dict] = []

    def search(self, *, keyword: str, current_page: int = 1, count_per_page: int = 20) -> list[dict]:
        self.calls.append(
            {
                "keyword": keyword,
                "current_page": current_page,
                "count_per_page": count_per_page,
            }
        )
        return list(self.rows)


class AddressSearchServiceTests(unittest.TestCase):
    def test_search_rejects_keyword_shorter_than_two_characters(self) -> None:
        service = AddressSearchService(juso_address_client=_StubJusoAddressClient([]))

        with self.assertRaisesRegex(ValueError, "at least 2 characters"):
            service.search_candidates(keyword="행")

    def test_search_returns_only_capital_area_apartment_candidates(self) -> None:
        service = AddressSearchService(
            juso_address_client=_StubJusoAddressClient(
                [
                    self._row(si_nm="서울특별시", sgg_nm="성동구", emd_nm="행당동", bd_nm="행당한진타운", bd_kdcd="1"),
                    self._row(si_nm="경기도", sgg_nm="성남시", emd_nm="백현동", bd_nm="판교아파트", bd_kdcd="1"),
                    self._row(si_nm="인천광역시", sgg_nm="연수구", emd_nm="송도동", bd_nm="송도아파트", bd_kdcd="1"),
                    self._row(si_nm="부산광역시", sgg_nm="해운대구", emd_nm="우동", bd_nm="부산아파트", bd_kdcd="1"),
                    self._row(si_nm="서울특별시", sgg_nm="성동구", emd_nm="행당동", bd_nm="행당오피스텔", bd_kdcd="0"),
                ]
            )
        )

        candidates = service.search_candidates(keyword="아파트")

        self.assertEqual(
            [(item.sido, item.sigungu, item.complex_name) for item in candidates],
            [
                ("서울특별시", "성동구", "행당한진타운"),
                ("경기도", "성남시", "판교아파트"),
                ("인천광역시", "연수구", "송도아파트"),
            ],
        )

    def test_search_deduplicates_same_complex_name_and_same_road_address(self) -> None:
        road_addr = "서울특별시 성동구 행당로 82"
        service = AddressSearchService(
            juso_address_client=_StubJusoAddressClient(
                [
                    self._row(road_addr=road_addr, bd_nm="행당한진타운", bd_kdcd="1"),
                    self._row(road_addr=road_addr, bd_nm="행당한진타운", bd_kdcd="1"),
                ]
            )
        )

        candidates = service.search_candidates(keyword="행당")

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].road_address, road_addr)

    def test_search_maps_row_to_address_candidate_fields(self) -> None:
        service = AddressSearchService(
            juso_address_client=_StubJusoAddressClient(
                [
                    self._row(
                        road_addr="서울특별시 성동구 행당로 82",
                        jibun_addr="서울특별시 성동구 행당동 346",
                        si_nm="서울특별시",
                        sgg_nm="성동구",
                        emd_nm="행당동",
                        li_nm="",
                        adm_cd="1120010700",
                        bd_mgt_sn="1120010700103460000012345",
                        bd_nm="행당한진타운",
                        bd_kdcd="1",
                    )
                ]
            )
        )

        candidates = service.search_candidates(keyword="행당")

        self.assertEqual(
            candidates,
            [
                AddressCandidate(
                    complex_name="행당한진타운",
                    road_address="서울특별시 성동구 행당로 82",
                    jibun_address="서울특별시 성동구 행당동 346",
                    sido="서울특별시",
                    sigungu="성동구",
                    emd="행당동",
                    li="",
                    admin_code="1120010700",
                    building_management_no="1120010700103460000012345",
                    is_apartment=True,
                )
            ],
        )

    def test_search_returns_empty_when_no_capital_area_apartment_candidates_exist(self) -> None:
        service = AddressSearchService(
            juso_address_client=_StubJusoAddressClient(
                [
                    self._row(si_nm="부산광역시", sgg_nm="해운대구", emd_nm="우동", bd_nm="부산아파트", bd_kdcd="1"),
                    self._row(si_nm="서울특별시", sgg_nm="성동구", emd_nm="행당동", bd_nm="행당오피스텔", bd_kdcd="0"),
                ]
            )
        )

        self.assertEqual(service.search_candidates(keyword="행당"), [])
        self.assertEqual(service.last_raw_result_count, 2)
        self.assertEqual(service.last_candidate_count, 0)

    @staticmethod
    def _row(
        *,
        road_addr: str = "서울특별시 성동구 행당로 82",
        jibun_addr: str = "서울특별시 성동구 행당동 346",
        si_nm: str = "서울특별시",
        sgg_nm: str = "성동구",
        emd_nm: str = "행당동",
        li_nm: str = "",
        adm_cd: str = "1120010700",
        bd_mgt_sn: str = "1120010700103460000012345",
        bd_nm: str = "행당한진타운",
        bd_kdcd: str = "1",
    ) -> dict:
        return {
            "roadAddr": road_addr,
            "jibunAddr": jibun_addr,
            "siNm": si_nm,
            "sggNm": sgg_nm,
            "emdNm": emd_nm,
            "liNm": li_nm,
            "admCd": adm_cd,
            "bdMgtSn": bd_mgt_sn,
            "bdNm": bd_nm,
            "bdKdcd": bd_kdcd,
        }


if __name__ == "__main__":
    unittest.main()
