from __future__ import annotations

import pandas as pd
import streamlit as st


def render_complex_page(complex_repository) -> None:
    st.title("단지 등록")
    st.caption("처음에는 찾기 쉬운 정보만 입력하면 됩니다.")

    create_tab, manage_tab = st.tabs(["등록", "관리"])

    with create_tab:
        with st.form("create_complex_form"):
            name = st.text_input("단지명 *")
            col1, col2 = st.columns(2)
            with col1:
                sido = st.text_input("시/도")
                sigungu = st.text_input("시/군/구")
            with col2:
                dong = st.text_input("동")
                build_year = st.number_input("준공연도", min_value=0, step=1, value=0)
            address = st.text_input("주소")
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
                    memo=memo.strip() or None,
                )
                st.success("단지를 저장했습니다.")
                st.rerun()

    with manage_tab:
        complexes = complex_repository.list_all()
        if not complexes:
            st.caption("등록된 단지가 없습니다.")
            return

        complex_df = pd.DataFrame(complexes)[
            ["id", "name", "sido", "sigungu", "dong", "address", "build_year", "memo", "created_at"]
        ].rename(
            columns={
                "id": "ID",
                "name": "단지명",
                "sido": "시/도",
                "sigungu": "시/군/구",
                "dong": "동",
                "address": "주소",
                "build_year": "준공연도",
                "memo": "메모",
                "created_at": "등록일시",
            }
        )
        st.dataframe(complex_df, use_container_width=True)
        options = {
            f"#{item['id']} | {item['name']} | {item['sigungu'] or '-'}": item for item in complexes
        }
        selected_label = st.selectbox("수정할 단지 선택", list(options.keys()))
        selected = options[selected_label]

        with st.form("update_complex_form"):
            name = st.text_input("단지명 *", value=selected["name"])
            col1, col2 = st.columns(2)
            with col1:
                sido = st.text_input("시/도", value=selected["sido"] or "")
                sigungu = st.text_input("시/군/구", value=selected["sigungu"] or "")
            with col2:
                dong = st.text_input("동", value=selected["dong"] or "")
                build_year = st.number_input(
                    "준공연도",
                    min_value=0,
                    step=1,
                    value=int(selected["build_year"] or 0),
                )
            address = st.text_input("주소", value=selected["address"] or "")
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
                memo=memo.strip() or None,
            )
            st.success("단지 정보를 수정했습니다.")
            st.rerun()

        if delete_clicked:
            complex_repository.delete(selected["id"])
            st.warning("단지를 삭제했습니다.")
            st.rerun()
