from __future__ import annotations

import streamlit as st

from config.settings import get_settings
from modules.repositories.analysis_repository import AnalysisRepository
from modules.repositories.complex_repository import ApartmentComplexRepository
from modules.repositories.database import initialize_database
from modules.repositories.finance_profile_repository import UserFinanceProfileRepository
from modules.repositories.listing_repository import ManualListingRepository
from modules.repositories.rent_transaction_repository import RentTransactionRepository
from modules.repositories.sale_transaction_repository import SaleTransactionRepository
from modules.services.analysis_service import AnalysisService
from modules.ui.analysis_view import render_analysis_page
from modules.ui.complex_form import render_complex_page
from modules.ui.dashboard import render_dashboard_page
from modules.ui.finance_profile_form import render_finance_profile_page
from modules.ui.listing_form import render_listing_page


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
    analysis_service = AnalysisService(
        settings=settings,
        listing_repository=listing_repository,
        finance_repository=finance_repository,
        analysis_repository=analysis_repository,
        sale_transaction_repository=sale_transaction_repository,
        rent_transaction_repository=rent_transaction_repository,
    )

    pages = {
        "대시보드": lambda: render_dashboard_page(
            complex_repository=complex_repository,
            listing_repository=listing_repository,
            finance_repository=finance_repository,
            analysis_repository=analysis_repository,
        ),
        "단지 등록": lambda: render_complex_page(complex_repository),
        "매물 입력": lambda: render_listing_page(
            complex_repository=complex_repository,
            listing_repository=listing_repository,
        ),
        "자금 프로필": lambda: render_finance_profile_page(finance_repository),
        "분석 결과": lambda: render_analysis_page(
            complex_repository=complex_repository,
            listing_repository=listing_repository,
            finance_repository=finance_repository,
            analysis_repository=analysis_repository,
            analysis_service=analysis_service,
            settings=settings,
        ),
    }

    st.sidebar.title(settings.app_name)
    selected_page = st.sidebar.radio("메뉴", list(pages.keys()))
    st.sidebar.caption("Phase 1 MVP · 로컬 Streamlit + SQLite")

    pages[selected_page]()


if __name__ == "__main__":
    main()
