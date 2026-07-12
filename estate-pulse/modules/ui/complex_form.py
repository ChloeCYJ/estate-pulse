from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.collectors.juso_address_client import (
    JusoAddressApiBusinessError,
    JusoAddressApiConfigurationError,
    JusoAddressApiConnectionError,
)
from modules.services.complex_registration_service import (
    ComplexAlreadyExistsError,
    LawdCodeMappingError,
)


JUSO_SEARCH_INPUT_KEY = "juso_search_keyword_input"
JUSO_SEARCH_RESULTS_KEY = "juso_search_results"
JUSO_SEARCH_KEYWORD_KEY = "juso_search_keyword"
JUSO_PREVIEW_KEY = "juso_registration_preview"
JUSO_CANDIDATE_SELECTBOX_KEY = "juso_candidate_selectbox"
JUSO_PLACEHOLDER_OPTION = "선택하세요"
MANAGE_SELECT_COLUMN = "선택"


def render_complex_page(
    complex_repository,
    *,
    address_search_service=None,
    complex_registration_service=None,
) -> None:
    st.title("단지 등록")
    st.caption(
        "사용자는 아파트명만 검색하고, 주소/법정동/LAWD_CD는 주소 후보와 "
        "법정동코드 기준으로 자동 매핑합니다."
    )

    create_tab, manage_tab = st.tabs(["등록", "관리"])

    with create_tab:
        _render_juso_address_registration(
            address_search_service=address_search_service,
            complex_registration_service=complex_registration_service,
        )
        st.divider()
        with st.expander("기존 직접 입력 등록", expanded=False):
            _render_manual_create_form(complex_repository)

    with manage_tab:
        _render_manage_tab(complex_repository)


def _render_juso_address_registration(
    *,
    address_search_service,
    complex_registration_service,
) -> None:
    st.subheader("행정안전부 아파트 검색")
    st.caption("검색 버튼을 눌렀을 때만 주소 API를 호출하고, 선택한 후보 기준으로 단지를 등록합니다.")

    has_service_key = _has_juso_service_key(address_search_service)
    if not has_service_key:
        st.warning("JUSO_API_KEY가 설정되지 않아 주소 검색 기능을 사용할 수 없습니다.")

    with st.form("juso_address_search_form"):
        keyword = st.text_input("아파트명 검색", key=JUSO_SEARCH_INPUT_KEY)
        search_clicked = st.form_submit_button("검색", disabled=not has_service_key)

    _reset_search_state_if_keyword_changed(
        st.session_state,
        current_keyword=keyword,
        search_clicked=search_clicked,
    )

    if search_clicked:
        _clear_registration_preview(st.session_state)
        try:
            candidates = _search_address_candidates_cached(
                keyword=keyword.strip(),
                page=1,
                _address_search_service=address_search_service,
            )
        except JusoAddressApiConfigurationError:
            _clear_search_state(st.session_state)
            st.error("JUSO_API_KEY가 설정되지 않아 주소 검색을 사용할 수 없습니다.")
        except JusoAddressApiConnectionError:
            _clear_search_state(st.session_state)
            st.error("주소 API 연결에 실패했습니다. 잠시 후 다시 시도해 주세요.")
        except JusoAddressApiBusinessError as exc:
            _clear_search_state(st.session_state)
            st.error(f"주소 API 업무 오류: {exc}")
        except ValueError as exc:
            _clear_search_state(st.session_state)
            st.error(str(exc))
        else:
            st.session_state[JUSO_SEARCH_KEYWORD_KEY] = keyword.strip()
            st.session_state[JUSO_SEARCH_RESULTS_KEY] = candidates
            if not candidates:
                raw_count = int(getattr(address_search_service, "last_raw_result_count", 0) or 0)
                if raw_count <= 0:
                    st.info("검색 결과가 없습니다.")
                else:
                    st.info("서울·경기·인천 공동주택 후보가 없습니다.")

    candidates = st.session_state.get(JUSO_SEARCH_RESULTS_KEY, [])
    if not candidates:
        return

    st.caption(f"검색 결과 {len(candidates)}건")
    selected_label = st.selectbox(
        "후보 선택",
        _candidate_selectbox_options(candidates),
        index=0,
        key=JUSO_CANDIDATE_SELECTBOX_KEY,
    )
    selected_candidate = _candidate_from_label(selected_label, candidates)
    if selected_candidate is None:
        return

    try:
        preview = complex_registration_service.prepare_registration(candidate=selected_candidate)
    except LawdCodeMappingError as exc:
        _clear_registration_preview(st.session_state)
        st.error(_registration_error_message(exc))
        preview = None
    except ValueError as exc:
        _clear_registration_preview(st.session_state)
        st.error(str(exc))
        preview = None
    else:
        st.session_state[JUSO_PREVIEW_KEY] = preview

    _render_selected_candidate(selected_candidate)
    if preview is not None:
        _render_registration_preview(preview)

    with st.form("juso_complex_register_form"):
        memo = st.text_input("등록 메모 (선택)", key="juso_register_memo")
        register_clicked = st.form_submit_button("단지 등록", disabled=preview is None)

    if register_clicked:
        try:
            complex_id = complex_registration_service.register_candidate(
                candidate=selected_candidate,
                memo=_optional_text(memo),
            )
        except ComplexAlreadyExistsError:
            st.error("기존 단지가 이미 존재합니다.")
        except LawdCodeMappingError as exc:
            st.error(_registration_error_message(exc))
        except ValueError as exc:
            st.error(str(exc))
        else:
            _clear_search_state(st.session_state)
            _clear_registration_preview(st.session_state)
            st.success(f"단지를 등록했습니다. complex_id={complex_id}")
            st.rerun()


