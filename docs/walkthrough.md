# ETF EDA 대시보드 구축 완료 보고서 (Walkthrough)

네이버 금융 API를 주기적으로 수집하여 GitHub Pages에 정적 웹 형태로 호스팅 가능한 ETF 실시간 EDA 대시보드 및 자동화 파이프라인 구축을 완료했습니다.

---

## 🛠️ 작업 내용 및 변경 파일

### 1. 데이터 수집 파이프라인 보완
* **[fetch_etf.py](file:///c:/Users/student/Documents/etf-eda/src/fetch_etf.py)**
  * 기존 CSV 저장 로직에 추가로 `save_to_json` 함수를 구현했습니다.
  * 데이터는 `data/etf_items_latest.json` 및 각 주기별 이력 파일(`.json`)로 저장됩니다.
  * `orient="records"` 및 `force_ascii=False` 형식을 지정해 웹 브라우저에서 JSON 데이터를 즉시 로드하고 한글이 깨지지 않도록 처리했습니다.

### 2. 정적 웹 대시보드 개발
* **[index.html](file:///c:/Users/student/Documents/etf-eda/index.html)**
  * **프레임워크 프리**: 별도의 빌드 도구 없이 동작 가능한 단일 HTML 파일로 개발했습니다.
  * **풍부한 에스테틱**: Tailwind CSS 및 Noto Sans KR 폰트를 적용하여 고급스러운 다크 모드를 기본으로 적용했습니다.
  * **테마 토글**: 라이트 모드와 다크 모드 간 실시간 전환이 가능하도록 구성했습니다.
  * **Plotly.js 시각화**:
    1. **시가총액 상위 10개** 비교 (막대 차트)
    2. **자산운용사별 시장 점유율** (도넛 차트 - 점유율 및 세부 툴팁)
    3. **3개월 수익률 vs 시가총액 상관관계** (버블 산점도 - 거래량 크기 시각화)
    4. **일일 등락률 분포** (히스토그램)
  * **검색 & 정렬 테이블**: 종목명/종목코드 실시간 검색, 자산운용사별 필터링, 정렬(헤더 클릭), 그리고 가독성을 위한 페이징 처리(페이지당 15개)가 제공됩니다. 테마 전환이나 필터링 시 차트도 실시간으로 다시 그려집니다.

### 3. GitHub Actions 자동화 워크플로우 구성
* **[.github/workflows/update_data.yml](file:///c:/Users/student/Documents/etf-eda/.github/workflows/update_data.yml)**
  * 매 1시간마다(`cron: "0 * * * *"`) 가상환경(`uv` 활용)을 통해 `fetch_etf.py` 수집 스크립트를 자동 구동합니다.
  * 최신 데이터를 업데이트한 후 변경 사항이 있을 때만 `github-actions[bot]` 계정을 사용해 저장소에 자동으로 커밋 및 푸시합니다.
  * 쓰기 권한(`contents: write`)이 포함되어 있습니다.

---

## 🔍 로컬 테스트 및 확인 방법

브라우저 에이전트 자동 테스트 환경(Playwright)의 외부 라이브러리 서버 장애로 인해, 에이전트 측에서 스크린샷 캡처 테스트를 최종 수행하지 못했습니다. 대신 **로컬 웹 서버가 현재 포트 `8000`번에서 실행 중**이므로 사용자의 웹 브라우저에서 직접 아래 주소에 접속하여 결과를 확인하실 수 있습니다.

* **로컬 대시보드 접속 주소**: [http://127.0.0.1:8000](http://127.0.0.1:8000)

> [!TIP]
> 1. 브라우저로 위 주소에 접속하여 대시보드가 정상적으로 출력되는지 확인합니다.
> 2. 우측 상단의 ☀️/🌙 아이콘을 클릭하여 테마 전환이 매끄럽게 작동하는지, 차트 테마도 잘 연동되는지 확인합니다.
> 3. 상세 리스트 테이블의 검색창에 'TIGER' 혹은 'KODEX'를 입력하여 결과가 필터링되며 차트들이 즉시 재렌더링되는지 확인합니다.

---

## 🚀 GitHub Pages 배포 가이드

원격 저장소에 대시보드를 배포하기 위해 아래 단계를 따릅니다:

1. **GitHub Actions 권한 설정**:
   * GitHub 저장소 페이지의 **[Settings] -> [Actions] -> [General]**로 이동합니다.
   * **Workflow permissions** 섹션에서 **`Read and write permissions`**를 선택하고 저장합니다. (GitHub Actions가 데이터를 업데이트하여 푸시할 수 있게 하기 위함)

2. **GitHub Pages 활성화**:
   * GitHub 저장소 페이지의 **[Settings] -> [Pages]**로 이동합니다.
   * **Build and deployment** 섹션의 Source를 **`Deploy from a branch`**로 지정합니다.
   * Branch를 **`main`** 브랜치, 폴더를 **`/(root)`**로 선택한 후 **[Save]** 버튼을 누릅니다.

3. **최종 코드 푸시**:
   * 로컬의 최신 변경사항을 GitHub에 최종 커밋 및 푸시합니다.
   * 잠시 후 GitHub Pages에 배포가 완료되어 `https://<사용자이름>.github.io/etf-eda/` 주소를 통해 전 세계 어디서든 대시보드를 조회할 수 있습니다.
