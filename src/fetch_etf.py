"""네이버 금융 ETF 실시간 데이터를 수집 및 전처리하여 CSV 파일로 저장하는 배치 실행 모듈.

이 모듈은 src.data_loader 모듈의 실시간 전처리 로더를 활용하여
한글화된 컬럼 및 파생 변수(NAV 괴리율, 운용사 분류)를 포함한 최신 ETF 데이터를
지정된 데이터 디렉토리에 CSV 포맷으로 저장합니다.
반복 실행 옵션(--loop)을 제공하여 주기적인 자동 수집을 지원합니다.
"""

import argparse
from datetime import datetime
import os
import sys
import time
from typing import Optional
import pandas as pd

# 프로젝트 루트 디렉토리를 sys.path에 추가하여 src 모듈 임포트 오류 방지
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_realtime_etf_data


def save_to_csv(df: pd.DataFrame, output_dir: str = "data") -> Optional[str]:
    """전처리된 ETF 데이터프레임을 CSV 파일로 지정된 디렉토리에 저장합니다.

    두 가지 파일 형태로 저장됩니다:
    1. etf_items_latest.csv (최신 갱신용)
    2. etf_items_YYYYMMDD_HHMMSS.csv (이력 관리용)

    Args:
        df (pd.DataFrame): 저장할 전처리 완료된 ETF 데이터프레임.
        output_dir (str, optional): CSV 파일이 저장될 상대경로 디렉토리. 기본값은 "data".

    Returns:
        Optional[str]: 생성된 타임스탬프 CSV 파일의 상대경로, 실패 시 None.
    """
    if df.empty:
        print("[경고] 수집된 ETF 데이터가 없습니다.")
        return None

    # 저장 디렉토리가 존재하지 않는 경우 생성 (상대경로 준수)
    os.makedirs(output_dir, exist_ok=True)

    # 현재 시각 타임스탬프 생성 (YYYYMMDD_HHMMSS)
    now_str: str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 저장 파일 경로 설정
    file_path: str = os.path.join(output_dir, f"etf_items_{now_str}.csv")
    latest_file_path: str = os.path.join(output_dir, "etf_items_latest.csv")

    # CSV 파일 저장 (한글 깨짐 방지를 위해 utf-8-sig 인코딩 적용)
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    df.to_csv(latest_file_path, index=False, encoding="utf-8-sig")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 실시간 ETF 데이터를 저장했습니다:")
    print(f"  - 이력 파일: {file_path}")
    print(f"  - 최신 파일: {latest_file_path}")
    return file_path


def run_collection_cycle() -> None:
    """1회 데이터 수집 및 저장을 수행하는 단일 주기 처리 함수."""
    try:
        # 실시간 수집 및 전처리 완료된 DataFrame 로드
        df: pd.DataFrame = load_realtime_etf_data()
        save_to_csv(df)
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [오류] 데이터 수집 및 저장 실패: {e}")


def main() -> None:
    """커맨드라인 인자를 파싱하고 수집 로직(1회 실행 또는 루프 실행)을 구동하는 메인 함수."""
    parser = argparse.ArgumentParser(description="네이버 ETF 데이터 실시간 수집기")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="1분 간격 무한 루프로 실행합니다."
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="반복 수집 주기(초 단위, 기본값: 60초)"
    )

    args = parser.parse_args()

    if args.loop:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args.interval}초 간격 무한 루프 수집을 시작합니다...")
        try:
            while True:
                run_collection_cycle()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[안내] 사용자에 의해 데이터 수집 루프가 종료되었습니다.")
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 실시간 데이터 1회 수집을 시작합니다...")
        run_collection_cycle()


if __name__ == "__main__":
    main()
