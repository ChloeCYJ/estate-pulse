from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.utils.money_utils import format_compact_won


def render_watchlist_page(
    *,
    complex_repository,
    listing_repository,
    finance_repository,
    watchlist_repository,
    opportunity_service,
    policy_event_service,
) -> None:
    st.title("Watchlist")
    st.caption("Track selected complexes and listings with current finance assumptions.")

    profiles = finance_repository.list_all()
    complexes = complex_repository.list_all()
    listings = listing_repository.list_all()

    if not profiles:
        st.info("Create a finance profile first.")
        return

    profile_options = {_profile_label(item): item["id"] for item in profiles}
    selected_profile_id = profile_options[st.selectbox("Finance Profile", list(profile_options.keys()))]

    add_complex_col, add_listing_col = st.columns(2)
    with add_complex_col:
        st.subheader("Add Complex")
        if complexes:
            complex_options = {f"#{item['id']} | {item['name']}": int(item["id"]) for item in complexes}
            selected_complex = st.selectbox("Complex", list(complex_options.keys()), key="watchlist_complex")
            if st.button("Add Complex", use_container_width=True):
                watchlist_repository.add_complex(complex_options[selected_complex])
                st.success("Complex added to watchlist.")
        else:
            st.caption("No complexes available.")

    with add_listing_col:
        st.subheader("Add Listing")
        if listings:
            listing_options = {
                f"#{item['id']} | {item['complex_name']} | {format_compact_won(item['sale_price'])}": int(item["id"])
                for item in listings
            }
            selected_listing = st.selectbox("Listing", list(listing_options.keys()), key="watchlist_listing")
            if st.button("Add Listing", use_container_width=True):
                watchlist_repository.add_listing(listing_options[selected_listing])
                st.success("Listing added to watchlist.")
        else:
            st.caption("No listings available.")

    st.divider()
    st.subheader("Watchlist")
    rows = opportunity_service.build_watchlist(finance_profile_id=selected_profile_id)
    if rows:
        display_df = pd.DataFrame(rows)[
            [
                "watchlist_id",
                "watch_target",
                "summary_basis",
                "representative_listing_id",
                "complex_listing_count",
                "analysis_status",
                "complex_name",
                "sale_price",
                "required_cash",
                "shortage_cash",
                "bargain_score",
                "jeonse_ratio",
                "relevant_policy_event_count",
                "relevant_policy_event_titles",
                "complex_grade_label",
                "liquidity_score",
                "investment_score",
                "latest_analysis_date",
            ]
        ].rename(
            columns={
                "watchlist_id": "ID",
                "watch_target": "Target Type",
                "summary_basis": "Summary Basis",
                "representative_listing_id": "Representative Listing",
                "complex_listing_count": "Complex Listing Count",
                "analysis_status": "Analysis Status",
                "complex_name": "Complex",
                "sale_price": "Sale Price",
                "required_cash": "Required Cash",
                "shortage_cash": "Shortage",
                "bargain_score": "Bargain Score",
                "jeonse_ratio": "Jeonse Ratio",
                "relevant_policy_event_count": "Policy Event Count",
                "relevant_policy_event_titles": "Policy Event Titles",
                "complex_grade_label": "Grade",
                "liquidity_score": "Liquidity",
                "investment_score": "Investment Score",
                "latest_analysis_date": "Latest Analysis",
            }
        )
        for column in ["Sale Price", "Required Cash", "Shortage"]:
            display_df[column] = display_df[column].map(_format_money_or_dash)
        display_df["Jeonse Ratio"] = display_df["Jeonse Ratio"].map(_format_percent_or_dash)
        display_df["Representative Listing"] = display_df["Representative Listing"].map(
            _format_int_or_dash
        )
        display_df["Complex Listing Count"] = display_df["Complex Listing Count"].map(
            _format_int_or_dash
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        removable_options = {
            f"#{item['watchlist_id']} | {item['complex_name']} | {item.get('watch_target', '-')}": int(
                item["watchlist_id"]
            )
            for item in rows
        }
        selected_remove = st.selectbox("Remove Item", list(removable_options.keys()))
        if st.button("Remove from Watchlist", type="secondary"):
            watchlist_repository.delete(removable_options[selected_remove])
            st.success("Item removed from watchlist.")
    else:
        st.info("Watchlist is empty.")

    relevant_events = policy_event_service.list_high_impact_events()
    st.divider()
    st.subheader("Relevant Policy Events")
    if not relevant_events:
        st.caption("No active or future high-impact policy events.")
        return

    event_df = pd.DataFrame(relevant_events)[
        [
            "effective_from",
            "effective_to",
            "policy_type",
            "title",
            "impact_level",
            "status",
            "reference_mode",
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
        }
    )
    st.dataframe(event_df, use_container_width=True, hide_index=True)


def _profile_label(profile: dict) -> str:
    return f"#{profile['id']} | Cash {format_compact_won(profile['cash_amount'])}"


def _format_money_or_dash(value: int | float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return format_compact_won(value)


def _format_percent_or_dash(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.1f}%"


def _format_int_or_dash(value: int | float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return str(int(value))
