"""
채널 원본 데이터 로딩 및 컬럼 정규화.
원본 컬럼(한글) → 공통 스키마(영문 snake_case)
"""
import glob
import pandas as pd
from scripts.utils.logger import get_logger

logger = get_logger(__name__)

COLUMN_MAP = {
    "일": "date",
    "채널": "channel",
    "채널분류": "channel_type",
    "캠페인": "campaign",
    "캠페인목적": "campaign_objective",
    "그룹": "adgroup",
    "소재": "ad_name",
    "노출": "impressions",
    "클릭": "clicks",
    "비용": "spend_krw",
    "회원가입": "signups",
    "구매": "purchases_ch",
    "구매매출": "revenue_krw_ch",
}

CHANNEL_CODE_MAP = {
    "구글": "google",
    "메타": "meta",
    "네이버": "naver",
    "틱톡": "tiktok",
}


def load_channel_data(data_dir: str = "data/raw/channel") -> pd.DataFrame:
    files = sorted(glob.glob(f"{data_dir}/*.csv"))
    if not files:
        logger.error("채널 데이터 파일 없음: %s", data_dir)
        raise FileNotFoundError(f"No channel files in {data_dir}")

    frames = []
    for f in files:
        try:
            df = pd.read_csv(f, encoding="utf-8-sig")
            frames.append(df)
        except Exception as e:
            logger.warning("파일 로딩 실패: %s (%s)", f, e)

    logger.info("채널 파일 %d개 로딩 완료", len(frames))
    raw = pd.concat(frames, ignore_index=True)

    # 컬럼 정규화
    raw.columns = raw.columns.str.strip()
    df = raw.rename(columns=COLUMN_MAP)

    missing = [c for c in COLUMN_MAP.values() if c not in df.columns]
    if missing:
        logger.warning("누락 컬럼: %s", missing)

    # 채널 코드 영문화
    df["channel"] = df["channel"].map(CHANNEL_CODE_MAP).fillna(df["channel"])

    # 날짜 타입
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # 수치 결측 → 0
    for col in ["impressions", "clicks", "spend_krw", "signups", "purchases_ch", "revenue_krw_ch"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 이상값 경고
    anomaly = df[(df["impressions"] == 0) & (df["clicks"] > 0)]
    if not anomaly.empty:
        logger.warning("impressions=0 이지만 clicks>0 행: %d건", len(anomaly))

    ctr_over = df[df["impressions"] > 0].copy()
    ctr_over = ctr_over[ctr_over["clicks"] / ctr_over["impressions"] > 1]
    if not ctr_over.empty:
        logger.warning("CTR > 100%% 행: %d건", len(ctr_over))

    logger.info("채널 데이터 로딩 완료: %s rows", len(df))
    return df
