from __future__ import annotations

from config.settings import get_settings
from modules.repositories.complex_repository import ApartmentComplexRepository
from modules.repositories.database import initialize_database
from modules.repositories.rent_transaction_repository import RentTransactionRepository
from modules.repositories.sale_transaction_repository import SaleTransactionRepository
from modules.services.mock_transaction_seed_service import MockTransactionSeedService


def main() -> None:
    settings = get_settings()
    initialize_database(settings.database_path)

    seed_service = MockTransactionSeedService(
        complex_repository=ApartmentComplexRepository(settings.database_path),
        sale_transaction_repository=SaleTransactionRepository(settings.database_path),
        rent_transaction_repository=RentTransactionRepository(settings.database_path),
    )
    result = seed_service.seed()
    print(
        "Mock transaction seed completed: "
        f"{result['complex_count']} complexes, "
        f"{result['sale_transaction_count']} sale transactions, "
        f"{result['rent_transaction_count']} rent transactions."
    )


if __name__ == "__main__":
    main()
