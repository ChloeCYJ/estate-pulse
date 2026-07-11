from __future__ import annotations

import pandas as pd
import streamlit as st


MOLIT_SEARCH_RESULTS_KEY = "complex_molit_search_results"
MOLIT_SEARCH_KEYWORD_KEY = "complex_molit_search_keyword"


def render_complex_page(
    complex_repository,
    *,
    molit_complex_search_service=None,
) -> None:
    st.title("단지 등록")
    st.caption(
        "사용자는 아파트명만 검색하고, 주소/법정동/LAWD_CD는 MOLIT 후보와 법정동코드 기준으로 자동 매핑합니다."
    )

    create_tab, manage_tab = st.tabs(
        [
            "등록",
            "관리",
        ]
    )

    with create_tab:
        _render_molit_search_registration(
            molit_complex_search_service=molit_complex_search_service,
        )
        st.divider()
        with st.expander("기존 직접 입력 등록", expanded=False):
            _render_manual_create_form(complex_repository)

    with manage_tab:
        _render_manage_tab(complex_repository)


def _render_molit_search_registration(*, molit_complex_search_service) -> None:
    st.subheader("MOLIT 아파트 검색")
    st.caption("최근 매매 실거래 raw 후보에서 검색하고, 선택된 후보를 기준으로 단지를 저장합니다.")

    collector = getattr(molit_complex_search_service, "molit_sale_collector", None)
    has_service_key = bool(getattr(collector, "service_key", None))
    if not has_service_key:
        st.warning("MOLIT_SERVICE_KEY가 설정되지 않아 MOLIT 후보 검색을 사용할 수 없습니다.")

    default_keyword = st.session_state.get(MOLIT_SEARCH_KEYWORD_KEY, "")
    with st.form("search_molit_complex_form"):
        keyword = st.text_input("아파트명 검색", value=default_keyword)
        search_clicked = st.form_submit_button(
            "MOLIT 후보 검색",
            disabled=not has_service_key,
        )

    if search_clicked:
        if molit_complex_search_service is None:
            st.error("MOLIT 검색 서비스가 준비되지 않았습니다.")
        elif not has_service_key:
            st.error("MOLIT_SERVICE_KEY를 먼저 설정해야 검색할 수 있습니다.")
        else:
            try:
                candidates = molit_complex_search_service.search_candidates(keyword=keyword.strip())
            except ValueError as exc:
                st.error(str(exc))
            except Exception as exc:  # pragma: no cover - Streamlit surface safety
                st.error(f"MOLIT 후보 검색에 실패했습니다: {exc}")
            else:
                st.session_state[MOLIT_SEARCH_KEYWORD_KEY] = keyword.strip()
                st.session_state[MOLIT_SEARCH_RESULTS_KEY] = candidates
                search_warning = getattr(molit_complex_search_service, "last_search_warning", None)
                if search_warning:
                    st.warning(search_warning)
                if not candidates:
                    st.info("검색어와 일치하는 MOLIT 후보를 찾지 못했습니다.")

    candidates = st.session_state.get(MOLIT_SEARCH_RESULTS_KEY, [])
    if not candidates:
        return

    st.caption(f"검색 결과 {len(candidates)}건")
    options = {
        _format_candidate_option_label(index=index, candidate=item): item
        for index, item in enumerate(candidates)
    }
    selected_label = st.selectbox(
        "MOLIT 후보 선택",
        list(options.keys()),
        key="complex_molit_candidate_selectbox",
    )
    selected_candidate = options[selected_label]
    _render_candidate_summary(selected_candidate)

    try:
        preview_payload = molit_complex_search_service.build_registration_payload(
            candidate=selected_candidate,
            memo=None,
        )
    except ValueError as exc:
        st.error(str(exc))
        preview_payload = None

    if selected_candidate.get("is_registered"):
        existing_complex_id = selected_candidate.get("existing_complex_id")
        st.warning(
            "이미 등록된 후보일 수 있습니다."
            + (f" existing_complex_id={existing_complex_id}" if existing_complex_id else "")
        )

    if preview_payload is not None:
        st.caption(
            "저장 예정값: "
            f"{preview_payload['name']} | "
            f"{preview_payload['sido']} {preview_payload['sigungu']} {preview_payload['dong']} | "
            f"LAWD_CD={preview_payload['molit_lawd_cd']}"
        )

    with st.form("register_molit_complex_form"):
        memo = st.text_input("등록 메모 (선택)")
        register_clicked = st.form_submit_button("선택 후보로 단지 등록")

    if register_clicked:
        if molit_complex_search_service is None:
            st.error("MOLIT 검색 서비스가 준비되지 않았습니다.")
            return
        try:
            complex_id = molit_complex_search_service.register_candidate(
                candidate=selected_candidate,
                memo=_optional_text(memo),
            )
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:  # pragma: no cover - Streamlit surface safety
            st.error(f"단지 저장에 실패했습니다: {exc}")
        else:
            st.session_state.pop(MOLIT_SEARCH_RESULTS_KEY, None)
            st.session_state.pop(MOLIT_SEARCH_KEYWORD_KEY, None)
            st.success(f"단지를 저장했습니다. complex_id={complex_id}")
            st.rerun()


