5. 프로젝트 구조
real-estate-investment-engine/
  app.py
  requirements.txt
  .env.example
  README.md

  config/
    settings.py

  data/
    app.db

  modules/
    collectors/
      molit_sale_collector.py
      molit_rent_collector.py
      reb_stats_collector.py
      regulation_collector.py

    analyzers/
      cash_flow_analyzer.py
      loan_analyzer.py
      tax_analyzer.py
      bargain_analyzer.py
      undervalue_analyzer.py
      risk_analyzer.py

    repositories/
      database.py
      complex_repository.py
      transaction_repository.py
      listing_repository.py
      analysis_repository.py

    services/
      analysis_service.py
      report_service.py

    ui/
      dashboard.py
      complex_form.py
      listing_form.py
      analysis_view.py

    utils/
      date_utils.py
      money_utils.py
      score_utils.py
6. DB 스키마
6.1 interest_area
CREATE TABLE interest_area (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sido TEXT NOT NULL,
    sigungu TEXT NOT NULL,
    dong TEXT,
    memo TEXT,
    created_at TEXT NOT NULL
);
6.2 apartment_complex
CREATE TABLE apartment_complex (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sido TEXT,
    sigungu TEXT,
    dong TEXT,
    address TEXT,
    build_year INTEGER,
    household_count INTEGER,
    lat REAL,
    lng REAL,
    created_at TEXT NOT NULL
);
6.3 manual_listing
CREATE TABLE manual_listing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complex_id INTEGER NOT NULL,
    area_m2 REAL NOT NULL,
    sale_price INTEGER NOT NULL,
    expected_jeonse_price INTEGER,
    floor TEXT,
    direction TEXT,
    condition_memo TEXT,
    source_memo TEXT,
    checked_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (complex_id) REFERENCES apartment_complex(id)
);
6.4 sale_transaction
CREATE TABLE sale_transaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complex_id INTEGER,
    complex_name TEXT,
    area_m2 REAL,
    deal_year INTEGER,
    deal_month INTEGER,
    deal_day INTEGER,
    price INTEGER,
    floor INTEGER,
    raw_address TEXT,
    created_at TEXT NOT NULL
);
6.5 rent_transaction
CREATE TABLE rent_transaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complex_id INTEGER,
    complex_name TEXT,
    area_m2 REAL,
    deal_year INTEGER,
    deal_month INTEGER,
    deal_day INTEGER,
    deposit INTEGER,
    monthly_rent INTEGER,
    floor INTEGER,
    raw_address TEXT,
    created_at TEXT NOT NULL
);
6.6 user_finance_profile
CREATE TABLE user_finance_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cash_amount INTEGER NOT NULL,
    annual_income INTEGER,
    existing_debt INTEGER DEFAULT 0,
    interest_rate REAL,
    ltv_limit REAL,
    dsr_limit REAL,
    created_at TEXT NOT NULL
);
6.7 analysis_result
CREATE TABLE analysis_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    required_cash INTEGER,
    shortage_cash INTEGER,
    jeonse_ratio REAL,
    discount_vs_recent_avg REAL,
    drop_from_high REAL,
    bargain_score INTEGER,
    undervalue_score INTEGER,
    risk_score INTEGER,
    decision TEXT,
    summary TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (listing_id) REFERENCES manual_listing(id)
);
7. 화면 구성
7.1 메인 대시보드
- 관심 단지 목록
- 최근 분석 결과
- 급매 후보 TOP 10
- 투자 가능 후보
- 부족 자금 큰 후보
7.2 단지 등록 화면
입력:
- 단지명
- 지역
- 전용면적
- 메모
7.3 매물 입력 화면
입력:
- 단지 선택
- 매물가
- 예상 전세가
- 층
- 향
- 상태 메모
- 출처 메모
7.4 분석 결과 화면
출력:
- 투자 가능/불가
- 필요현금
- 부족현금
- 전세가율
- 최근 실거래 대비 할인율
- 고점 대비 하락률
- 급매 점수
- 저평가 점수
- 주요 리스크
8. 급매 분석 로직 예시
def calculate_bargain_score(
    sale_price: int,
    recent_avg_price: int,
    one_year_high_price: int,
    expected_jeonse_price: int,
    required_cash: int,
    user_cash: int,
) -> dict:
    score = 0
    reasons = []

    discount_rate = (recent_avg_price - sale_price) / recent_avg_price * 100
    drop_from_high = (one_year_high_price - sale_price) / one_year_high_price * 100
    jeonse_ratio = expected_jeonse_price / sale_price * 100

    if discount_rate >= 10:
        score += 30
        reasons.append("최근 실거래 평균 대비 10% 이상 낮음")
    elif discount_rate >= 5:
        score += 20
        reasons.append("최근 실거래 평균 대비 5% 이상 낮음")
    elif discount_rate >= 3:
        score += 10
        reasons.append("최근 실거래 평균 대비 3% 이상 낮음")

    if drop_from_high >= 20:
        score += 20
        reasons.append("최근 1년 고점 대비 20% 이상 하락")
    elif drop_from_high >= 10:
        score += 10
        reasons.append("최근 1년 고점 대비 10% 이상 하락")

    if jeonse_ratio >= 70:
        score += 15
        reasons.append("전세가율 70% 이상")
    elif jeonse_ratio >= 60:
        score += 10
        reasons.append("전세가율 60% 이상")

    if user_cash >= required_cash:
        score += 15
        reasons.append("현재 보유 현금으로 투자 가능")
    else:
        reasons.append("현재 보유 현금으로는 투자 불가")

    return {
        "score": min(score, 100),
        "discount_rate": discount_rate,
        "drop_from_high": drop_from_high,
        "jeonse_ratio": jeonse_ratio,
        "reasons": reasons,
    }

