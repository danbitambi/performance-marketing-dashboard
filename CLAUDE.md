# Performance Marketing Data Pipeline

## 프로젝트 개요

매일 채널 데이터(Meta/Google/TikTok 등)와 AppsFlyer 데이터를 업로드하고,
조인 및 전처리를 거쳐 퍼포먼스 마케팅 인사이트를 추출하는 파이프라인.

---

## 디렉토리 구조

```
data/
  raw/
    channel/          # 채널별 원본 파일 (절대 수정 금지)
      meta/
      google/
      tiktok/
    appsflyer/        # AppsFlyer 원본 파일 (절대 수정 금지)
  processed/          # 전처리 완료 파일
  output/             # 인사이트 결과물 (Excel, CSV)
  unmatched/          # 조인 실패 row 보관

scripts/
  ingest/             # 데이터 업로드 및 파싱
  transform/          # 전처리 및 조인
  insight/            # 인사이트 추출
  utils/              # 공통 유틸
```

---

## 데이터 소스 정의

### 채널 데이터 (Channel Data)
- **형식**: CSV, 일별 수동 업로드
- **경로**: `data/raw/channel/{source}/YYYYMMDD.csv`
- **업로드 기준**: 전일 데이터 기준 (D-1)

| 소스 | 파일 기준 | 주요 컬럼 |
|------|-----------|-----------|
| Meta | 광고 계정별 | campaign_id, adset_id, ad_id, ad_name, spend, impressions, clicks, date |
| Google | 캠페인별 | campaign_id, ad_group_id, ad_id, ad_name, cost, impressions, clicks, date |
| TikTok | 광고 계정별 | campaign_id, adgroup_id, ad_id, ad_name, spend, impressions, clicks, stat_time_day |

> 채널별 컬럼명이 다름. 조인 전 반드시 공통 스키마로 정규화할 것. (아래 컬럼 매핑 참고)

### AppsFlyer 데이터
- **형식**: CSV (Raw Data Export → Performance Report)
- **경로**: `data/raw/appsflyer/YYYYMMDD.csv`
- **Attribution window**: 클릭 7일 / 뷰스루 1일
- **주요 컬럼**: media_source, campaign, campaign_id (af_c_id), adset_id (af_adset_id), ad_id (af_ad_id), install_time, event_name, revenue, currency

---

## 채널 컬럼 정규화 매핑

조인 전 아래 기준으로 컬럼명 통일. 없는 컬럼은 NaN 처리.

| 공통 컬럼 | Meta | Google | TikTok |
|-----------|------|--------|--------|
| campaign_id | campaign_id | campaign_id | campaign_id |
| adset_id | adset_id | ad_group_id | adgroup_id |
| ad_id | ad_id | ad_id | ad_id |
| ad_name | ad_name | ad_name | ad_name |
| spend_krw | spend | cost | spend |
| impressions | impressions | impressions | impressions |
| clicks | clicks | clicks | clicks |
| date | date | date | stat_time_day |
| source | (고정값) 'meta' | (고정값) 'google' | (고정값) 'tiktok' |

---

## 소재 네이밍 컨벤션 및 파싱 규칙

### 네이밍 형식

```
{소재타입}_{AB유무}_{카테고리}_{시즌/테마}_{버전}
예시: VD_A_신발_SS25_v1
```

### 소재 타입 코드

| 코드 | 설명 |
|------|------|
| VD | 동영상 |
| IM | 이미지 (단일) |
| CA | 카루셀 |
| GI | GIF |

### AB 유무

| 코드 | 설명 |
|------|------|
| A | A안 (컨트롤) |
| B | B안 (변형) |
| N | AB 테스트 없음 |

### 카테고리 코드
<!-- TODO: 실제 상품군/카테고리 코드표 삽입 -->
| 코드 | 설명 |
|------|------|
| (예시) SH | 신발 |
| (예시) CL | 의류 |

### 파싱 규칙

```python
# 파싱 기준: ad_name.split('_')
# 인덱스: [0]=소재타입, [1]=AB유무, [2]=카테고리, [3]=시즌, [4]=버전

def parse_ad_name(ad_name):
    parts = ad_name.split('_')
    if len(parts) < 3:
        # 파싱 실패 → 경고 로그 출력 후 UNKNOWN 처리 (중단하지 말 것)
        return {'creative_type': 'UNKNOWN', 'ab_flag': 'UNKNOWN', 'category': 'UNKNOWN'}
    return {
        'creative_type': parts[0],
        'ab_flag': parts[1],
        'category': parts[2],
        'season': parts[3] if len(parts) > 3 else None,
        'version': parts[4] if len(parts) > 4 else None,
    }
```

### 예외 케이스 처리

| 상황 | 처리 방식 |
|------|-----------|
| 구분자가 `-`인 구형 소재 | `-`를 `_`로 치환 후 파싱 |
| `test_`, `_temp` 포함 소재 | is_test=True 플래그 추가, 인사이트 집계에서 제외 |
| 외부 에이전시 소재 (컨벤션 미준수) | UNKNOWN 처리, unmatched 로그에 기록 |
| 파싱 실패 | 경고 출력 후 계속 진행. 절대 임의로 값 추론하지 말 것 |

---

## KPI / 지표 정의

모든 지표는 아래 정의를 그대로 사용. 임의로 공식 변경 금지.

| 지표 | 공식 | 비고 |
|------|------|------|
| ROAS | revenue_krw / spend_krw | revenue = AF event_name='af_purchase'의 revenue 합산 |
| CPI | spend_krw / installs | installs = AF install 이벤트 수 |
| CTR | clicks / impressions | 채널 데이터 기준 |
| CVR | installs / clicks | AF installs ÷ 채널 clicks |
| CPC | spend_krw / clicks | |
| CPM | spend_krw / impressions * 1000 | |

