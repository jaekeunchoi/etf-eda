"""네이버 금융 ETF 리스트 데이터를 실시간 수집 및 전처리하는 데이터 로더 모듈.

이 모듈은 네이버 금융 API를 통해 ETF 항목 데이터를 수집하고,
분석에 적합하도록 정제(컬럼 한글화, 파생변수 생성 등)하여 pandas DataFrame 형태로 제공합니다.
"""

import json
import re
from typing import Any, Dict, List, Optional
import pandas as pd
import requests

# 네이버 금융 API URL (기본 JSON 응답 및 callback 응답 모두 대비)
API_URL: str = (
    "https://finance.naver.com/api/sise/etfItemList.nhn?"
    "etfType=0&targetColumn=market_sum&sortOrder=desc"
)


def extract_json_from_jsonp(text: str) -> str:
    """JSONP 형태의 문자열에서 순수 JSON 문자열만 추출합니다.

    Args:
        text (str): API 응답으로 받은 raw 텍스트 (예: window.__jindo2_callback._7957({...})).

    Returns:
        str: 추출된 JSON 문자열.

    Raises:
        ValueError: 텍스트에서 JSON 패턴을 찾지 못할 경우 발생.
    """
    # 중괄호 { }로 감싸진 내부 데이터를 찾기 위해 정규식 적용
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("응답 텍스트에서 올바른 JSON 형식을 추출할 수 없습니다.")
    return match.group(0)


def fetch_raw_etf_data(url: str = API_URL) -> List[Dict[str, Any]]:
    """네이버 금융 API로부터 ETF 리스트 데이터를 실시간으로 가져옵니다.

    Args:
        url (str, optional): 요청할 API 주소. 기본값은 API_URL.

    Returns:
        List[Dict[str, Any]]: ETF 항목 정보 목록.

    Raises:
        requests.RequestException: HTTP 요청 실패 시 발생.
        ValueError: JSON 파싱 에러 발생 시 발생.
    """
    headers: Dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # API 요청
    response: requests.Response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    # 인코딩 설정 (네이버 금융 API는 euc-kr을 사용하므로 한글 깨짐 방지 처리)
    response.encoding = "euc-kr"
    response_text: str = response.text.strip()

    # JSONP 콜백 함수 래핑 처리 여부 확인 및 파싱
    if response_text.startswith("window.__jindo2_callback") or "(" in response_text:
        # JSONP 응답 처리
        json_str: str = extract_json_from_jsonp(response_text)
        json_data: Dict[str, Any] = json.loads(json_str)
    else:
        # 일반 JSON 응답 처리
        json_data = response.json()

    etf_list: List[Dict[str, Any]] = json_data.get("result", {}).get("etfItemList", [])
    return etf_list


