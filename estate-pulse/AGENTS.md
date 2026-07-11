# Engineering Guidelines

## 1. 기본 원칙

- 기능을 한 번에 크게 만들지 말고 작은 단위로 구현한다.
- 기존 구현을 먼저 확인하고, 현재 상태를 `Already Implemented / Partially Implemented / Missing`으로 나눈 뒤 최소 변경 범위를 정한다.
- 기존 Service, Repository, UI, Analyzer, Collector를 우선 재사용한다.
- UI, 비즈니스 로직, DB 접근, 외부 API 수집 코드는 분리한다.
- 계산 로직은 Streamlit 화면 안에 직접 작성하지 않는다.
- 모든 계산 함수는 입력값과 출력값이 명확해야 한다.
- 나중에 FastAPI, PostgreSQL, 모바일 앱으로 전환할 수 있도록 모듈 경계를 유지한다.
- Repository Pattern과 Service Layer를 유지한다.
- SQLite fallback과 PostgreSQL runtime support를 함께 유지한다. 작업 범위가 아닌 경우 한쪽만 깨는 변경을 하지 않는다.
- 불필요한 아키텍처 변경과 대규모 리팩토링을 지양한다.

## 2. 디렉터리 규칙

- `collectors/`: 외부 데이터 수집
- `analyzers/`: 투자 판단, 급매 점수, 필요 현금 계산
- `repositories/`: DB 저장/조회
- `services/`: 여러 모듈을 조합하는 업무 로직
- `ui/`: Streamlit 화면
- `config/`: 설정값, 계산 기준
- `tests/`: 테스트 코드

## 3. 구현 우선순위

1. DB 스키마 생성
2. 관심 단지 등록
3. 매물 수동 입력
4. 사용자 자금 프로필 입력
5. 필요 현금 계산
6. 부족 금액 계산
7. 전세가율 계산
8. 급매 점수 계산
9. 분석 리포트 화면

## 4. 코딩 규칙

- Python 3.11 이상 기준으로 작성한다.
- 함수에는 type hint를 사용한다.
- 계산 함수에는 간단한 docstring을 작성한다.
- 금액은 내부적으로 원 단위 integer로 저장한다.
- 날짜는 ISO format 문자열 또는 datetime으로 관리한다.
- 하드코딩된 임계값은 `config/scoring_rules.py`로 분리한다.

## 5. 금지 사항

- UI 코드에서 SQL 직접 작성 금지
- UI 코드에서 점수 계산 금지
- DB 연결 정보를 코드에 하드코딩 금지
- 외부 API Key를 코드에 직접 작성 금지
- 민간 부동산 플랫폼 자동 수집 구현 금지
- 봇 탐지 우회, 세션 회전, CAPTCHA 우회 구현 금지

## 6. 테스트 기준

최소한 아래 계산 함수는 테스트를 작성한다.

- 필요 현금 계산
- 부족 금액 계산
- 전세가율 계산
- 최근 실거래 대비 할인율 계산
- 고점 대비 하락률 계산
- 급매 점수 계산

Repository, Service, Analyzer, import, matching, validation 변경 시에는 `unittest` 추가/수정과 기존 테스트 유지 여부를 함께 확인한다.

## 7. Codex 작업 방식

작업 전 반드시 아래 문서를 읽는다.

- README.md
- docs/ARCHITECTURE.md
- docs/CODEX_GUIDE.md
- docs/REVIEW_GUIDE.md
- AGENTS.md

작업은 Phase 단위로 진행한다.

한 번의 작업에서는 하나의 Phase만 구현한다.

문서에 있는 공통 규칙은 작업 시작 시 다시 길게 반복 설명하지 않는다.

작업 완료 후에는 사용자 지정 형식이 있으면 그 형식을 따르고, 없으면 `docs/CODEX_GUIDE.md`의 완료 보고 형식을 따른다.

## Important Rules

- Do not refactor unrelated files.
- Do not rewrite existing docs wholesale.
- Only implement the requested scope.
- Do not overwrite README.md unless explicitly instructed.
- Keep changes minimal and localized.

## Protected Paths

Never modify, restore, delete, compile, or inspect:

- .venv/
- .git/
- **pycache**/
- \*.pyc
- .env
- \*.db

These are outside the implementation scope.
