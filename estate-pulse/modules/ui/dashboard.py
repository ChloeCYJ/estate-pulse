from __future__ import annotations

import pandas as pd
import streamlit as st


def render_dashboard_page(
    *,
    complex_repository,
    listing_repository,
    finance_repository,
    analysis_repository,
) -> None:
    st.title("Estate Pulse 대시보드")
    st.caption("로컬 SQLite 기반 Phase 1 진행 현황입니다.")

    complexes = complex_repository.list_all()
    listings = listing_repository.list_all()
    profiles = finance_repository.list_all()
    analyses = analysis_repository.list_recent(limit=10)

    cols = st.columns(4)
    cols[0].metric("단지 수", len(complexes))
    cols[1].metric("매물 수", len(listings))
    cols[2].metric("자금 프로필 수", len(profiles))
    cols[3].metric("저장된 분석 수", len(analyses))

    if analyses:
        st.subheader("최근 분석 결과")
        analysis_df = pd.DataFrame(analyses)[
            ["complex_name", "sale_price", "required_cash", "shortage_cash", "bargain_score", "decision", "created_at"]
        ].rename(
            columns={
                "complex_name": "단지명",
                "sale_price": "매물가",
                "required_cash": "필요 현금",
                "shortage_cash": "부족 현금",
                "bargain_score": "급매 점수",
                "decision": "판정",
                "created_at": "분석일시",
            }
        )
        st.dataframe(
            analysis_df,
            use_container_width=True,
        )
    else:
        st.info("아직 분석 결과가 없습니다. 매물과 자금 프로필을 등록한 뒤 분석을 실행해 주세요.")
