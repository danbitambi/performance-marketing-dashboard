"""Streamlit 공용 데이터 로더 (캐싱 포함)"""
import os
import sys
import pandas as pd
import streamlit as st

# 프로젝트 루트 기준 절대경로 (실행 위치와 무관하게 동작)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
MASTER_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "processed_master.csv")


@st.cache_data(ttl=300)
def load_master() -> pd.DataFrame:
    """전처리 마스터 로딩. 없으면 파이프라인을 먼저 실행."""
    if not os.path.exists(MASTER_PATH):
        from scripts.pipeline import run_pipeline
        run_pipeline()
    df = pd.read_csv(MASTER_PATH, parse_dates=["date"])
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def get_filtered(
    df: pd.DataFrame,
    channels: list,
    date_range: tuple,
    creative_types: list | None = None,
    categories: list | None = None,
) -> pd.DataFrame:
    """사이드바 필터를 적용한 분석용 DataFrame 반환 (집계 제외 행 제거)."""
    mask = (
        (~df["exclude_from_insight"])
        & (df["channel"].isin(channels))
        & (df["date"] >= date_range[0])
        & (df["date"] <= date_range[1])
    )
    if creative_types:
        mask &= df["creative_type"].isin(creative_types)
    if categories:
        mask &= df["category"].isin(categories)
    return df[mask].copy()
