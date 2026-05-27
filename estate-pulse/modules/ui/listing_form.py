from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.utils.date_utils import parse_date_or_today


def render_listing_page(*, complex_repository, listing_repository) -> None:
    st.title("매물 입력")

    complexes = complex_repository.list_all()
    if not complexes:
        st.info("먼저 단지를 등록해 주세요.")
        return

    create_tab, manage_tab = st.tabs(["등록", "관리"])
    complex_options = {f"#{item['id']} | {item['name']}": item["id"] for item in complexes}

    with create_tab:
        with st.form("create_listing_form"):
            complex_label = st.selectbox("단지 선택 *", list(complex_options.keys()))
            area_m2 = st.number_input("전용면적 (m²) *", min_value=0.0, step=1.0, value=84.0)
            sale_price = st.number_input("매물가 *", min_value=0, step=1000000, value=0)
            expected_jeonse_price = st.number_input(
                "예상 전세가",
                min_value=0,
                step=1000000,
                value=0,
            )
            floor = st.text_input("층")
            direction = st.text_input("향")
            condition_memo = st.text_area("상태 메모")
            source_memo = st.text_area("출처 메모")
            checked_at = st.date_input("확인일")
            submitted = st.form_submit_button("매물 저장")

        if submitted:
            if sale_price <= 0:
                st.error("매물가는 필수입니다.")
            else:
                listing_repository.create(
                    complex_id=complex_options[complex_label],
                    area_m2=float(area_m2),
                    sale_price=int(sale_price),
                    expected_jeonse_price=int(expected_jeonse_price),
                    floor=floor.strip(),
                    direction=direction.strip(),
                    condition_memo=condition_memo.strip(),
                    source_memo=source_memo.strip(),
                    checked_at=checked_at.isoformat(),
                )
                st.success("매물을 저장했습니다.")
                st.rerun()

    with manage_tab:
        listings = listing_repository.list_all()
        if not listings:
            st.caption("등록된 매물이 없습니다.")
            return

        listing_df = pd.DataFrame(listings)[
            [
                "id",
                "complex_name",
                "area_m2",
                "sale_price",
                "expected_jeonse_price",
                "floor",
                "direction",
                "checked_at",
                "created_at",
            ]
        ].rename(
            columns={
                "id": "ID",
                "complex_name": "단지명",
                "area_m2": "전용면적(m²)",
                "sale_price": "매물가",
                "expected_jeonse_price": "예상 전세가",
                "floor": "층",
                "direction": "향",
                "checked_at": "확인일",
                "created_at": "등록일시",
            }
        )
        st.dataframe(listing_df, use_container_width=True)
        options = {
            f"#{item['id']} | {item['complex_name']} | {item['sale_price']:,}": item for item in listings
        }
        selected_label = st.selectbox("수정할 매물 선택", list(options.keys()))
        selected = options[selected_label]

        matching_complex_label = next(
            label for label, complex_id in complex_options.items() if complex_id == selected["complex_id"]
        )

        with st.form("update_listing_form"):
            complex_label = st.selectbox(
                "단지 선택 *",
                list(complex_options.keys()),
                index=list(complex_options.keys()).index(matching_complex_label),
            )
            area_m2 = st.number_input(
                "전용면적 (m²) *",
                min_value=0.0,
                step=1.0,
                value=float(selected["area_m2"]),
            )
            sale_price = st.number_input(
                "매물가 *",
                min_value=0,
                step=1000000,
                value=int(selected["sale_price"]),
            )
            expected_jeonse_price = st.number_input(
                "예상 전세가",
                min_value=0,
                step=1000000,
                value=int(selected["expected_jeonse_price"] or 0),
            )
            floor = st.text_input("층", value=selected["floor"] or "")
            direction = st.text_input("향", value=selected["direction"] or "")
            condition_memo = st.text_area("상태 메모", value=selected["condition_memo"] or "")
            source_memo = st.text_area("출처 메모", value=selected["source_memo"] or "")
            checked_at = st.date_input(
                "확인일",
                value=parse_date_or_today(selected["checked_at"]),
            )
            col_update, col_delete = st.columns(2)
            update_clicked = col_update.form_submit_button("수정")
            delete_clicked = col_delete.form_submit_button("삭제")

        if update_clicked:
            listing_repository.update(
                selected["id"],
                complex_id=complex_options[complex_label],
                area_m2=float(area_m2),
                sale_price=int(sale_price),
                expected_jeonse_price=int(expected_jeonse_price),
                floor=floor.strip(),
                direction=direction.strip(),
                condition_memo=condition_memo.strip(),
                source_memo=source_memo.strip(),
                checked_at=checked_at.isoformat(),
            )
            st.success("매물 정보를 수정했습니다.")
            st.rerun()

        if delete_clicked:
            listing_repository.delete(selected["id"])
            st.warning("매물을 삭제했습니다.")
            st.rerun()