def parse_brand(itemname: str) -> str:
    """ETF 종목명으로부터 자산운용사 브랜드명을 추출하여 매핑합니다.

    Args:
        itemname (str): ETF 종목명 (예: "KODEX 200").

    Returns:
        str: 운용사 브랜드명 (예: "삼성자산운용 (KODEX)").
    """
    # 대소문자 구분 없이 매칭하기 위해 종목명을 대문자로 변환 및 공백 제거된 첫 단어 위주 체크
    name_upper: str = itemname.upper().strip()
    first_word: str = name_upper.split()[0] if name_upper.split() else ""

    # 운용사 브랜드 매핑 딕셔너리 정의
    # 주요 브랜드 접두사와 이에 해당하는 정식 운용사명을 연결
    brand_map: Dict[str, str] = {
        "KODEX": "삼성자산운용 (KODEX)",
        "TIGER": "미래에셋자산운용 (TIGER)",
        "ACE": "한국투자신탁운용 (ACE)",
        "KINDEX": "한국투자신탁운용 (KINDEX)",
        "KBSTAR": "KB자산운용 (KBSTAR)",
        "RISE": "KB자산운용 (RISE)",
        "SOL": "신한자산운용 (SOL)",
        "ARIRANG": "한화자산운용 (ARIRANG)",
        "PLUS": "한화자산운용 (PLUS)",
        "HANARO": "NH-Amundi자산운용 (HANARO)",
        "WOORI": "우리자산운용 (WOORI)",
        "WON": "우리자산운용 (WON)",
        "KOACT": "삼성액티브자산운용 (KoAct)",
        "HANA": "하나자산운용 (HANA)",
        "UNICORN": "현대자산운용 (UNICORN)",
        "TIMEFOLIO": "타임폴리오자산운용 (TIMEFOLIO)",
        "HEROES": "키움투자자산운용 (HEROES)",
        "히어로즈": "키움투자자산운용 (HEROES)",
        "MASTER": "마스턴투자운용 (MASTER)",
        "TRUSTON": "트러스톤자산운용 (TRUSTON)",
        "대신": "대신자산운용 (대신)",
        "MIGHTY": "기타 (MIGHTY)",
        "마이티": "기타 (MIGHTY)",
    }

    # 첫 단어가 직접 매핑 테이블에 있는지 확인
    if first_word in brand_map:
        return brand_map[first_word]

    # 첫 단어 이외에도 종목명 전체 텍스트에 브랜드 키워드가 포함되어 있는지 검사
    for key, val in brand_map.items():
        if key in name_upper:
            return val

    # 어떤 조건에도 맞지 않으면 기타로 분류
    return "기타"


def load_realtime_etf_data(url: str = API_URL) -> pd.DataFrame:
    """실시간 ETF 데이터를 수집하고 분석에 필요한 형태로 전처리하여 DataFrame으로 반환합니다.

    Args:
        url (str, optional): 요청할 API 주소. 기본값은 API_URL.

    Returns:
        pd.DataFrame: 전처리가 완료된 ETF 데이터프레임.
    """
    raw_data: List[Dict[str, Any]] = fetch_raw_etf_data(url)
    if not raw_data:
        return pd.DataFrame()

    df: pd.DataFrame = pd.DataFrame(raw_data)

    # 1. 컬럼명 매핑 (한글 직관화)
    column_mapping: Dict[str, str] = {
        "itemcode": "종목코드",
        "itemname": "종목명",
        "nowVal": "현재가",
        "changeVal": "전일대비변동액",
        "changeRate": "등락률",
        "nav": "NAV",
        "threeMonthEarnRate": "3개월수익률",
        "quant": "거래량",
        "amonut": "거래대금(백만)",  # API 상의 오타 amonut 보정
        "marketSum": "시가총액(억)",
    }
    df = df.rename(columns=column_mapping)

    # 필요한 컬럼만 추출하여 정제
    required_cols: List[str] = list(column_mapping.values())
    # API 응답에 누락될 수 있는 컬럼 방어
    existing_cols: List[str] = [col for col in required_cols if col in df.columns]
    df = df[existing_cols]

    # 2. 데이터 타입 변환 및 결측치 처리
    numeric_cols: List[str] = ["현재가", "전일대비변동액", "등락률", "NAV", "3개월수익률", "거래량", "거래대금(백만)", "시가총액(억)"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 3. 파생변수 생성
    # (1) NAV 괴리율(%) = ((현재가 - NAV) / NAV) * 100
    if "현재가" in df.columns and "NAV" in df.columns:
        df["NAV괴리율(%)"] = ((df["현재가"] - df["NAV"]) / df["NAV"] * 100).round(2)
    else:
        df["NAV괴리율(%)"] = 0.0

    # (2) 자산운용사 분류
    if "종목명" in df.columns:
        df["운용사"] = df["종목명"].apply(parse_brand)
    else:
        df["운용사"] = "기타"

    return df


if __name__ == "__main__":
    # 모듈 자체 실행 시 데이터 조회 테스트
    try:
        test_df: pd.DataFrame = load_realtime_etf_data()
        print(f"성공적으로 {len(test_df)}개의 ETF 데이터를 수집하였습니다.")
        print(test_df.head(3))
    except Exception as e:
        print(f"데이터 로드 테스트 중 오류 발생: {e}")
