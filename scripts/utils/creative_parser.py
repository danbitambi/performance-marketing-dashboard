"""
소재명 파싱 유틸리티.
네이밍 규칙: {소재타입}_{카테고리}_{시즌}_{AB유무}_{버전}
예: VID_플러스멤버십_겨울_A_v1
    CRS_특가_겨울_v1  (AB 없는 경우)
"""
import re
import pandas as pd
from scripts.utils.logger import get_logger

logger = get_logger(__name__)

CREATIVE_TYPES = {"VID", "IMG", "CRS", "GIF", "TXT"}
AB_FLAGS = {"A", "B", "N"}
VERSION_PATTERN = re.compile(r"^v\d+$")


def parse_ad_name(ad_name: str) -> dict:
    if not isinstance(ad_name, str) or not ad_name.strip():
        logger.warning("소재명 없음 → UNKNOWN 처리")
        return _unknown()

    raw = ad_name.strip().replace("-", "_")

    if "test_" in raw.lower() or "_temp" in raw.lower():
        return {**_parse_parts(raw), "is_test": True}

    return {**_parse_parts(raw), "is_test": False}


def _parse_parts(name: str) -> dict:
    parts = name.split("_")
    if len(parts) < 3:
        logger.warning("파싱 실패 (구분자 부족): %s", name)
        return _unknown()

    creative_type = parts[0] if parts[0] in CREATIVE_TYPES else "UNKNOWN"
    if creative_type == "UNKNOWN":
        logger.warning("알 수 없는 소재타입: %s (소재: %s)", parts[0], name)

    # AB 플래그는 버전 패턴이 아닌 위치에서 탐지
    ab_flag = "N"
    category_parts = []
    season = None
    version = None

    for i, p in enumerate(parts[1:], 1):
        if p in AB_FLAGS and i == len(parts) - 2 and VERSION_PATTERN.match(parts[-1] if len(parts) > i else ""):
            ab_flag = p
        elif VERSION_PATTERN.match(p):
            version = p
        elif p in AB_FLAGS and VERSION_PATTERN.match(parts[i] if i < len(parts) - 1 else ""):
            ab_flag = p
        else:
            if season is None and i > 1:
                # 마지막 비버전 파트를 시즌으로
                category_parts.append(p)
            else:
                category_parts.append(p)

    # 간단한 규칙: parts[-1]=버전, parts[-2]=AB(있으면), 나머지=카테고리+시즌
    version = parts[-1] if VERSION_PATTERN.match(parts[-1]) else None
    remaining = parts[1: -1 if version else len(parts)]

    if remaining and remaining[-1] in AB_FLAGS:
        ab_flag = remaining[-1]
        remaining = remaining[:-1]

    season = remaining[-1] if remaining else None
    category = "_".join(remaining[:-1]) if len(remaining) > 1 else (remaining[0] if remaining else "UNKNOWN")

    return {
        "creative_type": creative_type,
        "category": category,
        "season": season,
        "ab_flag": ab_flag,
        "version": version,
    }


def _unknown() -> dict:
    return {
        "creative_type": "UNKNOWN",
        "category": "UNKNOWN",
        "season": None,
        "ab_flag": "UNKNOWN",
        "version": None,
        "is_test": False,
    }


def parse_creative_column(series: pd.Series) -> pd.DataFrame:
    """소재명 Series → 파싱 결과 DataFrame 반환"""
    parsed = series.apply(parse_ad_name)
    return pd.DataFrame(parsed.tolist(), index=series.index)
