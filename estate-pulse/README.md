# Estate Pulse Phase 1 MVP

Estate Pulse is a personal real-estate investment analysis MVP built with Python, Streamlit, and SQLite.

This Phase 1 build includes:

- SQLite schema initialization
- CRUD for apartment complexes
- CRUD for manual listings
- CRUD for user finance profiles
- Required cash, shortage cash, jeonse ratio, and bargain score analysis
- Streamlit pages for registration, input, and analysis review

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
- `modules/services/analysis_service.py`: Phase 1 analysis orchestration
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

## Phase 1 Workflow

1. Register one or more apartment complexes.
2. Add manual listings linked to a complex.
3. Create a finance profile with cash, debt, and LTV/DSR inputs.
4. Open the analysis page.
5. Select a listing and finance profile.
6. Enter manual benchmark values for recent average price and one-year high price.
7. Optionally adjust repair cost or expected loan amount.
8. Run and optionally save the analysis result.

## Tests

Run the basic analyzer test suite:

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

## Notes

- Calculation defaults such as acquisition tax, brokerage fee, legal fee, and contingency rate are configurable through `.env`.
- The current analysis page uses manual benchmark inputs because public transaction ingestion is deferred to a later phase.
- The repository and service layers are separated so FastAPI and PostgreSQL can be added later without rewriting the UI logic.

## Documentation Protection

README.md and docs/\* are source-of-truth documents.

Do not:

- overwrite them
- recreate them
- heavily rewrite them

Only append or minimally modify documentation when explicitly requested.
