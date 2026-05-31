from __future__ import annotations

from pathlib import Path

from modules.repositories.database import execute, fetch_all, fetch_one
from modules.utils.date_utils import utc_now_iso


class UserFinanceProfileRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create(
        self,
        *,
        cash_amount: int,
        annual_income: int | None,
        existing_debt: int,
        interest_rate: float | None,
        ltv_limit: float | None,
        dsr_limit: float | None,
        home_count: int = 0,
        owned_real_estate_value: int = 0,
        owned_real_estate_debt: int = 0,
        credit_loan_balance: int = 0,
        other_loan_balance: int = 0,
        use_manual_ltv: bool = False,
        manual_ltv_rate: float | None = None,
    ) -> int:
        return execute(
            self.database_path,
            """
            INSERT INTO user_finance_profile (
                cash_amount, annual_income, existing_debt, interest_rate,
                ltv_limit, dsr_limit, home_count, owned_real_estate_value,
                owned_real_estate_debt, credit_loan_balance, other_loan_balance,
                use_manual_ltv, manual_ltv_rate, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cash_amount,
                annual_income,
                existing_debt,
                interest_rate,
                ltv_limit,
                dsr_limit,
                home_count,
                owned_real_estate_value,
                owned_real_estate_debt,
                credit_loan_balance,
                other_loan_balance,
                1 if use_manual_ltv else 0,
                manual_ltv_rate,
                utc_now_iso(),
            ),
        )

    def get(self, profile_id: int) -> dict | None:
        return fetch_one(
            self.database_path,
            "SELECT * FROM user_finance_profile WHERE id = ?",
            (profile_id,),
        )

    def get_latest(self) -> dict | None:
        return fetch_one(
            self.database_path,
            """
            SELECT * FROM user_finance_profile
            ORDER BY created_at DESC
            LIMIT 1
            """,
        )

    def list_all(self) -> list[dict]:
        return fetch_all(
            self.database_path,
            "SELECT * FROM user_finance_profile ORDER BY created_at DESC",
        )

    def update(
        self,
        profile_id: int,
        *,
        cash_amount: int,
        annual_income: int | None,
        existing_debt: int,
        interest_rate: float | None,
        ltv_limit: float | None,
        dsr_limit: float | None,
        home_count: int = 0,
        owned_real_estate_value: int = 0,
        owned_real_estate_debt: int = 0,
        credit_loan_balance: int = 0,
        other_loan_balance: int = 0,
        use_manual_ltv: bool = False,
        manual_ltv_rate: float | None = None,
    ) -> None:
        execute(
            self.database_path,
            """
            UPDATE user_finance_profile
            SET
                cash_amount = ?,
                annual_income = ?,
                existing_debt = ?,
                interest_rate = ?,
                ltv_limit = ?,
                dsr_limit = ?,
                home_count = ?,
                owned_real_estate_value = ?,
                owned_real_estate_debt = ?,
                credit_loan_balance = ?,
                other_loan_balance = ?,
                use_manual_ltv = ?,
                manual_ltv_rate = ?
            WHERE id = ?
            """,
            (
                cash_amount,
                annual_income,
                existing_debt,
                interest_rate,
                ltv_limit,
                dsr_limit,
                home_count,
                owned_real_estate_value,
                owned_real_estate_debt,
                credit_loan_balance,
                other_loan_balance,
                1 if use_manual_ltv else 0,
                manual_ltv_rate,
                profile_id,
            ),
        )

    def delete(self, profile_id: int) -> None:
        execute(
            self.database_path,
            "DELETE FROM user_finance_profile WHERE id = ?",
            (profile_id,),
        )
