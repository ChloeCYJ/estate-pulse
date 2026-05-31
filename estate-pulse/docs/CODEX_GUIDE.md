9. 리포트 출력 예시
[분석 결과]

단지: OOO아파트
매물가: 13.0억
예상 전세가: 7.4억
전세가율: 56.9%

최근 6개월 실거래 평균: 13.8억
최근 1년 최고가: 15.0억
실거래 평균 대비 할인율: -5.8%
고점 대비 하락률: -13.3%

필요현금: 5.9억
보유현금: 2.0억
부족현금: 3.9억

급매 점수: 68점
저평가 점수: 71점

판정:
급매 후보로 검토할 수 있으나, 현재 보유 현금 기준으로는 투자 불가.
추가 현금 3.9억 또는 대출/전세 조건 재검토 필요.
10. 구현 우선순위
1. SQLite DB 초기화
2. 관심 단지 CRUD
3. 매물 수동 입력 CRUD
4. 사용자 자금 프로필 입력
5. 필요현금 계산
6. 급매 점수 계산
7. 분석 결과 저장
8. Streamlit 화면 구현
9. 국토부 실거래가 API 연동
10. 전월세 실거래가 API 연동
11. 토허제/규제 체크
12. 리포트 화면 고도화
11. 구현 시 주의사항
- 민간 부동산 서비스 무단 크롤링 금지
- 봇 탐지 우회 로직 구현 금지
- 모든 수집 데이터는 출처와 수집일자를 저장
- 계산식은 하드코딩하지 말고 config로 분리
- 세금/대출 규제는 자주 바뀌므로 버전 관리
- 분석 결과는 투자 조언이 아니라 판단 보조 정보로 표기
12. Codex 작업 지시
위 지침서를 기준으로 Python Streamlit 기반 MVP를 구현하라.

우선 구현 범위:
1. SQLite DB 초기화
2. 관심 단지 등록/조회
3. 매물 수동 입력/조회
4. 사용자 자금 프로필 입력
5. 필요현금 계산
6. 급매 점수 계산
7. 분석 리포트 화면 출력

공공 API 연동은 인터페이스만 먼저 만들고, 실제 API Key는 .env에서 읽도록 구성하라.

민간 부동산 서비스 크롤링, 봇 탐지 우회, 세션 회전, CAPTCHA 우회 코드는 작성하지 마라.
## Current Codex Working Guide

This section reflects the current Estate Pulse implementation and should be followed for new Codex work.

### Required Reading Before Work

Read these files before implementation work:

- `AGENTS.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/CODEX_GUIDE.md`

Also inspect the current code implementation before changing behavior. Do not duplicate functionality that already exists.

### Protected Paths

Do not modify, restore, delete, compile, or inspect protected runtime artifacts:

- `.venv/`
- `.git/`
- `__pycache__/`
- `*.pyc`
- `.env`
- `*.db`

SQLite DB files, including `data/app.db`, must not be edited directly. Schema compatibility should be handled in code through initialization-time additive migrations when required.

### General Rules

- Keep changes minimal and localized.
- Do not refactor unrelated files.
- Do not change DB schema unless the task explicitly requires it.
- Do not update README/docs unless the user explicitly requests documentation updates.
- Do not implement external API integration unless explicitly requested.
- Do not implement private real-estate platform scraping.
- Do not implement bot detection bypass, session rotation, or CAPTCHA bypass.
- Do not write SQL directly in Streamlit UI code.
- Keep UI, service orchestration, repository access, and analyzer calculation logic separated.
- Preserve future FastAPI + PostgreSQL migration paths.

### Current Architecture Expectations

- Repositories own persistence and SQL.
- Services combine repositories and analyzers.
- Analyzers contain deterministic calculation/scoring functions.
- UI modules handle Streamlit forms/rendering and call services/repositories.

For feature development, first check whether the relevant Repository, Service, Analyzer, or UI module already exists. Extend existing modules where appropriate rather than creating parallel implementations.

### Current Feature Areas

Basic analysis:

- Complex CRUD
- Listing CRUD
- Finance Profile CRUD
- Owner-occupied analysis
- Investment analysis
- Transaction-based market context
- Loan rule engine
- Analysis history

Comparison/ranking:

- Watchlist
- Comparison
- Ranking
- Bargain score
- Liquidity score
- Complex grade
- Overall investment score

Policy/admin:

- Policy Event admin management
- Loan rule management
- Tax rule management
- Brokerage/cost rule management
- Regional regulation management
- Policy document import
- Policy candidate generation, approval, rejection, and application
- Integrated policy document section review

Finance Profile:

- Cash amount
- Existing debt
- Home count
- Owned real-estate market value
- Owned real-estate debt balance
- Credit loan balance
- Other loan balance
- Automatic LTV from policy/loan rule engine by default
- Optional manual LTV override in the 0 to 1 range

### Policy And Regulation Notes

- `REGULATED_AREA` is a legacy/generic parent concept and is not shown as a new regional regulation selection.
- Existing `REGULATED_AREA` DB rows are not automatically converted.
- Current regional regulation uses practical multiple rows for multiple regulations on one region.
- It is not yet a normalized N:M notice-to-region-to-regulation structure.
- SQLite does not enforce enum/check constraints for policy types; Service validation controls supported values.
- Consider PostgreSQL CHECK constraints or regulation type master tables during migration.

### Test Command

Use the standard unittest suite:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python -B -m unittest discover -s tests -v
```

Using `PYTHONDONTWRITEBYTECODE=1` and `-B` reduces `__pycache__` and `*.pyc` changes.

### Documentation Rules

- Do not overwrite documentation wholesale.
- Preserve existing structure where practical.
- Add or minimally update sections to reflect actual implemented behavior.
- Do not document planned features as complete.
- Include known limitations when behavior is intentionally constrained.

### Completion Report

When finishing a task, report:

- Files changed
- Main implementation or documentation changes
- Tests run and results, or why tests were not run
- Known limitations
- Suggested next step when useful