@st.cache_data(ttl=86400, show_spinner=False)
def _search_address_candidates_cached(
    *,
    keyword: str,
    page: int,
    _address_search_service,
):
    return _address_search_service.search_candidates(keyword=keyword, current_page=page)


def _has_juso_service_key(address_search_service) -> bool:
    client = getattr(address_search_service, "juso_address_client", None)
    return bool(getattr(client, "service_key", None))


def _candidate_selectbox_options(candidates: list) -> list[str]:
    return [JUSO_PLACEHOLDER_OPTION, *_candidate_labels(candidates)]


def _candidate_from_label(selected_label: str, candidates: list):
    if selected_label == JUSO_PLACEHOLDER_OPTION:
        return None
    for candidate, label in zip(candidates, _candidate_labels(candidates)):
        if label == selected_label:
            return candidate
    return None


def _candidate_labels(candidates: list) -> list[str]:
    base_labels = [_format_candidate_label(candidate) for candidate in candidates]
    label_counts: dict[str, int] = {}
    for label in base_labels:
        label_counts[label] = label_counts.get(label, 0) + 1

    labels: list[str] = []
    for candidate, base_label in zip(candidates, base_labels):
        if label_counts.get(base_label, 0) > 1 and candidate.road_address:
            labels.append(f"{base_label} | {candidate.road_address}")
        else:
            labels.append(base_label)
    return labels


def _format_candidate_label(candidate) -> str:
    dong_name = candidate.li or candidate.emd
    return f"{candidate.complex_name} | {candidate.sido} {candidate.sigungu} {dong_name}"


def _render_selected_candidate(candidate) -> None:
    st.caption("선택한 주소 후보")
    preview_cols = st.columns(2)
    preview_cols[0].text_input(
        "단지명",
        value=candidate.complex_name,
        disabled=True,
        key="juso_selected_complex_name",
    )
    preview_cols[1].text_input(
        "시도 / 시군구",
        value=f"{candidate.sido} {candidate.sigungu}",
        disabled=True,
        key="juso_selected_region",
    )
    st.text_input(
        "도로명주소",
        value=candidate.road_address,
        disabled=True,
        key="juso_selected_road_address",
    )
    st.text_input(
        "지번주소",
        value=candidate.jibun_address,
        disabled=True,
        key="juso_selected_jibun_address",
    )


def _render_registration_preview(preview: dict) -> None:
    st.caption("자동 매핑 결과")
    preview_cols = st.columns(2)
    preview_cols[0].text_input(
        "단지명",
        value=preview["name"],
        disabled=True,
        key="juso_preview_complex_name",
    )
    preview_cols[1].text_input(
        "LAWD_CD",
        value=preview["lawd_cd"],
        disabled=True,
        key="juso_preview_lawd_cd",
    )
    st.text_input(
        "법정동 기준 주소",
        value=f"{preview['sido']} {preview['sigungu']} {preview['dong']}",
        disabled=True,
        key="juso_preview_region_address",
    )
    st.text_input(
        "대표 주소",
        value=preview["address"],
        disabled=True,
        key="juso_preview_full_address",
    )


def _registration_error_message(exc: LawdCodeMappingError) -> str:
    message = str(exc)
    if "multiple lawd code matches" in message:
        return "법정동코드 매핑 결과가 복수건이라 자동 등록을 중단했습니다."
    if "admCd prefix mismatch" in message:
        return "주소 API admCd와 LAWD_CD가 일치하지 않아 자동 등록을 중단했습니다."
    return "법정동코드 매핑에 실패했습니다."


def _reset_search_state_if_keyword_changed(session_state, *, current_keyword: str, search_clicked: bool) -> None:
    previous_keyword = str(session_state.get(JUSO_SEARCH_KEYWORD_KEY) or "").strip()
    normalized_current = str(current_keyword or "").strip()
    if search_clicked:
        return
    if previous_keyword and normalized_current != previous_keyword:
        _clear_search_state(session_state)
        _clear_registration_preview(session_state)