def _render_candidate_summary(candidate: dict) -> None:
    details = [
        f"aptNm: {candidate.get('apt_name') or '-'}",
        f"시도: {candidate.get('sido') or '-'}",
        f"시군구: {candidate.get('sigungu') or '-'}",
        f"법정동: {candidate.get('dong') or '-'}",
        f"LAWD_CD 후보: {candidate.get('lawd_cd') or '-'}",
        f"거래일: {_format_deal_date(candidate)}",
        f"전용면적: {_format_area(candidate.get('area_m2'))}",
        f"거래금액: {_format_price(candidate.get('price'))}",
        f"거래건수: {int(candidate.get('count') or 0)}",
    ]
    st.code("\n".join(details), language="text")


def _render_manual_create_form(complex_repository) -> None:
    st.caption("기존 직접 입력 등록은 fallback 용도로 유지합니다.")
    with st.form("create_complex_form"):
        name = st.text_input("단지명*")
        col1, col2 = st.columns(2)
        with col1:
            sido = st.text_input("시도")
            sigungu = st.text_input("시군구")
        with col2:
            dong = st.text_input("동")
            build_year = st.number_input(
                "준공연도",
                min_value=0,
                step=1,
                value=0,
            )
        address = st.text_input("주소")
        st.caption("MOLIT 매핑 (선택 입력)")
        molit_col1, molit_col2 = st.columns(2)
        with molit_col1:
            molit_lawd_cd = st.text_input("MOLIT LAWD_CD")
            molit_umd_name = st.text_input("MOLIT umdNm")
        with molit_col2:
            molit_apt_name = st.text_input("MOLIT aptNm")
        memo = st.text_area("메모")
        submitted = st.form_submit_button("단지 저장")

    if submitted:
        if not name.strip():
            st.error("단지명은 필수입니다.")
        else:
            complex_repository.create(
                name=name.strip(),
                sido=sido.strip(),
                sigungu=sigungu.strip(),
                dong=dong.strip(),
                address=address.strip(),
                build_year=build_year or None,
                household_count=None,
                lat=None,
                lng=None,
                molit_lawd_cd=_optional_text(molit_lawd_cd),
                molit_apt_name=_optional_text(molit_apt_name),
                molit_umd_name=_optional_text(molit_umd_name),
                memo=_optional_text(memo),
            )
            st.success("단지를 저장했습니다.")
            st.rerun()


