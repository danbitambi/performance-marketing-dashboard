"""
AppsFlyer 원본 데이터 로딩 및 컬럼 정규화.
"""
import glob
import pandas as pd
from scripts.utils.logger import get_logger

logger = get_logger(__name__)

COLUMN_MAP = {
    "일": "date",
    "미디어소스": "media_source",
    "캠페인": "campaign",
    "그룹": "adgroup",
    "소재": "ad_name",
    "클릭": "clicks_af",
    "회원가입": "installs",
    "구매": "purchases_af",
    "구매매출": "revenue_krw_af",
}

MEDIA_SOURCE_TO_CHANNEL = {
    "googleadwords_int": "google",
    "Facebook Ads": "meta",
    "naver_search": "naver",
    "tiktok_int": "tiktok",
}


def load_appsflyer_data(data_dir: str = "data/raw/appsflyer") -> pd.DataFrame:
    files = sorted(glob.glob(f"{data_dir}/*.csv"))
    if not files:
        logger.error("AF 데이터 파일 없음: %s", data_dir)
        raise FileNotFoundError(f"No appsflyer files in {data_dir}")

    frames = []
    for f in files:
        try:
            df = pd.read_csv(f, encoding="utf-8-sig")
            frames.append(df)
        except Exception as e:
            logger.warning("파일 로딩 실패: %s (%s)", f, e)

    logger.info("AF 파일 %d개 로딩 완료", len(frames))
    raw = pd.concat(frames, ignore_index=True)

    raw.columns = raw.columns.str.strip()
    df = raw.rename(columns=COLUMN_MAP)

    # 채널 컬럼 추가 (조인 키용)
    df["channel"] = df["media_source"].map(MEDIA_SOURCE_TO_CHANNEL).fillna(df["media_source"])

    df["date"] = pd.to_datetime(df["date"]).dt.date

    for col in ["clicks_af", "installs", "purchases_af", "revenue_krw_af"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    logger.info("AF 데이터 로딩 완료: %s rows", len(df))
    return df