def _clear_search_state(session_state) -> None:
    session_state.pop(JUSO_SEARCH_RESULTS_KEY, None)
    session_state.pop(JUSO_SEARCH_KEYWORD_KEY, None)
    session_state.pop(JUSO_CANDIDATE_SELECTBOX_KEY, None)


def _clear_registration_preview(session_state) -> None:
    session_state.pop(JUSO_PREVIEW_KEY, None)


def _render_manual_create_form(complex_repository) -> None:
    st.caption("검색 결과가 없거나 자동 매핑이 실패하면 기존 직접 입력 등록을 사용할 수 있습니다.")
    with st.form("create_complex_form"):
        name = st.text_input("단지명")
        col1, col2 = st.columns(2)
        with col1:
            sido = st.text_input("시도")
            sigungu = st.text_input("시군구")
        with col2:
            dong = st.text_input("동")
            build_year = st.number_input("준공연도", min_value=0, step=1, value=0)
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
            return

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

    complex_df = pd.DataFrame(_manage_complex_editor_rows(complexes))
    edited_complex_df = st.data_editor(
        complex_df,
        use_container_width=True,
        hide_index=True,
        key="manage_complex_editor",
        disabled=[column for column in complex_df.columns if column != MANAGE_SELECT_COLUMN],
        column_config={
            MANAGE_SELECT_COLUMN: st.column_config.CheckboxColumn(
                MANAGE_SELECT_COLUMN,
                help="수정 또는 삭제할 단지 1개만 선택하세요.",
                default=False,
            )
        },
    )
    selected_complexes = _selected_manage_complexes(
        edited_complex_df.to_dict("records"),
        complexes,
    )
    selected_count = len(selected_complexes)
    if selected_count == 0:
        st.caption("표에서 수정 또는 삭제할 단지를 1개 이상 체크하세요.")
        return

    with st.form("delete_complex_form"):
        delete_confirmed = st.checkbox(
            f"선택한 단지 {selected_count}건을 확인 후 삭제",
            key=f"delete_complex_confirm_{selected_count}",
        )
        delete_clicked = st.form_submit_button(f"선택 단지 {selected_count}건 삭제")

    if delete_clicked:
        if not delete_confirmed:
            st.error("삭제 전에 확인 체크박스를 선택하세요.")
            return
        for item in selected_complexes:
            complex_repository.delete(item["id"])
        st.warning(f"단지 {selected_count}건을 삭제했습니다.")
        st.rerun()

    if selected_count != 1:
        st.info("수정은 1건만 선택했을 때 가능합니다.")
        return

    selected = selected_complexes[0]

    with st.form("update_complex_form"):
        name = st.text_input("단지명", value=selected["name"])
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
            molit_lawd_cd = st.text_input("MOLIT LAWD_CD", value=selected.get("molit_lawd_cd") or "")
            molit_umd_name = st.text_input("MOLIT umdNm", value=selected.get("molit_umd_name") or "")
        with molit_col2:
            molit_apt_name = st.text_input("MOLIT aptNm", value=selected.get("molit_apt_name") or "")
        memo = st.text_area("메모", value=selected.get("memo") or "")
        update_clicked = st.form_submit_button("수정")

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

def _manage_complex_editor_rows(complexes: list[dict]) -> list[dict]:
    return [
        {
            MANAGE_SELECT_COLUMN: False,
            "ID": item["id"],
            "단지명": item["name"],
            "시도": item["sido"],
            "시군구": item["sigungu"],
            "동": item["dong"],
            "주소": item["address"],
            "MOLIT LAWD_CD": item.get("molit_lawd_cd"),
            "MOLIT aptNm": item.get("molit_apt_name"),
            "MOLIT umdNm": item.get("molit_umd_name"),
            "준공연도": item.get("build_year"),
            "메모": item.get("memo"),
            "등록일시": item.get("created_at"),
        }
        for item in complexes
    ]


def _selected_manage_complexes(rows: list[dict], complexes: list[dict]) -> list[dict]:
    selected_ids = [int(row["ID"]) for row in rows if row.get(MANAGE_SELECT_COLUMN)]
    complex_by_id = {int(item["id"]): item for item in complexes}
    return [complex_by_id[selected_id] for selected_id in selected_ids if selected_id in complex_by_id]


def _selected_manage_complex(rows: list[dict], complexes: list[dict]) -> tuple[dict | None, int]:
    selected_complexes = _selected_manage_complexes(rows, complexes)
    if len(selected_complexes) != 1:
        return None, len(selected_complexes)
    return selected_complexes[0], len(selected_complexes)


def _optional_text(value: str) -> str | None:
    stripped = value.strip()
    return stripped or None
