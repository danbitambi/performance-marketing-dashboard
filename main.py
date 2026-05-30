"""퍼포먼스 마케팅 대시보드 - 개요(Overview) 페이지
실행: streamlit run main.py
"""
import os, sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.data_loader import load_master, get_filtered
from app.components.filters import sidebar_filters, CHANNEL_LABELS

st.set_page_config(
    page_title="퍼포먼스 마케팅 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 스타일 ────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    [data-testid="stMetric"] {
        background: #F5F7FA;
        border: 1px solid #E6E9EF;
        border-radius: 12px;
        padding: 16px 18px;
    }
    [data-testid="stMetricLabel"] {color: #5A6275;}
</style>
""", unsafe_allow_html=True)

st.title("📊 퍼포먼스 마케팅 대시보드")
st.caption("채널 광고비 × AppsFlyer 전환 데이터 기반 통합 성과 분석")

df = load_master()
f = sidebar_filters(df)
fdf = get_filtered(df, f["channels"], f["date_range"])

if fdf.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해주세요.")
    st.stop()

# ── KPI 요약 ──────────────────────────────────────────────
spend = fdf["spend_krw"].sum()
revenue = fdf["revenue_krw_af"].sum()
installs = fdf["installs"].sum()
clicks = fdf["clicks"].sum()
impressions = fdf["impressions"].sum()
roas = revenue / spend if spend else 0
cpi = spend / installs if installs else 0
ctr = clicks / impressions if impressions else 0

st.subheader("핵심 지표")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("총 광고비", f"₩{spend/1e6:,.1f}M")
c2.metric("총 매출", f"₩{revenue/1e6:,.1f}M")
c3.metric("ROAS", f"{roas:.2f}x")
c4.metric("설치 수", f"{installs:,.0f}")
c5.metric("CPI", f"₩{cpi:,.0f}")
c6.metric("CTR", f"{ctr:.2%}")

st.divider()

# ── 채널별 비교 + 일별 추이 ───────────────────────────────
by_ch = (
    fdf.groupby("channel")
    .agg(spend=("spend_krw", "sum"), revenue=("revenue_krw_af", "sum"),
         installs=("installs", "sum"))
    .assign(roas=lambda x: x.revenue / x.spend)
    .reset_index()
)
by_ch["채널"] = by_ch["channel"].map(CHANNEL_LABELS)

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("채널별 광고비 vs 매출")
    fig = go.Figure()
    fig.add_bar(x=by_ch["채널"], y=by_ch["spend"], name="광고비", marker_color="#4F8EF7")
    fig.add_bar(x=by_ch["채널"], y=by_ch["revenue"], name="매출", marker_color="#2ECC71")
    fig.update_layout(barmode="group", height=360, margin=dict(t=10), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("채널별 ROAS")
    fig = px.bar(by_ch.sort_values("roas"), x="roas", y="채널", orientation="h",
                 text_auto=".2f", color="roas", color_continuous_scale="Blues")
    fig.update_layout(height=360, margin=dict(t=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# 일별 추이
st.subheader("일별 광고비·매출·ROAS 추이")
daily = (
    fdf.groupby("date")
    .agg(spend=("spend_krw", "sum"), revenue=("revenue_krw_af", "sum"))
    .assign(roas=lambda x: x.revenue / x.spend)
    .reset_index()
)
fig = go.Figure()
fig.add_bar(x=daily["date"], y=daily["spend"], name="광고비", marker_color="#C9D6F0")
fig.add_bar(x=daily["date"], y=daily["revenue"], name="매출", marker_color="#A8E6C2")
fig.add_trace(go.Scatter(x=daily["date"], y=daily["roas"], name="ROAS",
                         yaxis="y2", mode="lines+markers", line=dict(color="#F7724F", width=2)))
fig.update_layout(
    barmode="group", height=380, margin=dict(t=10),
    yaxis=dict(title="금액(₩)"),
    yaxis2=dict(title="ROAS", overlaying="y", side="right", showgrid=False),
    legend=dict(orientation="h", y=1.12),
)
st.plotly_chart(fig, use_container_width=True)

st.info("👈 왼쪽 사이드바에서 채널·기간을 조정하세요. 상단 페이지 메뉴에서 **채널 / 소재 / AB테스트 / 일별 트렌드** 상세 분석으로 이동할 수 있습니다.")