### Revenue 환율 처리
- AppsFlyer revenue는 USD 기준
- 환율 기준: <!-- TODO: 고정환율(1,300원) 또는 당일 환율 API 사용 여부 결정 -->
- 컬럼명: `revenue_usd`, `revenue_krw` (suffix 필수)

---

## 날짜 및 타임존 기준

- **모든 날짜는 KST (UTC+9) 기준**
- AppsFlyer `install_time` 컬럼: UTC → KST 변환 후 사용
- 채널 데이터 날짜: 이미 KST 기준 (확인 필요 시 소스 대시보드와 대조)
- 날짜 포맷: `YYYY-MM-DD` (datetime이 아닌 date 타입으로 저장)
- 분석 기준일: 데이터 업로드 날짜의 전일 (D-1) 기준

---

## 데이터 조인 규칙

### 조인 키

```
채널 데이터 + AppsFlyer 데이터
조인 키: campaign_id + date
조인 타입: LEFT JOIN (채널 데이터 기준)
```

### 컬럼명 주의사항

| 채널 컬럼 | AF 컬럼 | 비고 |
|-----------|---------|------|
| campaign_id | af_c_id | 이름 다름, 값은 동일해야 함 |
| adset_id | af_adset_id | |
| ad_id | af_ad_id | |

### 미매칭 처리

- AF 미매칭 row: installs=0, revenue=0으로 채움 (누락 데이터로 표기)
- 채널 미매칭 row (AF에만 있음): `data/unmatched/YYYYMMDD_unmatched.csv`에 별도 저장
- **경고 로그 출력 후 파이프라인은 계속 진행** (중단하지 말 것)
- 미매칭 비율이 20% 초과 시 경고 메시지 출력

---

## 전처리 규칙

### 결측값 처리

| 컬럼 유형 | 처리 방식 |
|-----------|-----------|
| spend, impressions, clicks | 0으로 채움 |
| revenue | 0으로 채움 |
| ad_name | 'UNKNOWN' |
| 파싱 결과 컬럼 | 'UNKNOWN' |

### 이상값 기준
- spend가 0인 row: 인사이트 집계에서 제외 (단, 파일에는 유지)
- impressions=0이지만 clicks>0: 경고 로그 출력, 데이터는 유지
- CTR > 100%: 경고 로그 출력, 데이터는 유지 (삭제 금지)

### 금액 단위
- 모든 금액 컬럼은 suffix로 통화 명시: `_krw`, `_usd`
- 최종 아웃풋은 KRW 기준으로 통일

---

## 파일 네이밍 규칙

| 파일 종류 | 네이밍 형식 | 예시 |
|-----------|------------|------|
| 채널 원본 | `{source}_YYYYMMDD.csv` | `meta_20250522.csv` |
| AF 원본 | `appsflyer_YYYYMMDD.csv` | `appsflyer_20250522.csv` |
| 전처리 완료 | `processed_YYYYMMDD.csv` | `processed_20250522.csv` |
| 인사이트 결과 | `insight_{topic}_YYYYMMDD.xlsx` | `insight_creative_20250522.xlsx` |
| 미매칭 로그 | `unmatched_YYYYMMDD.csv` | `unmatched_20250522.csv` |

---

## 코딩 컨벤션

- **언어**: Python 3.10+
- **데이터 처리**: pandas (polars 혼용 금지)
- **컬럼명**: snake_case 통일
- **날짜 컬럼명**: `date` (단일 날짜), `start_date` / `end_date` (기간)
- **함수명**: snake_case, 동사로 시작 (예: `parse_ad_name`, `load_channel_data`)
- **경고 출력**: `logging.warning()` 사용 (print 사용 금지)
- **로그 레벨**: INFO (정상 흐름), WARNING (예외 처리), ERROR (파이프라인 중단 필요 시)

---

## 인사이트 추출 기준

### 집계 단위 (기본)
- 일별 × 채널 × 소재타입 × 카테고리 × AB여부

### 제외 조건
- is_test=True 소재
- spend=0 row
- creative_type='UNKNOWN' (별도 시트로 분리 출력)

### 인사이트 항목 (우선순위순)
1. 채널별 ROAS / CPI 비교
2. 소재 타입별 CTR / CVR
3. AB 테스트 결과 (A vs B 비교)
4. 카테고리별 성과
5. 신규 소재 vs 기존 소재 성과 비교

---

## 파이프라인 실행 순서

```
1. 데이터 업로드 확인 (data/raw/ 파일 존재 여부)
2. 채널 데이터 정규화 (컬럼 매핑)
3. AppsFlyer 데이터 타임존 변환 (UTC → KST)
4. 소재명 파싱 (ad_name → creative_type, ab_flag, category 등)
5. 채널 + AF 조인
6. 전처리 (결측값, 이상값, 환율 적용)
7. KPI 계산
8. 인사이트 집계 및 Excel 출력
9. 미매칭 로그 저장
```

---

## TODO (초기 설정 필요 항목)

- [ ] 카테고리 코드표 완성 (현재 예시만 있음)
- [ ] Revenue 환율 처리 방식 결정 (고정 vs 실시간 API)
- [ ] 채널 추가 시 컬럼 매핑표 업데이트
- [ ] 인사이트 Excel 템플릿 확정
- [ ] AppsFlyer API 연동 여부 결정 (현재 수동 업로드 가정)
