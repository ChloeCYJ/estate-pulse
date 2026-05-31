# Estate Pulse MVP

Estate Pulse is a personal real-estate investment analysis MVP built with Python, Streamlit, and SQLite.

The current MVP helps compare listings, analyze purchase affordability, manage real-estate policy/rule data, and review regional regulation context.

The current build includes:

- SQLite schema initialization
- CRUD for apartment complexes
- CRUD for manual listings
- CRUD for user finance profiles
- Owner-occupied and investment analysis
- Required cash, shortage cash, jeonse ratio, bargain score, liquidity score, complex grade, and investment score analysis
- Transaction-based sale/rent market context
- Loan rule engine, tax rule, brokerage/cost rule, and regional regulation support
- Watchlist, comparison, ranking, and analysis history
- Policy import workflow with rule candidates and policy event candidates
- Admin pages for policy events, rule management, regional regulation, and policy document review

External API integration is intentionally not implemented yet. Public collector modules exist as stubs only, and no private platform scraping is included.

## Project Structure

```text
estate-pulse/
  app.py
  requirements.txt
  .env.example
  config/
  data/
  docs/
  modules/
    collectors/
    analyzers/
    repositories/
    services/
    ui/
    utils/
  tests/
```

## Key Modules

- `config/settings.py`: environment-driven configuration
- `modules/repositories/database.py`: SQLite connection helpers and schema initialization
- `modules/repositories/complex_repository.py`: CRUD for `apartment_complex`
- `modules/repositories/listing_repository.py`: CRUD for `manual_listing`
- `modules/repositories/finance_profile_repository.py`: CRUD for `user_finance_profile`
- `modules/repositories/policy_event_repository.py`: CRUD for reference policy events
- `modules/repositories/region_policy_repository.py`: CRUD for active regional regulation status rows
- `modules/services/analysis_service.py`: analysis orchestration for owner-occupied and investment scenarios
- `modules/services/rule_runtime_service.py`: active loan/tax/brokerage rule runtime access
- `modules/services/policy_import_service.py`: policy document import, candidate review, and application workflow
- `modules/services/policy_event_service.py`: reference policy event normalization, matching, and status handling
- `modules/services/region_policy_service.py`: regional regulation matching and loan-region resolution
- `modules/services/opportunity_service.py`: watchlist, comparison, and ranking orchestration
- `modules/analyzers/`: calculation and scoring functions
- `modules/ui/`: Streamlit page modules

## Environment Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

## Run the App

```powershell
.venv\Scripts\python -m streamlit run app.py
```

The app creates `data/app.db` automatically on first run.

## User Workflow

1. Register one or more apartment complexes.
2. Add manual listings linked to a complex.
3. Create a finance profile with cash, debt, owned real-estate, and optional manual LTV override settings.
4. Open the analysis page.
5. Select a listing and finance profile.
6. Choose owner-occupied or investment analysis and the funding scenario.
7. Optionally adjust market inputs, repair cost, expected loan amount, or one-time LTV override.
8. Run and optionally save the analysis result.
9. Use watchlist, comparison, and ranking pages to compare candidates.

## Menus

User menu:

- `Dashboard`
- `단지`
- `매물`
- `자금`
- `분석`
- `관심단지`
- `비교`
- `랭킹`

Admin menu:

- `관리자`

Admin tabs:

- `정책 이벤트`
- `대출 규칙`
- `세금 규칙`
- `중개보수 규칙`
- `지역 규제 상태`
- `정책 가져오기`

Policy Event is currently treated as an admin CRUD/review feature, not as a standalone user-facing lookup page.

## Current MVP Scope

Analysis:

- Apartment complex CRUD
- Manual listing CRUD
- Finance profile CRUD
- Owner-occupied analysis
- Investment analysis
- Transaction-based sale/rent market analysis
- Loan rule engine
- Analysis history saving

Comparison and ranking:

- Watchlist
- Comparison
- Ranking
- Bargain score
- Liquidity score
- Complex grade
- Overall investment score

Policy and regulation:

- Loan rule management
- Tax rule management
- Brokerage/cost rule management
- Regional regulation management
- Policy document import
- Policy candidate generation, approval, rejection, and application
- Integrated policy document handling
- Reference-only Policy Event management

Finance profile:

- Cash amount
- Existing debt
- Home count
- Owned real-estate market value
- Owned real-estate debt balance
- Credit loan balance
- Other loan balance
- Default LTV calculation through policy/loan rule engine
- Optional manual LTV override for policy data errors or special bank conditions

Funding scenarios:

- Cash-only purchase analysis
- Sell-owned-real-estate-before-purchase analysis using cash + owned real-estate value - owned real-estate debt

## Tests

Run the basic analyzer test suite:

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

## Notes

- Calculation defaults such as acquisition tax, brokerage fee, legal fee, and contingency rate are configurable through `.env`.
- The current analysis page can use transaction-derived market context and optional manual benchmark overrides.
- The repository and service layers are separated so FastAPI and PostgreSQL can be added later without rewriting the UI logic.
- SQLite schema migrations are handled by additive `ALTER TABLE` checks during initialization. Existing SQLite DB files are not edited directly by development tasks.
- SQLite does not enforce enum/check constraints for policy types at the DB level. The current MVP relies on Service validation.
- `REGULATED_AREA` is retained only for legacy compatibility. It is not shown as a new regional regulation selection; existing rows are not automatically converted.
- Regional regulation currently uses practical multiple rows for multiple regulations on one region, not a normalized N:M master structure.
- Future PostgreSQL migration should consider CHECK constraints, regulation type master tables, and N:M structures for policy notices that apply multiple regulations to multiple regions.

## Roadmap Summary

- Add read-only user-facing policy event views if needed.
- Improve finance profile use in DSR, net worth, and multi-home tax logic.
- Add sell-side costs for replacement purchase scenarios.
- Replace SQLite validation gaps with PostgreSQL constraints where appropriate.
- Introduce normalized policy notice/regulation master structures when policy notice-level management becomes necessary.

## Documentation Protection

README.md and docs/\* are source-of-truth documents.

Do not:

- overwrite them
- recreate them
- heavily rewrite them

Only append or minimally modify documentation when explicitly requested.
