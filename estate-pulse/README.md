# Estate Pulse MVP

Estate Pulse is a personal real-estate investment analysis MVP built with Python and Streamlit, with SQLite as the default local database and optional PostgreSQL runtime support.

The current MVP helps compare listings, analyze purchase affordability, manage real-estate policy/rule data, and review regional regulation context.

The current build includes:

- SQLite schema initialization
- CRUD for apartment complexes
- CRUD for manual listings
- CRUD for user finance profiles
- Owner-occupied and investment analysis
- Required cash, shortage cash, jeonse ratio, bargain score, liquidity score, complex grade, and investment score analysis
- Transaction-based sale/rent market context
- Analysis explainability with score factors, bargain context, applied-rule traces, and scenario comparison
- Loan rule engine, tax rule, brokerage/cost rule, and regional regulation support
- Investor-facing dashboard, watchlist, comparison, ranking, and analysis history
- Policy import workflow with rule candidates and policy event candidates
- Admin pages grouped around policy operations, rule management, and policy review/approval
- Loan rule admin support for current-rule query, Wizard-style multi-row registration, inline row editing, batch update, and batch deactivate

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
- `modules/repositories/database.py`: SQLite/PostgreSQL connection helpers and schema initialization
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

If `DATABASE_URL` is not set, the app creates and uses `data/app.db` automatically on first run.

## Local PostgreSQL

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_postgres_windows.ps1
```

```powershell
$env:DATABASE_URL="postgresql://estate:estate@localhost:5432/estate_pulse"
$env:TEST_DATABASE_URL="postgresql://estate:estate@localhost:5432/estate_pulse_test"
powershell -ExecutionPolicy Bypass -File .\scripts\init_postgres.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run_postgres_smoke.ps1
.\.venv\Scripts\python -m streamlit run app.py
```

Leave `DATABASE_URL` unset to keep the default SQLite development path. When `DATABASE_URL` is set, the app connects to PostgreSQL instead. `TEST_DATABASE_URL` is used by the PostgreSQL smoke test and should point to the separate `estate_pulse_test` database.

The Windows install/init flow creates the `estate` role, the `estate_pulse` and `estate_pulse_test` databases, and applies `migrations/postgres/0001_initial_schema.sql` to both databases.

## User Workflow

1. Register one or more apartment complexes.
2. Add manual listings linked to a complex.
3. Create a finance profile with cash, debt, owned real-estate, annual income, annual interest rate, and optional manual LTV override settings.
4. Open the analysis page.
5. Select a listing and finance profile.
6. Choose owner-occupied or investment analysis and the funding scenario.
7. Optionally adjust market inputs, repair cost, expected loan amount, one-time LTV override, or scenario inputs for price/jeonse/rate changes.
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

Admin groups:

- `정책 이벤트`
- `대출 규칙`
- `세금 규칙`
- `중개보수 규칙`
- `지역 규제 상태`
- `정책 가져오기`

Policy Event is currently treated as an admin CRUD/review feature, not as a standalone user-facing lookup page.

Current user-facing labels in the Streamlit UI are:

- `Dashboard`
- `단지`
- `매물`
- `자금`
- `분석`
- `투자 후보`
- `매물 비교`
- `투자 랭킹`
- `관리자`

The current admin page groups work into `정책 운영`, `규칙 관리`, and `정책 수집/승인`.

## Dashboard Design Principle

Dashboard는 분석 결과를 나열하는 화면이 아니라
"지금 무엇을 사야 하는가"에 대한 의사결정 화면을 목표로 한다.

사용자에게는 다음 질문에 대한 답을 우선 제공한다.

1. 지금 살 수 있는 후보가 있는가
2. 가장 좋은 후보는 무엇인가
3. 얼마가 부족한가
4. 어떤 정책이 영향을 주는가

세부 분석은 Analysis / Ranking 화면에서 확인한다.

## Investment Score

투자점수는 절대적인 가치 평가가 아니다.

다음 요소를 종합하여 상대 비교용으로 사용한다.

- 급매 매력도
- 자금 효율성
- 유동성
- 단지 등급
- 부족 자금 패널티

동일 시점 후보 비교에 활용하며
실제 투자 판단은 정책, 자금 계획, 실거주 목적 등을 함께 고려해야 한다.

## Current MVP Scope

Analysis:

- Apartment complex CRUD
- Manual listing CRUD
- Finance profile CRUD
- Owner-occupied analysis
- Investment analysis
- Transaction-based sale/rent market analysis
- Loan rule engine
- Analysis explainability for investment score, bargain score, jeonse ratio, and complex grade
- Scenario Analyzer for single baseline-vs-changed comparison inside the analysis page
- Analysis history saving

Comparison and ranking:

- Investment-candidate watchlist
- Comparison
- Ranking
- Ranking Top 3 summary cards with reason snippets
- Bargain score
- Liquidity score
- Complex grade
- Overall investment score

Policy and regulation:

- Loan rule management
- Loan rule current-rule query filters by purpose, region type, buyer type, house price, and rule version
- Loan rule Wizard registration for shared policy inputs plus price-band matrix preview
- Loan rule batch update and batch deactivate for applied/admin override rows
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
- Annual income
- Annual interest rate input
- Net worth summary cards in the finance profile UI
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
- Finance profile annual interest rate is entered as a percent value in the UI. For example, `4.0` means `4%`, and the app stores it as a ratio for calculation.
- The finance profile UI warns when a rate input looks ambiguous because incorrect rate units can significantly distort DSR, expected loan amount, and monthly repayment.
- The repository and service layers are separated so FastAPI and PostgreSQL can be added later without rewriting the UI logic.
- SQLite schema migrations are handled by additive `ALTER TABLE` checks during initialization. Existing SQLite DB files are not edited directly by development tasks.
- SQLite does not enforce enum/check constraints for policy types at the DB level. The current MVP relies on Service validation.
- `REGULATED_AREA` is retained only for legacy compatibility. It is not shown as a new regional regulation selection; existing rows are not automatically converted.
- Regional regulation currently uses practical multiple rows for multiple regulations on one region, not a normalized N:M master structure.
- Scenario Analyzer currently supports only immediate single-scenario comparison in the analysis page. It does not save multiple scenarios, render charts, or simulate policy-rule changes.
- Dashboard and ranking summaries are based on saved recent analysis results, not on a separate portfolio or recommendation engine.
- Tax and brokerage admin screens remain limited compared with loan-rule management and may still be read-only in parts of the current admin UI.
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