## Current Architecture Update

Estate Pulse currently uses a layered Streamlit + SQLite architecture.

### Runtime Stack

- UI: Streamlit pages under `modules/ui/`
- Storage: SQLite through repository classes under `modules/repositories/`
- Business orchestration: services under `modules/services/`
- Calculation/scoring: analyzers under `modules/analyzers/`
- Configuration: `config/`
- Tests: `tests/`

The module boundaries are kept so a future FastAPI + PostgreSQL migration can reuse most Repository, Service, and Analyzer logic.

### Layer Responsibilities

- Repositories own SQL and persistence details. They should not contain scoring or business decision logic.
- Services combine repositories and analyzers. They own workflows such as analysis orchestration, rule selection, policy import, policy event matching, and regional regulation resolution.
- Analyzers provide deterministic calculation functions for required cash, shortage cash, loan terms, taxes, brokerage/costs, bargain score, liquidity score, complex grade, and investment score.
- UI modules render Streamlit forms/pages and call repositories/services rather than writing SQL directly.

### Main Domains

- Basic analysis: `apartment_complex`, `manual_listing`, `user_finance_profile`, `analysis_result`, `sale_transaction`, and `rent_transaction`.
- Comparison/ranking: `watchlist`, `OpportunityService`, bargain score, liquidity score, complex grade, and overall investment score.
- Investor-facing summary UI: Dashboard, watchlist, comparison, ranking, and analysis explainability all reuse saved analysis results and existing calculator outputs rather than a separate recommendation engine.
- Policy/rule administration: policy imports, rule candidates, loan rules, tax rules, brokerage/cost rules, regional regulation rows, and review/approval/application workflows.
- Policy Event: useful policy information that is not necessarily applied to calculation rules. It is currently an admin CRUD/review feature, not a standalone user lookup page.
- Regional regulation: active region status rows in `region_policy_status`.

### Finance Profile

Finance Profile currently stores:

- Cash amount
- Existing debt total
- Home count
- Owned real-estate market value
- Owned real-estate debt balance
- Credit loan balance
- Other loan balance
- Legacy `ltv_limit`
- Manual LTV usage flag
- Manual LTV rate
- Optional income, interest rate, and DSR fields retained for analysis compatibility

Default analysis uses loan rule and regional regulation based automatic LTV. Manual LTV is only applied when explicitly enabled on the finance profile or entered as a one-time analysis override. Manual LTV is validated in the 0 to 1 range at the UI/input layer.

The finance profile UI now treats annual interest rate as a percent input for humans. For example, `4.0` means `4%`, and the UI converts it to the internal ratio value used by analyzers and services. Ambiguous small decimal inputs are warned or blocked because rate-unit mistakes materially change DSR, expected loan amount, and monthly repayment outputs.

Funding scenarios:

- Cash-only purchase: uses cash amount as available cash.
- Sell-owned-real-estate-before-purchase: uses cash + owned real-estate market value - owned real-estate debt balance.

Sell-side taxes, brokerage, early repayment fees, and sale price discounts are not yet modeled.

### Analysis Explainability And Scenario UX

