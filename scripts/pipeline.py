"""
전체 파이프라인 실행 진입점.
python -m scripts.pipeline
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.ingest.load_channel import load_channel_data
from scripts.ingest.load_appsflyer import load_appsflyer_data
from scripts.transform.join_and_process import join_and_process, save_processed
from scripts.utils.logger import get_logger

logger = get_logger("pipeline")


def run_pipeline() -> str:
    logger.info("=== 파이프라인 시작 ===")

    logger.info("[1/3] 채널 데이터 로딩")
    ch = load_channel_data()

    logger.info("[2/3] AppsFlyer 데이터 로딩")
    af = load_appsflyer_data()

    logger.info("[3/3] 조인 및 전처리")
    master = join_and_process(ch, af)

    path = save_processed(master, "master")
    logger.info("=== 파이프라인 완료: %s ===", path)
    return path


if __name__ == "__main__":
    run_pipeline()
