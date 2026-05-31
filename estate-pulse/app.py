from __future__ import annotations

import streamlit as st

from config.settings import get_settings
from modules.repositories.analysis_repository import AnalysisRepository
from modules.repositories.complex_repository import ApartmentComplexRepository
from modules.repositories.database import initialize_database
from modules.repositories.finance_profile_repository import UserFinanceProfileRepository
from modules.repositories.listing_repository import ManualListingRepository
from modules.repositories.policy_import_repository import PolicyImportRepository
from modules.repositories.region_policy_repository import RegionPolicyRepository
from modules.repositories.rent_transaction_repository import RentTransactionRepository
from modules.repositories.rule_candidate_repository import RuleCandidateRepository
from modules.repositories.sale_transaction_repository import SaleTransactionRepository
from modules.repositories.watchlist_repository import WatchlistRepository
from modules.services.analysis_service import AnalysisService
from modules.services.market_scoring_service import MarketScoringService
from modules.services.opportunity_service import OpportunityService
from modules.services.policy_import_service import PolicyImportService
from modules.services.region_policy_service import RegionPolicyService
from modules.services.rule_admin_service import RuleAdminService
from modules.services.rule_runtime_service import RuleRuntimeService
from modules.ui.admin_view import render_admin_page
from modules.ui.analysis_view import render_analysis_page
from modules.ui.comparison_view import render_comparison_page
from modules.ui.complex_form import render_complex_page
from modules.ui.dashboard import render_dashboard_page
from modules.ui.finance_profile_form import render_finance_profile_page
from modules.ui.listing_form import render_listing_page
from modules.ui.ranking_view import render_ranking_page
from modules.ui.watchlist_view import render_watchlist_page


def main() -> None:
    settings = get_settings()
    initialize_database(settings.database_path)

    st.set_page_config(
        page_title=settings.app_name,
        layout="wide",
    )

    complex_repository = ApartmentComplexRepository(settings.database_path)
    listing_repository = ManualListingRepository(settings.database_path)
    finance_repository = UserFinanceProfileRepository(settings.database_path)
    analysis_repository = AnalysisRepository(settings.database_path)
    sale_transaction_repository = SaleTransactionRepository(settings.database_path)
    rent_transaction_repository = RentTransactionRepository(settings.database_path)
    watchlist_repository = WatchlistRepository(settings.database_path)
    policy_import_repository = PolicyImportRepository(settings.database_path)
    rule_candidate_repository = RuleCandidateRepository(settings.database_path)
    region_policy_repository = RegionPolicyRepository(settings.database_path)
    rule_runtime_service = RuleRuntimeService(
        rule_candidate_repository=rule_candidate_repository,
    )
    region_policy_service = RegionPolicyService(
        region_policy_repository=region_policy_repository,
    )
    market_scoring_service = MarketScoringService(
        complex_repository=complex_repository,
        sale_transaction_repository=sale_transaction_repository,
        rent_transaction_repository=rent_transaction_repository,
    )
    analysis_service = AnalysisService(
        settings=settings,
        listing_repository=listing_repository,
        finance_repository=finance_repository,
        analysis_repository=analysis_repository,
        sale_transaction_repository=sale_transaction_repository,
        rent_transaction_repository=rent_transaction_repository,
        market_scoring_service=market_scoring_service,
        rule_runtime_service=rule_runtime_service,
        complex_repository=complex_repository,
        region_policy_service=region_policy_service,
    )
    opportunity_service = OpportunityService(
        listing_repository=listing_repository,
        analysis_repository=analysis_repository,
        watchlist_repository=watchlist_repository,
        analysis_service=analysis_service,
    )
    rule_admin_service = RuleAdminService(
        rule_runtime_service=rule_runtime_service,
        region_policy_service=region_policy_service,
    )
    policy_import_service = PolicyImportService(
        policy_import_repository=policy_import_repository,
        rule_candidate_repository=rule_candidate_repository,
        rule_runtime_service=rule_runtime_service,
        region_policy_service=region_policy_service,
    )

    pages = {
        "Dashboard": lambda: render_dashboard_page(
            complex_repository=complex_repository,
            listing_repository=listing_repository,
            finance_repository=finance_repository,
            analysis_repository=analysis_repository,
        ),
        "Complex": lambda: render_complex_page(complex_repository),
        "Listing": lambda: render_listing_page(
            complex_repository=complex_repository,
            listing_repository=listing_repository,
        ),
        "Finance": lambda: render_finance_profile_page(finance_repository),
        "Analysis": lambda: render_analysis_page(
            complex_repository=complex_repository,
            listing_repository=listing_repository,
            finance_repository=finance_repository,
            analysis_repository=analysis_repository,
            analysis_service=analysis_service,
            settings=settings,
        ),
        "Watchlist": lambda: render_watchlist_page(
            complex_repository=complex_repository,
            listing_repository=listing_repository,
            finance_repository=finance_repository,
            watchlist_repository=watchlist_repository,
            opportunity_service=opportunity_service,
        ),
        "Comparison": lambda: render_comparison_page(
            listing_repository=listing_repository,
            finance_repository=finance_repository,
            opportunity_service=opportunity_service,
        ),
        "Ranking": lambda: render_ranking_page(
            finance_repository=finance_repository,
            opportunity_service=opportunity_service,
        ),
        "관리자": lambda: render_admin_page(
            rule_admin_service=rule_admin_service,
            policy_import_service=policy_import_service,
            complex_repository=complex_repository,
        ),
    }

    st.sidebar.title(settings.app_name)
    selected_page = st.sidebar.radio("Menu", list(pages.keys()))
    st.sidebar.caption("Phase 2 comparison platform")
    pages[selected_page]()


if __name__ == "__main__":
    main()
