from __future__ import annotations

import pandas as pd
import streamlit as st


def render_complex_page(complex_repository) -> None:
    st.title("\ub2e8\uc9c0 \ub4f1\ub85d")
    st.caption(
        "\ucc98\uc74c\uc5d0\ub294 \ud575\uc2ec \ub2e8\uc9c0 \uc815\ubcf4\ub9cc \uc785\ub825\ud574\ub3c4 \ub429\ub2c8\ub2e4. "
        "MOLIT \ub9e4\ud551 \uc815\ubcf4\ub294 \ud544\uc694\ud560 \ub54c\ub9cc \ucd94\uac00\ud558\uc138\uc694."
    )

    create_tab, manage_tab = st.tabs(
        [
            "\ub4f1\ub85d",
            "\uad00\ub9ac",
        ]
    )

    with create_tab:
        with st.form("create_complex_form"):
            name = st.text_input("\ub2e8\uc9c0\uba85*")
            col1, col2 = st.columns(2)
            with col1:
                sido = st.text_input("\uc2dc\ub3c4")
                sigungu = st.text_input("\uc2dc\uad70\uad6c")
            with col2:
                dong = st.text_input("\ub3d9")
                build_year = st.number_input(
                    "\uc900\uacf5\uc5f0\ub3c4",
                    min_value=0,
                    step=1,
                    value=0,
                )
            address = st.text_input("\uc8fc\uc18c")
            st.caption("MOLIT \ub9e4\ud551 (\uc120\ud0dd \uc785\ub825)")
            molit_col1, molit_col2 = st.columns(2)
            with molit_col1:
                molit_lawd_cd = st.text_input("MOLIT LAWD_CD")
                molit_umd_name = st.text_input("MOLIT umdNm")
            with molit_col2:
                molit_apt_name = st.text_input("MOLIT aptNm")
            memo = st.text_area("\uba54\ubaa8")
            submitted = st.form_submit_button("\ub2e8\uc9c0 \uc800\uc7a5")

        if submitted:
            if not name.strip():
                st.error("\ub2e8\uc9c0\uba85\uc740 \ud544\uc218\uc785\ub2c8\ub2e4.")
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
                st.success("\ub2e8\uc9c0\ub97c \uc800\uc7a5\ud588\uc2b5\ub2c8\ub2e4.")
                st.rerun()

    with manage_tab:
        complexes = complex_repository.list_all()
        if not complexes:
            st.caption("\ub4f1\ub85d\ub41c \ub2e8\uc9c0\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.")
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
                "name": "\ub2e8\uc9c0\uba85",
                "sido": "\uc2dc\ub3c4",
                "sigungu": "\uc2dc\uad70\uad6c",
                "dong": "\ub3d9",
                "address": "\uc8fc\uc18c",
                "molit_lawd_cd": "MOLIT LAWD_CD",
                "molit_apt_name": "MOLIT aptNm",
                "molit_umd_name": "MOLIT umdNm",
                "build_year": "\uc900\uacf5\uc5f0\ub3c4",
                "memo": "\uba54\ubaa8",
                "created_at": "\ub4f1\ub85d\uc77c\uc2dc",
            }
        )
        st.dataframe(complex_df, use_container_width=True)
        options = {
            f"#{item['id']} | {item['name']} | {item['sigungu'] or '-'}": item for item in complexes
        }
        selected_label = st.selectbox(
            "\uc218\uc815\ud560 \ub2e8\uc9c0 \uc120\ud0dd",
            list(options.keys()),
        )
        selected = options[selected_label]

        with st.form("update_complex_form"):
            name = st.text_input("\ub2e8\uc9c0\uba85*", value=selected["name"])
            col1, col2 = st.columns(2)
            with col1:
                sido = st.text_input("\uc2dc\ub3c4", value=selected["sido"] or "")
                sigungu = st.text_input("\uc2dc\uad70\uad6c", value=selected["sigungu"] or "")
            with col2:
                dong = st.text_input("\ub3d9", value=selected["dong"] or "")
                build_year = st.number_input(
                    "\uc900\uacf5\uc5f0\ub3c4",
                    min_value=0,
                    step=1,
                    value=int(selected["build_year"] or 0),
                )
            address = st.text_input("\uc8fc\uc18c", value=selected["address"] or "")
            st.caption("MOLIT \ub9e4\ud551 (\uc120\ud0dd \uc785\ub825)")
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
            memo = st.text_area("\uba54\ubaa8", value=selected.get("memo") or "")
            col_update, col_delete = st.columns(2)
            update_clicked = col_update.form_submit_button("\uc218\uc815")
            delete_clicked = col_delete.form_submit_button("\uc0ad\uc81c")

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
            st.success("\ub2e8\uc9c0 \uc815\ubcf4\ub97c \uc218\uc815\ud588\uc2b5\ub2c8\ub2e4.")
            st.rerun()

        if delete_clicked:
            complex_repository.delete(selected["id"])
            st.warning("\ub2e8\uc9c0\ub97c \uc0ad\uc81c\ud588\uc2b5\ub2c8\ub2e4.")
            st.rerun()


def _optional_text(value: str) -> str | None:
    stripped = value.strip()
    return stripped or None
