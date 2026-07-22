# 네이버 ETF 실시간 데이터 수집 스케줄러

## 1. 개요
네이버 금융 ETF 리스트 API(`https://finance.naver.com/api/sise/etfItemList.nhn`)로부터 1분마다 ETF 시세 및 항목 데이터를 수집하여 상대경로 `./data` 폴더에 CSV 파일 형태로 저장합니다.

## 2. 주요 파일 구성
- `src/fetch_etf.py`: ETF 데이터를 API 요청으로 가져와 CSV로 저장하는 파이썬 스크립트.
- `data/`: 수집된 CSV 데이터 파일들이 저장되는 폴더.
  - `etf_items_YYYYMMDD_HHMMSS.csv`: 각 수집 시점별 데이터.
  - `etf_items_latest.csv`: 가장 최근에 수집된 ETF 데이터.
- `.venv/`: `uv`를 통해 구축된 파이썬 가상환경.

## 3. 실행 방법 및 스케줄러
- **가상환경 실행**: `.\.venv\Scripts\python.exe src/fetch_etf.py`
- **자동 스케줄링**: `schedule` 도구를 활용하여 1분 간격(`*/1 * * * *`)으로 데이터 수집 스케줄러가 백그라운드 등록되어 실행됩니다.
