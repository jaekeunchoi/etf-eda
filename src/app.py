"""네이버 금융 ETF 실시간 데이터를 시각화하고 심층 분석하는 Streamlit 대시보드 애플리케이션.

이 모듈은 데이터 수집 모듈을 호출하여 실시간으로 가공된 데이터를 가져온 후,
Streamlit을 활용해 대화형 차트(Plotly), KPI 카드, 운용사별 점유율, 상세 종목 진단 등
종합적인 탐색적 데이터 분석(EDA) 대시보드를 제공합니다.
"""

import os
import sys
from typing import List

# 프로젝트 루트 디렉토리를 sys.path에 추가하여 src 모듈을 정상적으로 인식하도록 보정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_realtime_etf_data

# Streamlit 기본 설정 및 테마 세팅
st.set_page_config(
    page_title="실시간 네이버 금융 ETF 종합 EDA 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 20년차 데이터 분석가 스타일의 CSS 커스텀 스타일링 추가
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 1.2rem;
        border-radius: 0.5rem;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        font-size: 0.9rem;
        color: #6B7280;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #111827;
        margin-top: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)  # 60초 캐싱을 통해 과도한 API 호출 방지 및 속도 향상
def get_cached_etf_data() -> pd.DataFrame:
    """실시간 ETF 데이터를 로드하고 캐싱하는 함수.

    Returns:
        pd.DataFrame: 실시간 수집 및 전처리 완료된 ETF 데이터프레임.
    """
    return load_realtime_etf_data()


