"""
인사이트 집계 모듈.
분석 대상: spend>0, is_test=False, creative_type!='UNKNOWN' (별도 시트 분리)
"""
import pandas as pd
from scripts.utils.logger import get_logger

logger = get_logger(__name__)


def get_analysis_df(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(분석용 df, unknown 소재 df) 반환"""
    valid = df[~df["exclude_from_insight"]].copy()
    unknown = valid[valid["creative_type"] == "UNKNOWN"].copy()
    valid = valid[valid["creative_type"] != "UNKNOWN"].copy()
    logger.info("분석 대상: %d rows, UNKNOWN 소재: %d rows", len(valid), len(unknown))
    return valid, unknown


def agg_by_channel(df: pd.DataFrame) -> pd.DataFrame:
    """채널별 KPI 집계"""
    return (
        df.groupby("channel")
        .agg(
            spend_krw=("spend_krw", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            installs=("installs", "sum"),
            revenue_krw=("revenue_krw_af", "sum"),
            purchases=("purchases_af", "sum"),
        )
        .assign(
            roas=lambda x: x["revenue_krw"] / x["spend_krw"].replace(0, float("nan")),
            cpi_krw=lambda x: x["spend_krw"] / x["installs"].replace(0, float("nan")),
            ctr=lambda x: x["clicks"] / x["impressions"].replace(0, float("nan")),
            cpc_krw=lambda x: x["spend_krw"] / x["clicks"].replace(0, float("nan")),
            cpm_krw=lambda x: x["spend_krw"] / x["impressions"].replace(0, float("nan")) * 1000,
        )
        .reset_index()
    )


def agg_by_creative_type(df: pd.DataFrame) -> pd.DataFrame:
    """소재 타입별 KPI 집계"""
    return (
        df.groupby(["channel", "creative_type"])
        .agg(
            spend_krw=("spend_krw", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            installs=("installs", "sum"),
            revenue_krw=("revenue_krw_af", "sum"),
        )
        .assign(
            ctr=lambda x: x["clicks"] / x["impressions"].replace(0, float("nan")),
            cvr=lambda x: x["installs"] / x["clicks"].replace(0, float("nan")),
            roas=lambda x: x["revenue_krw"] / x["spend_krw"].replace(0, float("nan")),
        )
        .reset_index()
    )


def agg_ab_test(df: pd.DataFrame) -> pd.DataFrame:
    """AB 테스트 결과 (A vs B 비교)"""
    ab = df[df["ab_flag"].isin(["A", "B"])].copy()
    return (
        ab.groupby(["channel", "category", "ab_flag"])
        .agg(
            spend_krw=("spend_krw", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            installs=("installs", "sum"),
            revenue_krw=("revenue_krw_af", "sum"),
        )
        .assign(
            ctr=lambda x: x["clicks"] / x["impressions"].replace(0, float("nan")),
            cvr=lambda x: x["installs"] / x["clicks"].replace(0, float("nan")),
            roas=lambda x: x["revenue_krw"] / x["spend_krw"].replace(0, float("nan")),
            cpi_krw=lambda x: x["spend_krw"] / x["installs"].replace(0, float("nan")),
        )
        .reset_index()
    )


def agg_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """카테고리별 KPI 집계"""
    return (
        df.groupby(["channel", "category"])
        .agg(
            spend_krw=("spend_krw", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            installs=("installs", "sum"),
            revenue_krw=("revenue_krw_af", "sum"),
        )
        .assign(
            roas=lambda x: x["revenue_krw"] / x["spend_krw"].replace(0, float("nan")),
            cpi_krw=lambda x: x["spend_krw"] / x["installs"].replace(0, float("nan")),
            ctr=lambda x: x["clicks"] / x["impressions"].replace(0, float("nan")),
        )
        .reset_index()
    )


def agg_daily_trend(df: pd.DataFrame) -> pd.DataFrame:
    """일별 트렌드 (채널별)"""
    return (
        df.groupby(["date", "channel"])
        .agg(
            spend_krw=("spend_krw", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            installs=("installs", "sum"),
            revenue_krw=("revenue_krw_af", "sum"),
        )
        .assign(
            roas=lambda x: x["revenue_krw"] / x["spend_krw"].replace(0, float("nan")),
            ctr=lambda x: x["clicks"] / x["impressions"].replace(0, float("nan")),
        )
        .reset_index()
        .sort_values("date")
    )