def _render_manage_tab(complex_repository) -> None:
    complexes = complex_repository.list_all()
    if not complexes:
        st.caption("등록된 단지가 없습니다.")
        return

    complex_df = pd.DataFrame(complexes)[
        [
            "id",
            "name",
            "sido",
            "sigungu",
            "dong",
            "address",
            "molit_lawd_cd",
            "molit_apt_name",
            "molit_umd_name",
            "build_year",
            "memo",
            "created_at",
        ]
    ].rename(
        columns={
            "id": "ID",
            "name": "단지명",
            "sido": "시도",
            "sigungu": "시군구",
            "dong": "동",
            "address": "주소",
            "molit_lawd_cd": "MOLIT LAWD_CD",
            "molit_apt_name": "MOLIT aptNm",
            "molit_umd_name": "MOLIT umdNm",
            "build_year": "준공연도",
            "memo": "메모",
            "created_at": "등록일시",
        }
    )
    st.dataframe(complex_df, use_container_width=True)
    options = {f"#{item['id']} | {item['name']} | {item['sigungu'] or '-'}": item for item in complexes}
    selected_label = st.selectbox(
        "수정할 단지 선택",
        list(options.keys()),
    )
    selected = options[selected_label]

    with st.form("update_complex_form"):
        name = st.text_input("단지명*", value=selected["name"])
        col1, col2 = st.columns(2)
        with col1:
            sido = st.text_input("시도", value=selected["sido"] or "")
            sigungu = st.text_input("시군구", value=selected["sigungu"] or "")
        with col2:
            dong = st.text_input("동", value=selected["dong"] or "")
            build_year = st.number_input(
                "준공연도",
                min_value=0,
                step=1,
                value=int(selected["build_year"] or 0),
            )
        address = st.text_input("주소", value=selected["address"] or "")
        st.caption("MOLIT 매핑 (선택 입력)")
        molit_col1, molit_col2 = st.columns(2)
        with molit_col1:
            molit_lawd_cd = st.text_input(
                "MOLIT LAWD_CD",
                value=selected.get("molit_lawd_cd") or "",
            )
            molit_umd_name = st.text_input(
                "MOLIT umdNm",
                value=selected.get("molit_umd_name") or "",
            )
        with molit_col2:
            molit_apt_name = st.text_input(
                "MOLIT aptNm",
                value=selected.get("molit_apt_name") or "",
            )
        memo = st.text_area("메모", value=selected.get("memo") or "")
        col_update, col_delete = st.columns(2)
        update_clicked = col_update.form_submit_button("수정")
        delete_clicked = col_delete.form_submit_button("삭제")

    if update_clicked:
        complex_repository.update(
            selected["id"],
            name=name.strip(),
            sido=sido.strip(),
            sigungu=sigungu.strip(),
            dong=dong.strip(),
            address=address.strip(),
            build_year=build_year or None,
            household_count=selected.get("household_count"),
            lat=selected.get("lat"),
            lng=selected.get("lng"),
            molit_lawd_cd=_optional_text(molit_lawd_cd),
            molit_apt_name=_optional_text(molit_apt_name),
            molit_umd_name=_optional_text(molit_umd_name),
            complex_grade=selected.get("complex_grade"),
            memo=_optional_text(memo),
        )
        st.success("단지 정보를 수정했습니다.")
        st.rerun()

    if delete_clicked:
        complex_repository.delete(selected["id"])
        st.warning("단지를 삭제했습니다.")
        st.rerun()


def _format_candidate_option_label(*, index: int, candidate: dict) -> str:
    return (
        f"[{index + 1}] "
        f"{candidate.get('apt_name') or '-'} | "
        f"{candidate.get('sido') or '-'} "
        f"{candidate.get('sigungu') or '-'} "
        f"{candidate.get('dong') or '-'} | "
        f"{_format_deal_date(candidate)} | "
        f"{_format_price(candidate.get('price'))}"
    )


def _format_deal_date(candidate: dict) -> str:
    year = int(candidate.get("deal_year") or 0)
    month = int(candidate.get("deal_month") or 0)
    day = int(candidate.get("deal_day") or 0)
    if year and month and day:
        return f"{year:04d}-{month:02d}-{day:02d}"
    return "-"


def _format_area(value: object) -> str:
    if value in (None, ""):
        return "-"
    return f"{float(value):.2f}㎡"


def _format_price(value: object) -> str:
    if value in (None, ""):
        return "-"
    return f"{int(value):,}"


def _optional_text(value: str) -> str | None:
    stripped = value.strip()
    return stripped or None
