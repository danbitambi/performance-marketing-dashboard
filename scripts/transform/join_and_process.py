"""
채널 + AppsFlyer 조인 및 전처리 파이프라인.
조인 키: date + channel + campaign + adgroup + ad_name
"""
import os
import pandas as pd
from scripts.utils.logger import get_logger
from scripts.utils.creative_parser import parse_creative_column

logger = get_logger(__name__)

JOIN_KEYS = ["date", "channel", "campaign", "adgroup", "ad_name"]
UNMATCHED_DIR = "data/unmatched"
PROCESSED_DIR = "data/processed"


def join_and_process(ch: pd.DataFrame, af: pd.DataFrame) -> pd.DataFrame:
    """채널 + AF 조인 후 KPI 계산까지 완료된 마스터 DataFrame 반환."""
    os.makedirs(UNMATCHED_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # AF에서 조인에 필요한 컬럼만 선택
    af_cols = JOIN_KEYS + ["clicks_af", "installs", "purchases_af", "revenue_krw_af"]
    af_join = af[[c for c in af_cols if c in af.columns]].copy()

    merged = ch.merge(af_join, on=JOIN_KEYS, how="left")

    # 미매칭 처리
    unmatched_mask = merged["installs"].isna()
    unmatched_count = unmatched_mask.sum()
    total = len(merged)

    if unmatched_count > 0:
        unmatched_ratio = unmatched_count / total
        if unmatched_ratio > 0.20:
            logger.warning("미매칭 비율 %.1f%% (기준 20%% 초과)", unmatched_ratio * 100)
        else:
            logger.info("AF 미매칭: %d건 (%.1f%%)", unmatched_count, unmatched_ratio * 100)

        # 미매칭 row 저장
        dates = merged.loc[unmatched_mask, "date"].astype(str).unique()
        for d in dates:
            day_unmatched = merged[(unmatched_mask) & (merged["date"].astype(str) == d)]
            path = f"{UNMATCHED_DIR}/unmatched_{d.replace('-','')}.csv"
            day_unmatched.to_csv(path, index=False, encoding="utf-8-sig")

    # 미매칭 수치 → 0
    for col in ["clicks_af", "installs", "purchases_af", "revenue_krw_af"]:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    # AF 역방향 미매칭 확인 (AF에만 있는 row)
    af_only = af_join[~af_join.set_index(JOIN_KEYS).index.isin(ch.set_index(JOIN_KEYS).index)]
    if not af_only.empty:
        logger.warning("AF에만 있는 row: %d건 → unmatched 저장", len(af_only))
        af_only.to_csv(f"{UNMATCHED_DIR}/af_only_unmatched.csv", index=False, encoding="utf-8-sig")

    # 소재명 파싱
    parsed = parse_creative_column(merged["ad_name"])
    merged = pd.concat([merged, parsed], axis=1)

    # spend=0 행 플래그 (집계 제외용, 데이터는 유지)
    merged["exclude_from_insight"] = (merged["spend_krw"] == 0) | merged["is_test"].fillna(False)

    # KPI 계산
    merged = _calc_kpis(merged)

    logger.info("조인 완료: %d rows", len(merged))
    return merged


def _calc_kpis(df: pd.DataFrame) -> pd.DataFrame:
    eps = 1e-9  # 0 나누기 방지

    df["roas"] = df["revenue_krw_af"] / (df["spend_krw"] + eps)
    df["cpi_krw"] = df["spend_krw"] / (df["installs"] + eps)
    df["ctr"] = df["clicks"] / (df["impressions"] + eps)
    df["cvr"] = df["installs"] / (df["clicks"] + eps)
    df["cpc_krw"] = df["spend_krw"] / (df["clicks"] + eps)
    df["cpm_krw"] = df["spend_krw"] / (df["impressions"] + eps) * 1000

    # spend=0이면 KPI 의미 없음 → NaN
    zero_spend = df["spend_krw"] == 0
    for col in ["roas", "cpi_krw", "cpc_krw", "cpm_krw"]:
        df.loc[zero_spend, col] = None

    return df


def save_processed(df: pd.DataFrame, date_str: str = "all") -> str:
    path = f"{PROCESSED_DIR}/processed_{date_str}.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info("전처리 결과 저장: %s", path)
    return path
