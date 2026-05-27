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