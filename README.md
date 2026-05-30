# 📊 퍼포먼스 마케팅 대시보드

채널 광고비(Meta/Google/Naver)와 AppsFlyer 전환 데이터를 조인·정제하여
ROAS, CPI, CTR 등 핵심 KPI를 시각화하는 Streamlit 대시보드입니다.

## 주요 기능

| 페이지 | 내용 |
|--------|------|
| 📊 개요 | KPI 요약, 채널별 비용/매출 비교, 일별 ROAS 추이 |
| 📡 채널 분석 | 채널별 ROAS·CPI·CTR·비용 구성 + CSV 다운로드 |
| 🎨 소재 분석 | 소재 타입·카테고리·소재별 성과 랭킹 |
| 🔬 AB 테스트 | A안 vs B안 비교 및 승자 판별 |
| 📈 일별 트렌드 | 시계열 비용·매출·ROAS 추이 |

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run main.py
```

브라우저에서 `http://localhost:8501` 로 접속.

## 데이터 파이프라인

원본 데이터가 갱신되면 아래 명령으로 전처리 마스터를 재생성합니다.

```bash
python3 -m scripts.pipeline
```

```
data/raw/channel/*.csv  ─┐
                          ├→ 조인(date+channel+campaign+adgroup+ad_name)
data/raw/appsflyer/*.csv ─┘   → 소재명 파싱 → KPI 계산 → data/processed/processed_master.csv
```

## 폴더 구조

```
main.py                  # Streamlit 진입점 (개요 페이지)
requirements.txt
app/
├── data_loader.py       # 데이터 로딩 + 캐싱
├── components/filters.py# 공용 사이드바 필터
└── pages/               # 멀티페이지 (채널/소재/AB/트렌드)
scripts/
├── pipeline.py          # 전체 파이프라인 실행
├── ingest/              # 원본 로딩·정규화
├── transform/           # 조인·전처리
├── insight/             # KPI 집계
└── utils/               # 소재명 파싱, 로거
data/
├── raw/                 # 원본 (channel, appsflyer)
└── processed/           # 전처리 마스터
```

## 배포 (Streamlit Community Cloud)

1. [share.streamlit.io](https://share.streamlit.io) 에 GitHub 계정으로 로그인
2. **New app** → 이 저장소 / 브랜치 `main` / 메인 파일 `main.py` 선택
3. **Deploy** → `https://<앱이름>.streamlit.app` URL 발급
