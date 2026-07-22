# GitHub Pages 기반 실시간 ETF EDA 대시보드 구현 계획

네이버 금융 API 데이터를 기반으로 GitHub Pages에 배포하여 실시간(1시간 주기 자동 갱신)으로 데이터 분석이 가능한 EDA 대시보드를 구축합니다. CORS 제약을 극복하기 위해 GitHub Actions를 활용한 데이터 파이프라인을 구축하고, 다크/라이트 테마를 모두 지원하는 정적 웹 대시보드를 구현합니다.

## 사용자 검토 요구사항
> [!NOTE]
> * **배포 위치**: 대시보드는 리포지토리 루트의 `index.html`로 구성되어 GitHub Pages에서 즉시 호스팅됩니다.
> * **인증 및 푸시**: GitHub Actions 워크플로우가 1시간마다 데이터를 수집하고 커밋/푸시를 수행합니다. 이를 위해 Actions의 쓰기 권한(Write Permission) 활성화가 필요합니다.

## 제안된 변경 사항

---

### 1. 데이터 수집 및 전처리 파이프라인
웹 대시보드에서 CORS 문제 없이 데이터를 빠르게 fetch할 수 있도록 기존 CSV 저장 로직 외에 JSON 파일 포맷으로도 데이터를 내보내도록 수정합니다.

#### [MODIFY] [fetch_etf.py](file:///c:/Users/student/Documents/etf-eda/src/fetch_etf.py)
* `save_to_csv` 함수를 보완하거나 `save_to_json` 함수를 추가하여 `data/etf_items_latest.json` 및 `data/etf_items_latest.csv` 파일로 저장하게 합니다.
* 데이터가 프론트엔드 시각화에 적합하도록 정밀 가공하여 JSON으로 직렬화합니다.

---

### 2. 정적 웹 대시보드 구현
빌드 과정이 필요 없는 Single Page Application 구조로 개발하며, 다양한 인터랙티브 시각화를 포함합니다.

#### [NEW] [index.html](file:///c:/Users/student/Documents/etf-eda/index.html)
* **디자인 & 테마**: Tailwind CSS 기반의 세련된 UI. 밝은 모드와 어두운 모드를 전환할 수 있는 토글 스위치 제공.
* **차트 라이브러리**: Plotly.js / Chart.js CDN 연동
  * 시가총액 상위 10개 ETF 비교 (Bar chart)
  * 자산운용사별 시장 점유율 및 종목 수 (Donut chart)
  * 3개월 수익률 vs 시가총액 상관관계 (Scatter chart)
  * 일일 등락률 분포 히스토그램 (Histogram)
* **데이터 테이블**: 검색, 운용사 필터링, 정렬 기능이 포함된 실시간 반응형 데이터 테이블.
* **데이터 연동**: `data/etf_items_latest.json` 파일을 fetch하여 데이터 로드.

---

### 3. GitHub Actions 자동화 워크플로우 구축
매 시간마다 자동으로 네이버 API로부터 최신 데이터를 수집하고 변경 사항을 깃허브에 커밋 & 푸시하는 CI/CD 워크플로우를 생성합니다.

#### [NEW] [update_data.yml](file:///c:/Users/student/Documents/etf-eda/.github/workflows/update_data.yml)
* **수집 스케줄**: 매 1시간마다 작동 (`cron: "0 * * * *"`) 및 수동 트리거 지원.
* **환경 구성**: `astral-sh/setup-uv` 액션을 활용하여 가상환경 세팅 속도 최적화.
* **자동 푸시**: 수집된 최신 `data/etf_items_latest.json` 및 `data/etf_items_latest.csv` 변경사항을 `github-actions[bot]`을 통해 커밋 후 레포지토리에 푸시.

---

## 검증 계획

### 수동 검증 및 동작 테스트
1. **로컬 데이터 수집 테스트**:
   * 로컬에서 `python src/fetch_etf.py`를 실행하여 `data/etf_items_latest.json`이 정상적으로 생성되는지 검증합니다.
2. **로컬 웹서버 구동 테스트**:
   * VS Code 라이브 서버 또는 Python 심플 서버를 사용해 `index.html`을 열고, 다크/라이트 모드 전환 및 차트들이 데이터에 맞게 올바르게 그려지는지 검증합니다.
3. **GitHub Actions 실행 검증**:
   * 레포지토리에 푸시 후 깃허브 Actions 탭에서 워크플로우를 수동 트리거하여 정상적으로 데이터를 수집 및 자동 커밋하는지 확인합니다.