def display_metrics(df: pd.DataFrame) -> None:
    """데이터프레임의 요약 지표를 화면 상단에 렌더링합니다.

    Args:
        df (pd.DataFrame): 분석 대상이 되는 필터링 전 또는 필터링 후의 ETF 데이터프레임.
    """
    total_count: int = len(df)
    total_market_sum_trillion: float = df["시가총액(억)"].sum() / 10000.0  # 억 단위를 조 단위로 변환
    total_quant_million: float = df["거래대금(백만)"].sum() / 1000.0  # 백만 단위를 십억(10억) 단위로 변환

    # 당일 등락 현황 분석
    up_count: int = len(df[df["등락률"] > 0])
    down_count: int = len(df[df["등락률"] < 0])

    up_ratio: float = (up_count / total_count * 100) if total_count > 0 else 0.0
    avg_return_3m: float = df["3개월수익률"].mean()

    # Streamlit 레이아웃 열 분할
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            f"""
            <div class='metric-card' style='border-left-color: #3B82F6;'>
                <div class='metric-title'>📈 총 상장 종목 수</div>
                <div class='metric-value'>{total_count:,} 개</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class='metric-card' style='border-left-color: #10B981;'>
                <div class='metric-title'>💰 총 시가총액 합계</div>
                <div class='metric-value'>{total_market_sum_trillion:.2f} 조 원</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class='metric-card' style='border-left-color: #8B5CF6;'>
                <div class='metric-title'>📊 총 거래대금 합계</div>
                <div class='metric-value'>{total_quant_million:.1f} 십억 원</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        # 등락 종목 비율에 따라 카드 테두리 색상 분기 처리
        color = "#EF4444" if up_count < down_count else "#10B981"
        st.markdown(
            f"""
            <div class='metric-card' style='border-left-color: {color};'>
                <div class='metric-title'>⚖️ 당일 상승/하락 비율</div>
                <div class='metric-value'>🔺 {up_ratio:.1f}% / 🔻 {100-up_ratio:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col5:
        # 3개월 평균 수익률 음수/양수에 따른 색상 처리
        color_3m = "#EF4444" if avg_return_3m < 0 else "#10B981"
        st.markdown(
            f"""
            <div class='metric-card' style='border-left-color: {color_3m};'>
                <div class='metric-title'>📅 3개월 평균 수익률</div>
                <div class='metric-value' style='color: {color_3m};'>{avg_return_3m:.2f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def make_market_tab(df: pd.DataFrame) -> None:
    """시장 요약 및 운용사 점유율 분석 탭의 UI와 차트를 생성합니다.

    Args:
        df (pd.DataFrame): 필터링된 ETF 데이터프레임.
    """
    st.subheader("🏢 운용사별 시장 점유율 및 현황")

    # 데이터 집계: 운용사별 종목 수 및 시가총액
    agg_df = (
        df.groupby("운용사")
        .agg(
            종목수=("종목명", "count"),
            시가총액합계_억=("시가총액(억)", "sum"),
            평균3개월수익률=("3개월수익률", "mean"),
        )
        .reset_index()
    )

    agg_df["시가총액비율(%)"] = (agg_df["시가총액합계_억"] / agg_df["시가총액합계_억"].sum() * 100).round(2)
    agg_df = agg_df.sort_values(by="시가총액합계_억", ascending=False)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("##### 1. 운용사별 시가총액 점유율 (Treemap)")
        # Treemap은 계층구조 시각화 및 점유율 파악에 우수한 차트임
        fig_tree = px.treemap(
            df,
            path=["운용사", "종목명"],
            values="시가총액(억)",
            color="등락률",
            color_continuous_scale="RdBu",
            color_continuous_midpoint=0,
            title="운용사 및 종목별 시가총액 분포 (색상: 당일 등락률)",
        )
        fig_tree.update_layout(margin=dict(t=30, l=10, r=10, b=10))
        st.plotly_chart(fig_tree, use_container_width=True)

    with col2:
        st.markdown("##### 2. 운용사별 시가총액 및 종목수 집계")
        # 깔끔하게 요약된 데이터 표 표출
        display_df = agg_df.copy()
        display_df["시가총액합계_조"] = (display_df["시가총액합계_억"] / 10000.0).round(3)
        display_df = display_df.rename(
            columns={
                "종목수": "상장 종목수 (개)",
                "시가총액합계_조": "시가총액 합계 (조 원)",
                "평균3개월수익률": "3개월 평균 수익률 (%)",
            }
        )
        st.dataframe(
            display_df[["운용사", "상장 종목수 (개)", "시가총액 합계 (조 원)", "시가총액비율(%)", "3개월 평균 수익률 (%)"]],
            hide_index=True,
            use_container_width=True,
        )

    st.markdown("---")

    col3, col4 = st.columns([1, 1])

    with col3:
        st.markdown("##### 3. 운용사별 상장 종목 수 비교")
        fig_bar_count = px.bar(
            agg_df.sort_values(by="종목수", ascending=False),
            x="운용사",
            y="종목수",
            text="종목수",
            color="종목수",
            color_continuous_scale="Blues",
            labels={"종목수": "종목 수(개)"},
        )
        fig_bar_count.update_layout(showlegend=False)
        st.plotly_chart(fig_bar_count, use_container_width=True)

    with col4:
        st.markdown("##### 4. 운용사별 3개월 평균 수익률 비교")
        fig_bar_return = px.bar(
            agg_df.sort_values(by="평균3개월수익률", ascending=False),
            x="운용사",
            y="평균3개월수익률",
            text=agg_df["평균3개월수익률"].apply(lambda x: f"{x:.2f}%"),
            color="평균3개월수익률",
            color_continuous_scale="RdYlGn",
            labels={"평균3개월수익률": "평균 수익률(%)"},
        )
        st.plotly_chart(fig_bar_return, use_container_width=True)

    # 20년차 데이터 분석가의 심층 인사이트
    st.info(
        "💡 **20년차 데이터 분석가의 시장 요약 Insight**\n\n"
        "현재 국내 ETF 시장은 삼성자산운용(KODEX)과 미래에셋자산운용(TIGER) 양강 구도를 형성하고 있으며, "
        "두 회사의 시가총액 점유율 합계가 시장 대부분을 차지하고 있습니다. "
        "최근 들어 한국투자신탁운용(ACE) 및 신한자산운용(SOL) 등의 공격적인 라인업 확장이 눈에 띄며, "
        "브랜드 리브랜딩(예: 한화 PLUS, KB RISE)을 통해 시장 점유율 확보 경쟁이 가속화되고 있습니다. "
        "3개월 평균 수익률 측면에서는 자산 운용사별로 집중하는 테마(반도체, 빅테크, 채권, 배당형 등)의 단기 성과에 따라 "
        "성과 차이가 확연히 드러나는 경향을 보입니다."
    )


def make_rank_tab(df: pd.DataFrame) -> None:
    """순위 분석(Rankings) 탭의 UI와 차트를 생성합니다.

    Args:
        df (pd.DataFrame): 필터링된 ETF 데이터프레임.
    """
    st.subheader("🏆 시장 부문별 TOP 10 순위 분석")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 1. 시가총액 TOP 10")
        top_market = df.nlargest(10, "시가총액(억)")
        fig_market = px.bar(
            top_market,
            x="시가총액(억)",
            y="종목명",
            orientation="h",
            text="시가총액(억)",
            color="시가총액(억)",
            color_continuous_scale="Viridis",
        )
        fig_market.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_market, use_container_width=True)

    with col2:
        st.markdown("##### 2. 거래대금 TOP 10 (당일 기준)")
        top_volume = df.nlargest(10, "거래대금(백만)")
        fig_volume = px.bar(
            top_volume,
            x="거래대금(백만)",
            y="종목명",
            orientation="h",
            text="거래대금(백만)",
            color="거래대금(백만)",
            color_continuous_scale="Plasma",
        )
        fig_volume.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_volume, use_container_width=True)

    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("##### 3. 당일 등락률 상위 TOP 10 (상승률)")
        top_rise = df.nlargest(10, "등락률")
        fig_rise = px.bar(
            top_rise,
            x="등락률",
            y="종목명",
            orientation="h",
            text=top_rise["등락률"].apply(lambda x: f"+{x:.2f}%"),
            color="등락률",
            color_continuous_scale="Reds",
        )
        fig_rise.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_rise, use_container_width=True)

    with col4:
        st.markdown("##### 4. 당일 등락률 하위 TOP 10 (하락률)")
        top_fall = df.nsmallest(10, "등락률")
        fig_fall = px.bar(
            top_fall,
            x="등락률",
            y="종목명",
            orientation="h",
            text=top_fall["등락률"].apply(lambda x: f"{x:.2f}%"),
            color="등락률",
            color_continuous_scale="IceFire",
        )
        fig_fall.update_layout(yaxis={"categoryorder": "total descending"})  # 하락폭이 가장 큰 것이 위로
        st.plotly_chart(fig_fall, use_container_width=True)

    # 20년차 데이터 분석가의 심층 인사이트
    st.info(
        "💡 **20년차 데이터 분석가의 순위 분석 Insight**\n\n"
        "시가총액 최상위권은 주로 국내 대표 지수(KOSPI 200, KOSDAQ 150)를 추종하는 패시브 대형 상품들이 확고히 자리 잡고 있습니다. "
        "그러나 일일 거래대금 순위는 이와 상이하게 움직입니다. 주로 당일 거래대금 상위권은 레버리지, 인버스 혹은 해외 빅테크/반도체 레버리지 "
        "상품들과 같이 변동성이 큰 파생 상품 및 트렌디한 테마형 액티브 ETF에 쏠리는 현상이 두드러집니다. "
        "일일 등락률 상위/하위 종목을 통해 현재 거시 경제 이벤트와 섹터 순환매가 어떤 방향으로 격렬히 움직이고 있는지 즉각적으로 파악할 수 있으며, "
        "일시적인 테마 과열 및 낙폭과대 반발매수 유입 가능성을 탐색할 수 있습니다."
    )


def make_eda_tab(df: pd.DataFrame) -> None:
    """분포 및 관계 분석(EDA) 탭의 UI와 차트를 생성합니다.

    Args:
        df (pd.DataFrame): 필터링된 ETF 데이터프레임.
    """
    st.subheader("📊 데이터 분포 및 다차원 관계 탐색 (EDA)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 1. 3개월 수익률 분포 (Histogram & KDE)")
        valid_returns = df["3개월수익률"].dropna()
        if not valid_returns.empty:
            fig_hist = px.histogram(
                df,
                x="3개월수익률",
                nbins=50,
                marginal="box",  # 상단에 박스플롯 추가하여 다차원 분석
                color_discrete_sequence=["#3B82F6"],
                title="3개월 수익률 도수분포 및 사분위 분포",
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.warning("3개월 수익률 데이터가 유효하지 않습니다.")

    with col2:
        st.markdown("##### 2. 시가총액 대비 거래대금 관계 (Scatter Plot)")
        # 로그 스케일 변환 옵션 제공 (스케일 편차가 극심한 주식 데이터 특성 반영)
        use_log = st.checkbox("로그 스케일(Log Scale) 적용", value=True, key="scatter_log")
        fig_scatter = px.scatter(
            df,
            x="시가총액(억)",
            y="거래대금(백만)",
            color="등락률",
            size=df["현재가"].clip(lower=1000),  # 최소 크기 보정
            hover_name="종목명",
            color_continuous_scale="RdBu_r",
            color_continuous_midpoint=0,
            log_x=use_log,
            log_y=use_log,
            title="시가총액 vs 일 거래대금 분포 (원 크기: 현재가)",
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("##### 3. 수치형 변수 간 상관관계 히트맵 (Correlation Heatmap)")
        numeric_cols = ["현재가", "전일대비변동액", "등락률", "NAV", "3개월수익률", "거래량", "거래대금(백만)", "시가총액(억)", "NAV괴리율(%)"]
        corr_matrix = df[numeric_cols].corr()

        fig_heatmap = go.Figure(
            data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale="RdBu",
                zmin=-1,
                zmax=1,
                text=np.round(corr_matrix.values, 2),
                texttemplate="%{text}",
            )
        )
        fig_heatmap.update_layout(title="연속형 금융 변수 간 상관관계 매트릭스", margin=dict(t=50, l=50, r=50, b=50))
        st.plotly_chart(fig_heatmap, use_container_width=True)

    with col4:
        st.markdown("##### 4. 주요 운용사별 NAV 괴리율 분포 (Box Plot)")
        # 상위 6개 운용사 및 기타로 분류된 브랜드 대상 분석
        major_brands = df["운용사"].value_counts().nlargest(7).index.tolist()
        filtered_brand_df = df[df["운용사"].isin(major_brands)]

        fig_box = px.box(
            filtered_brand_df,
            x="운용사",
            y="NAV괴리율(%)",
            color="운용사",
            points="outliers",  # 극단적인 괴리율을 보인 이상치 즉각 식별
            title="자산운용사별 괴리율 분포 및 이상치 현황",
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # 20년차 데이터 분석가의 심층 인사이트
    st.info(
        "💡 **20년차 데이터 분석가의 통계 분석 Insight**\n\n"
        "1. **수익률 분포**: 3개월 수익률 분포의 왜도(Skewness)와 박스플롯상의 아웃라이어를 주목하십시오. 양의 꼬리가 길게 늘어져 있다면 "
        "특정 테마(레버리지 또는 원자재 등)의 초과 수익이 극단적으로 나타났음을 의미하며, 반대로 음의 영역에 긴 꼬리가 형성되면 "
        "시장 전반의 급격한 조정이나 하방 압력이 존재함을 말합니다.\n"
        "2. **시가총액과 거래대금의 멱법칙**: 산점도에서 두 변수 모두 극심한 우편향을 보여 로그 스케일을 적용했을 때 명확한 선형 경향성이 나타납니다. "
        "시가총액이 크더라도 일일 거래대금이 극단적으로 낮은 종목은 유동성 위험(슬리피지 비용 발생)을 유발할 수 있으므로 주의해야 합니다.\n"
        "3. **상관관계 해석**: 거래량과 거래대금의 높은 상관성은 당연하나, 'NAV괴리율'과 '등락률' 혹은 '거래대금' 간의 이상 상관성을 검증해야 합니다. "
        "시장의 변동성이 급증할 때 유동성공급자(LP)의 호가 제시 제한으로 인해 괴리율의 절대값이 벌어지는 현상이 Box Plot 이상치를 통해 확인됩니다."
    )


def make_table_tab(df: pd.DataFrame) -> None:
    """실시간 데이터 그리드 탭의 UI와 기능을 구현합니다.

    Args:
        df (pd.DataFrame): 필터링된 ETF 데이터프레임.
    """
    st.subheader("🗂️ 실시간 ETF 전체 데이터 시트")

    st.markdown(
        f"현재 필터 조건에 부합하는 종목 수: **{len(df):,}개** (전체 데이터에서 실시간으로 정렬 및 검색이 가능합니다.)"
    )

    # 다운로드용 CSV 포맷 변환 (메모리상 처리)
    csv_data = df.to_csv(index=False, encoding="utf-8-sig")

    # 상단 다운로드 버튼 제공
    st.download_button(
        label="📥 현재 데이터 CSV 파일 다운로드",
        data=csv_data,
        file_name="realtime_etf_data_filtered.csv",
        mime="text/csv",
    )

    # 보기 좋게 포맷팅된 데이터프레임 노출
    st.dataframe(
        df.style.format(
            {
                "현재가": "{:,.0f}원",
                "전일대비변동액": "{:+,.0f}원",
                "등락률": "{:+.2f}%",
                "NAV": "{:,.1f}원",
                "3개월수익률": "{:+.2f}%",
                "거래량": "{:,.0f}주",
                "거래대금(백만)": "{:,.0f}백만 원",
                "시가총액(억)": "{:,.0f}억 원",
                "NAV괴리율(%)": "{:+.2f}%",
            }
        ),
        use_container_width=True,
        height=500,
    )


def make_diagnosis_tab(df: pd.DataFrame) -> None:
    """개별 종목 정밀 진단 탭의 UI와 시뮬레이션을 구현합니다.

    Args:
        df (pd.DataFrame): 필터링되지 않은 전체 ETF 데이터프레임.
    """
    st.subheader("🔍 개별 ETF 종목 실시간 건강 진단 (정밀 분석)")

    # 종목 선택용 드롭다운 목록
    etf_list = [f"{row['종목코드']} | {row['종목명']}" for _, row in df.iterrows()]
    selected_etf_str = st.selectbox("진단할 ETF 종목을 선택해 주세요", etf_list)

    if selected_etf_str:
        # 코드 추출
        selected_code = selected_etf_str.split(" | ")[0]
        etf_row = df[df["종목코드"] == selected_code].iloc[0]

        # 개별 종목 정보 매핑
        name = etf_row["종목명"]
        price = etf_row["현재가"]
        nav = etf_row["NAV"]
        change = etf_row["전일대비변동액"]
        rate = etf_row["등락률"]
        return_3m = etf_row["3개월수익률"]
        volume = etf_row["거래량"]
        amount = etf_row["거래대금(백만)"]
        market_sum = etf_row["시가총액(억)"]
        discrepancy = etf_row["NAV괴리율(%)"]
        brand = etf_row["운용사"]

        # 레이아웃 구성
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown(f"#### 🏷️ `{name}` 핵심 투자 정보")

            info_df = pd.DataFrame(
                {
                    "항목": [
                        "종목코드",
                        "자산운용사",
                        "현재가 (원)",
                        "NAV (원)",
                        "전일대비 변동액",
                        "당일 등락률",
                        "시가총액",
                        "일 거래대금",
                        "3개월 수익률",
                        "실시간 괴리율",
                    ],
                    "수치 및 정보": [
                        selected_code,
                        brand,
                        f"{price:,.0f} 원",
                        f"{nav:,.1f} 원" if not pd.isna(nav) else "정보 없음",
                        f"{change:+,.0f} 원" if not pd.isna(change) else "0 원",
                        f"{rate:+.2f}%",
                        f"{market_sum:,.0f} 억 원",
                        f"{amount:,.0f} 백만 원",
                        f"{return_3m:+.2f}%" if not pd.isna(return_3m) else "정보 없음",
                        f"{discrepancy:+.2f}%" if not pd.isna(discrepancy) else "0.00%",
                    ],
                }
            )
            st.dataframe(info_df, hide_index=True, use_container_width=True)

        with col2:
            st.markdown("#### 🚨 리스크 및 밸류에이션 실시간 진단")

            # 괴리율 신호등
            discrepancy_abs = abs(discrepancy) if not pd.isna(discrepancy) else 0.0
            if discrepancy_abs >= 1.5:
                st.error(f"🔴 **괴리율 위험 상태! (절대값 {discrepancy_abs:.2f}%)**")
                discrepancy_desc = (
                    "현재 시장 거래가격이 실제 순자산가치(NAV) 대비 크게 왜곡되어 있습니다. "
                    "유동성공급자(LP)의 호가 제시 능력이 일시적으로 저하되었거나 시장 쏠림 현상이 격렬할 수 있으므로, "
                    "매수/매도 시 슬리피지 비용이 크게 발생할 위험이 있습니다. 즉각적인 거래를 피하거나 지정가 주문 활용을 강력히 권고합니다."
                )
            elif discrepancy_abs >= 0.5:
                st.warning(f"🟡 **괴리율 주의 상태 (절대값 {discrepancy_abs:.2f}%)**")
                discrepancy_desc = (
                    "괴리율이 소폭 벌어져 있습니다. 일반적인 시장 수준보다 다소 높은 상태이므로, "
                    "호가 스프레드가 벌어져 있지 않은지 호가창을 확인한 후 신중하게 진입해야 합니다."
                )
            else:
                st.success(f"🟢 **괴리율 매우 양호 (절대값 {discrepancy_abs:.2f}%)**")
                discrepancy_desc = (
                    "현재 ETF 거래가격이 순자산가치(NAV)와 밀접하게 연동되어 움직이고 있습니다. "
                    "유동성 공급이 원활하게 진행되고 있으며, 시장 가격으로 매매하더라도 자산 가치 왜곡으로 인한 불이익이 최소화됩니다."
                )

            st.write(discrepancy_desc)

            # 거래대금 유동성 평가
            st.markdown("##### 💧 유동성 평가")
            if amount < 100:  # 하루 거래대금 1억 미만
                st.error("🔴 **유동성 극도로 부족**")
                liquidity_desc = (
                    "일일 거래대금이 1억 원 미만으로 극도로 낮습니다. 원하는 가격에 대량 매매를 실행하기 매우 어렵습니다. "
                    "작은 주문에도 시세가 요동칠 수 있으므로 기관 및 거액 개인 투자자는 거래를 보류하는 편이 안전합니다."
                )
            elif amount < 1000:  # 하루 거래대금 10억 미만
                st.warning("🟡 **유동성 보통 이하**")
                liquidity_desc = (
                    "일일 거래대금이 10억 원 미만으로 다소 한정된 유동성을 가지고 있습니다. "
                    "소액 투자는 가능하나 분할 매매나 지정가 주문을 통해 리스크를 제한하십시오."
                )
            else:
                st.success("🟢 **유동성 매우 풍부**")
                liquidity_desc = (
                    f"일일 거래대금이 {amount/1000:.1f}억 원(총 {amount:,.0f}백만 원) 수준으로 매우 활발하게 거래되고 있습니다. "
                    "호가 스프레드가 좁게 촘촘하게 유지되어 시장가 주문 시에도 거래 비용 손실이 매우 적습니다."
                )
            st.write(liquidity_desc)

        st.markdown("---")
        st.markdown("#### 🧠 20년차 데이터 분석가의 종목 종합 처방전")

        # 3개월 수익률 기반 평가
        if pd.isna(return_3m):
            return_desc = "3개월 수익률 이력이 조회되지 않아 중장기 성과 추세를 파악할 수 없습니다. 신규 상장 종목인지 확인이 필요합니다."
        elif return_3m > 15:
            return_desc = (
                f"최근 3개월간 수익률이 {return_3m:.2f}%에 달해 매우 가파른 상승 추세를 달성했습니다. "
                f"시장 주도 섹터(모멘텀)의 혜택을 톡톡히 입고 있으나, 보조 지표상 이격이 과도하게 벌어져 단기적인 가격 되돌림(조정) 위험이 높습니다. "
                f"신규 매수는 분할 진입을 진지하게 고민하시고, 기존 보유자는 수익 실현 범위를 설정하는 전략이 유리합니다."
            )
        elif return_3m < -15:
            return_desc = (
                f"최근 3개월간 수익률이 {return_3m:.2f}%로 급격한 조정을 겪었습니다. "
                f"하방 모멘텀이 지배하고 있어 바닥 확인을 위한 기간 조정이 추가로 진행될 수 있습니다. "
                f"떨어지는 칼날을 잡기보다는 추세 전환 신호(이동평균 수렴 또는 양봉 거래량 수반)를 확인하고 진입하는 안전 분할 매수법이 적합합니다."
            )
        else:
            return_desc = (
                f"최근 3개월간 수익률은 {return_3m:+.2f}%로 횡보 및 완만한 수준을 유지하고 있습니다. "
                f"변동성이 제어되는 박스권 행보를 보이고 있으며, 특정 자산 배분 포트폴리오의 안정 장치 역할을 하고 있는 다수의 중성 테마일 가능성이 높습니다. "
                f"배당(분배금) 성격이 짙은 고배당 또는 채권형 ETF인지 자산 클래스를 교차 확인하시기 바랍니다."
            )

        diagnosis_report = (
            f"**[{name}]** 종목에 대한 실시간 정밀 진단 결과입니다.\n\n"
            f"1. **모멘텀 및 성과**: {return_desc}\n\n"
            f"2. **유동성 및 집행**: 거래량 {volume:,}주 및 거래대금 {amount:,.0f}백만 원 수준으로, {liquidity_desc.split('**')[1].strip()} 수준의 집행 안정성을 보이고 있습니다.\n\n"
            f"3. **가격 투명성**: 실제 자산과의 오차를 측정하는 괴리율이 {discrepancy:+.2f}%로 관측되며, {discrepancy_desc.split('**')[1].strip()} 수준으로 정상적 가치 추종이 가능합니다.\n\n"
            f"**종합 의견**: 본 ETF는 `{brand}`에서 운용하며 시가총액 `{market_sum:,.0f}억 원` 규모의 구조를 가지고 있습니다. "
            f"현재 시점의 시장 정보와 통계 지표를 고려할 때, 매매 비용 통제가 유연하므로 "
            f"{'적극적인 비중 조절' if discrepancy_abs < 0.5 and amount >= 1000 else '지정가를 활용한 신중한 접근'}이 합리적입니다."
        )
        st.write(diagnosis_report)


def main() -> None:
    """Streamlit 애플리케이션의 메인 제어 흐름 및 레이아웃을 생성합니다."""
    # 타이틀
    st.markdown("<div class='main-title'>📊 실시간 네이버 금융 ETF 종합 EDA 대시보드</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-title'>본 대시보드는 네이버 금융 API에서 제공하는 ETF 시장 데이터를 실시간으로 가져와 다차원 시각화 및 계량 분석을 수행합니다.</div>",
        unsafe_allow_html=True,
    )

    # 1. 실시간 데이터 로드
    try:
        raw_df = get_cached_etf_data()
        if raw_df.empty:
            st.error("실시간 데이터를 수집할 수 없습니다. 잠시 후 다시 시도해 주세요.")
            return
    except Exception as e:
        st.error(f"데이터 로드 중 에러 발생: {e}")
        return

    # 2. 사이드바 필터 레이아웃
    st.sidebar.header("⚙️ 데이터 필터링 설정")

    # 새로고침 버튼 (st.cache_data.clear() 호출을 유도해 실시간 호출 갱신)
    if st.sidebar.button("🔄 실시간 데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")

    # (1) 검색창 필터
    search_query = st.sidebar.text_input("🔍 종목명 / 종목코드 검색", "").strip()

    # (2) 운용사 필터
    all_brands = sorted(raw_df["운용사"].unique().tolist())
    selected_brands = st.sidebar.multiselect("🏢 자산운용사 필터 (다중 선택 가능)", all_brands, default=all_brands)

    # (3) 등락 여부 필터
    return_status = st.sidebar.radio("⚖️ 당일 등락 상태 필터", ["전체", "상승 종목만 (> 0%)", "하락 종목만 (< 0%)", "보합 (0%)"])

    # (4) 시가총액 슬라이더 필터
    min_market_cap = int(raw_df["시가총액(억)"].min())
    max_market_cap = int(raw_df["시가총액(억)"].max())
    selected_market_range = st.sidebar.slider(
        "💰 시가총액 범위 필터 (단위: 억 원)",
        min_value=min_market_cap,
        max_value=max_market_cap,
        value=(min_market_cap, max_market_cap),
    )

    # 3. 데이터 필터링 적용
    filtered_df = raw_df.copy()

    # 검색어 필터링
    if search_query:
        filtered_df = filtered_df[
            filtered_df["종목명"].str.contains(search_query, case=False)
            | filtered_df["종목코드"].str.contains(search_query, case=False)
        ]

    # 운용사 필터링
    if selected_brands:
        filtered_df = filtered_df[filtered_df["운용사"].isin(selected_brands)]
    else:
        filtered_df = pd.DataFrame(columns=filtered_df.columns)  # 아무것도 선택 안 한 경우 빈 데이터프레임

    # 등락 상태 필터링
    if return_status == "상승 종목만 (> 0%)":
        filtered_df = filtered_df[filtered_df["등락률"] > 0]
    elif return_status == "하락 종목만 (< 0%)":
        filtered_df = filtered_df[filtered_df["등락률"] < 0]
    elif return_status == "보합 (0%)":
        filtered_df = filtered_df[filtered_df["등락률"] == 0]

    # 시가총액 필터링
    filtered_df = filtered_df[
        (filtered_df["시가총액(억)"] >= selected_market_range[0])
        & (filtered_df["시가총액(억)"] <= selected_market_range[1])
    ]

    # 4. 요약 메트릭 전시
    display_metrics(filtered_df)

    st.markdown("<br>", unsafe_allow_html=True)

    # 5. 탭 구성 레이아웃
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "🏢 시장 요약 & 운용사 점유율",
            "🏆 TOP 10 순위 분석",
            "📊 분포 및 상관관계 (EDA)",
            "🗂️ 실시간 데이터 테이블",
            "🔍 개별 종목 정밀 진단",
        ]
    )

    if filtered_df.empty:
        st.warning("⚠️ 필터 조건에 일치하는 ETF 종목이 없습니다. 필터 설정을 변경해 주세요.")
        return

    with tab1:
        make_market_tab(filtered_df)

    with tab2:
        make_rank_tab(filtered_df)

    with tab3:
        make_eda_tab(filtered_df)

    with tab4:
        make_table_tab(filtered_df)

    with tab5:
        # 개별 종목 진단 탭에서는 전체 데이터를 검색하여 진단할 수 있도록 원본 raw_df 전달
        make_diagnosis_tab(raw_df)


if __name__ == "__main__":
    main()
