from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.utils.money_utils import format_compact_won


def render_dashboard_page(
    *,
    complex_repository,
    listing_repository,
    finance_repository,
    analysis_repository,
    policy_event_service,
) -> None:
    st.title("Estate Pulse Dashboard")
    st.caption("Recent analysis snapshots and high-impact policy references.")

    complexes = complex_repository.list_all()
    listings = listing_repository.list_all()
    profiles = finance_repository.list_all()
    analyses = analysis_repository.list_recent(limit=10)

    cols = st.columns(4)
    cols[0].metric("Complexes", len(complexes))
    cols[1].metric("Listings", len(listings))
    cols[2].metric("Profiles", len(profiles))
    cols[3].metric("Recent Analyses", len(analyses))

    if analyses:
        st.subheader("Recent Analysis Results")
        analysis_df = pd.DataFrame(analyses)[
            [
                "complex_name",
                "sale_price",
                "required_cash",
                "shortage_cash",
                "bargain_score",
                "liquidity_score",
                "investment_score",
                "complex_grade",
                "created_at",
            ]
        ].rename(
            columns={
                "complex_name": "Complex",
                "sale_price": "Sale Price",
                "required_cash": "Required Cash",
                "shortage_cash": "Shortage",
                "bargain_score": "Bargain Score",
                "liquidity_score": "Liquidity",
                "investment_score": "Investment Score",
                "complex_grade": "Grade",
                "created_at": "Created At",
            }
        )
        for column in ["Sale Price", "Required Cash", "Shortage"]:
            analysis_df[column] = analysis_df[column].map(format_compact_won)
        analysis_df["Grade"] = analysis_df["Grade"].map(_complex_grade_label)
        st.dataframe(analysis_df, use_container_width=True, hide_index=True)

        top_investment_df = pd.DataFrame(analyses).sort_values(
            by="investment_score",
            ascending=False,
        ).head(5)
        st.subheader("Top Investment Scores")
        top_view_df = top_investment_df[
            [
                "complex_name",
                "investment_score",
                "liquidity_score",
                "bargain_score",
                "required_cash",
                "complex_grade",
            ]
        ].rename(
            columns={
                "complex_name": "Complex",
                "investment_score": "Investment Score",
                "liquidity_score": "Liquidity",
                "bargain_score": "Bargain Score",
                "required_cash": "Required Cash",
                "complex_grade": "Grade",
            }
        )
        top_view_df["Required Cash"] = top_view_df["Required Cash"].map(format_compact_won)
        top_view_df["Grade"] = top_view_df["Grade"].map(_complex_grade_label)
        st.dataframe(top_view_df, use_container_width=True, hide_index=True)
    else:
        st.info("No saved analyses yet.")

    policy_events = policy_event_service.list_high_impact_events()
    st.subheader("Policy Events")
    if not policy_events:
        st.caption("No active or future high-impact policy events.")
        return

    event_df = pd.DataFrame(policy_events)[
        [
            "effective_from",
            "effective_to",
            "policy_type",
            "title",
            "impact_level",
            "status",
            "reference_mode",
            "source_name",
        ]
    ].rename(
        columns={
            "effective_from": "Effective From",
            "effective_to": "Effective To",
            "policy_type": "Type",
            "title": "Title",
            "impact_level": "Impact",
            "status": "Status",
            "reference_mode": "Mode",
            "source_name": "Source",
        }
    )
    st.dataframe(event_df, use_container_width=True, hide_index=True)


def _complex_grade_label(value: str | None) -> str:
    labels = {
        "LEADER": "Leader",
        "SUB_LEADER": "Sub Leader",
        "NORMAL": "Normal",
        "SMALL": "Small",
        "RISKY": "Risky",
    }
    return labels.get(value or "", value or "-")