- The analysis page keeps the existing calculation pipeline and adds explanation blocks on top of the existing result dict.
- Explainability reuses `investment_score`, `bargain_score`, `liquidity_score`, `complex_grade`, `required_cash_efficiency_score`, `shortage_cash`, and `jeonse_ratio` values that already exist in analysis results.
- The `Scenario Analyzer` is implemented inside the analysis UI and reuses `AnalysisService` with temporary override inputs for sale price, jeonse price, interest rate, and one-time LTV.
- Scenario results are shown as baseline vs changed comparisons for expected loan amount, total required cash, shortage cash, monthly burden, and investment score.
- Scenario-specific interpretation remains presentation-layer logic. No separate scenario persistence model or DB schema was added.

### Policy And Regulation Structure

- Active region status is stored in `region_policy_status`.
- Loan rules are still stored and applied as row-level records keyed by purpose, region type, buyer type, and house price band.
- The active loan rule runtime still uses built-in config rows plus `rule_candidate` overlay rows. No dedicated `loan_rule` table was added.
- Supported current regulation concepts are `NON_REGULATED_AREA`, `LAND_TRANSACTION_PERMISSION`, `SPECULATION_OVERHEATED_DISTRICT`, and `ADJUSTMENT_TARGET_AREA`.
- `REGULATED_AREA` is retained for legacy compatibility but is not used as a new selection because it is a generic parent concept.
- Existing `REGULATED_AREA` rows are not automatically converted.
- Multiple active regulations for one region are represented by multiple rows, not by a normalized N:M master structure.
- SQLite does not enforce enum/check constraints for policy type values in the current schema. Service-layer validation controls allowed values.

### Loan Rule Admin Flow

- Admin loan rule management keeps the existing row structure and adds UI/service helpers around it rather than redesigning the engine.
- `RuleAdminService` now supports current-rule query filtering by purpose, region type, buyer type, house price, and `rule_version`.
- The admin `Loan Rule Wizard` collects shared policy fields once and expands a price-band matrix into multiple row candidates with preview before save.
- Batch update and batch deactivate continue to operate on applied/admin override candidate rows. Deactivate is implemented by setting `effective_to`; no `is_active` schema field was introduced.
- The admin page now separates a filtered "current applicable loan rule" query view from the full grouped rule dump, which remains available for inspection.

### Admin UX Notes

- The admin page groups work into `정책 운영`, `규칙 관리`, and `정책 수집/승인` to reduce operator context switching.
- Policy collection/review keeps the existing candidate workflow, but the default UI now emphasizes policy name, impact, target, change summary, warnings, approval, and rejection before developer-facing metadata.
- Candidate metadata such as IDs, confidence, changed JSON, and raw fields is still available under an advanced expander instead of the primary review surface.
- Tax rule and brokerage rule screens remain more limited than loan-rule management and can still operate as read-only views in the current MVP.

### User-Facing Summary Screens

- Dashboard is now arranged as an investor decision summary page: best candidate first, funding status first, concise reasons/cautions, recent analyses in a collapsed section, and policy-event context below.
- Ranking adds Top 3 summary cards with short reason lists while keeping the detailed ranking table and unavailable-analysis rows.
- Comparison keeps the existing comparison flow but promotes core decision columns such as total required cash, additional required cash, liquidity, bargain score, and investment score.
- Watchlist is presented as an investment-candidate management screen with simplified user-facing labels and a related policy-event section.

### Menu Structure

The sidebar is separated into user and admin sections.

User menu:

- Dashboard
- 단지
- 매물
- 자금
- 분석
- 관심단지
- 비교
- 랭킹

Admin menu:

- 관리자

Admin tabs:

- 정책 이벤트
- 대출 규칙
- 세금 규칙
- 중개보수 규칙
- 지역 규제 상태
- 정책 가져오기

### SQLite Limitations And Migration Notes

- Additive schema compatibility is handled through initialization-time `ALTER TABLE` checks.
- Existing SQLite DB files should not be modified directly during development tasks.
- Scenario Analyzer currently supports only one immediate baseline-vs-changed comparison in the analysis page. It does not save multiple scenarios, render charts, or simulate policy imports/rule changes.
- Dashboard and ranking summaries are derived from saved recent analysis results, not from a separate portfolio model.
- PostgreSQL migration should consider CHECK constraints for enum-like fields.
- PostgreSQL migration should consider master tables for regulation types and policy notices.
- N:M structures should be considered when a single policy notice needs to connect many regions and many regulation types.
- A separate read-only user policy view can be added later if Policy Events become user-facing.
