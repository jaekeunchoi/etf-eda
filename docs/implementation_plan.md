# 네이버 금융 API 실시간 ETF 종합 EDA 대시보드 구현 계획

본 계획서는 네이버 금융 ETF 리스트 API 데이터를 실시간으로 수집하여 Streamlit 기반의 인터랙티브 EDA 대시보드를 구축하는 방안을 제시합니다. 파일 저장을 거치지 않고 메모리상에서 실시간으로 데이터를 가공·분석하여 사용자에게 대화형 시각화 및 깊이 있는 통찰을 제공하는 것을 목표로 합니다.

## User Review Required

> [!IMPORTANT]
> 1. **패키지 추가 설치**: Streamlit 대시보드 구현 및 인터랙티브 시각화를 위해 `.venv` 환경에 `streamlit`, `plotly` 패키지 설치가 필요합니다.
> 2. **실행 환경**: Streamlit 앱은 로컬 웹 서버로 동작하므로 `uv run streamlit run src/app.py` 형식으로 실행하게 됩니다.

## Proposed Changes

프로젝트 구조에 맞게 다음과 같이 파일들을 구성하고 수정할 것입니다.

```
c:\Users\student\Documents\etf-eda\
├── .venv/                   # 기존 파이썬 가상환경
├── docs/
│   └── implementation_plan.md  # [NEW] 본 계획서 복사본
├── src/
│   ├── __init__.py          # [NEW] 모듈 초기화 파일
│   ├── app.py               # [NEW] Streamlit 메인 애플리케이션 파일
│   └── data_loader.py       # [NEW] 실시간 네이버 API 호출 및 전처리 모듈
```

---

### [Component 1] 의존성 패키지 설치
Streamlit 웹앱 개발과 Plotly 인터랙티브 차트 구성을 위한 패키지를 `.venv` 환경에 설치합니다.
- `streamlit`: 대시보드 프레임워크
- `plotly`: 인터랙티브 시각화 차트 라이브러리

---

### [Component 2] 데이터 로더 모듈 (`src/data_loader.py`)

#### [NEW] [data_loader.py](file:///c:/Users/student/Documents/etf-eda/src/data_loader.py)
실시간으로 네이버 금융 API 데이터를 호출하고 pandas DataFrame으로 정제하여 리턴하는 전용 모듈입니다.
- **실시간 API 연동**: 사용자가 지정한 네이버 API 주소(`https://finance.naver.com/api/sise/etfItemList.nhn?etfType=0&targetColumn=market_sum&sortOrder=desc`)를 호출합니다. URL에 `_callback`이 있는 경우와 없는 경우를 모두 유연하게 처리할 수 있도록 정규식 기반의 JSON 파싱(JSONP 대응) 안전 장치를 마련합니다.
- **데이터 전처리**:
  - 컬럼 한글화 적용 (`itemcode` -> `종목코드`, `itemname` -> `종목명`, `nowVal` -> `현재가`, `changeVal` -> `전일대비변동액`, `changeRate` -> `등락률`, `nav` -> `NAV`, `threeMonthEarnRate` -> `3개월수익률`, `quant` -> `거래량`, `amonut` -> `거래대금(백만)`, `marketSum` -> `시가총액(억)`)
  - 추가 파생 변수 계산: **NAV 괴리율(%)** = `((현재가 - NAV) / NAV) * 100`
  - **운용사 브랜드 추출**: 종목명 첫 단어(KODEX, TIGER, ACE, KBSTAR, SOL, ARIRANG, HANARO, WOORI 등)를 추출하여 운용사 컬럼(`운용사`) 생성

---

### [Component 3] Streamlit 대시보드 웹 앱 (`src/app.py`)

#### [NEW] [app.py](file:///c:/Users/student/Documents/etf-eda/src/app.py)
다양한 필터와 지표, 탭 구조 시각화를 포함하는 대시보드 메인 파일입니다.

1. **상단 레이아웃 (Sidebar & Key Metrics)**
   - **실시간 새로고침**: 데이터 수집 시간 표시 및 수동 새로고침 버튼 제공
   - **필터링 조건**: 운용사 선택(다중 선택), 등락 여부 필터, 시가총액 범위 필터 제공
   - **주요 KPI 요약 카드**: 전체 종목 수, 총 시가총액 합계, 당일 상승/하락 종목 비율, 평균 3개월 수익률 등 표시

2. **메인 화면 (Tabs 구조)**
   - **Tab 1: 시장 요약 & 운용사 점유율**
     - 운용사별 시가총액 점유율 (Plotly Treemap / Pie Chart)
     - 운용사별 평균 3개월 수익률 비교 (Plotly Bar Chart)
   - **Tab 2: 순위 분석 (Top Rankings)**
     - 시가총액 Top 10 및 거래대금 Top 10 (Horizontal Bar Chart)
     - 당일 등락률 상/하위 Top 10 (Color-coded Bar Chart)
   - **Tab 3: 분포 및 관계성 분석 (EDA)**
     - 3개월 수익률 분포 (Histogram & KDE style)
     - 시가총액 대비 거래대금 분포 (Scatter Plot)
     - 변수간 상관관계 히트맵 (Plotly Heatmap)
     - NAV 괴리율 분포 (Box Plot)
   - **Tab 4: 실시간 데이터 테이블**
     - 검색 기능 및 다이내믹 정렬이 가능한 대화형 테이블
     - CSV 내보내기 기능 (메모리 내 다운로드 링크)
   - **Tab 5: 개별 종목 정밀 진단**
     - 특정 ETF 선택 시 해당 종목의 상세 스펙(현재가, NAV, 괴리율 상태, 3개월 수익률 추이 비교) 시각화 및 분석 리포트 제공

---

## Verification Plan

### Automated Tests
1. **패키지 설치 및 실행 여부 확인**:
   - `uv run streamlit --help` 또는 실행 테스트
2. **데이터 수집 모듈 검증**:
   - 대시보드 개발 전 `uv run python -c "from src.data_loader import load_realtime_etf; df = load_realtime_etf(); print(df.info())"` 명령어를 통해 정상적으로 한글 컬럼 변환 및 파생 변수 생성이 완료되는지 테스트합니다.

### Manual Verification
1. **대시보드 구동 테스트**:
   - `uv run streamlit run src/app.py`를 실행하여 로컬 포트(8501 등)로 정상 접속 확인
   - 사이드바 필터 조작 시 차트와 테이블이 즉각적으로 필터링되는지 검증
   - 운용사별 점유율 및 변수 간 상관관계 히트맵 등 6개 이상의 대화형 그래프가 정상 렌더링되는지 확인
   - '개별 종목 정밀 진단' 탭에서 종목 검색 및 괴리율 경보 로직이 잘 작동하는지 검증
