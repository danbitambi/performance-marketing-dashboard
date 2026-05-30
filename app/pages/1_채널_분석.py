import os, sys
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.data_loader import load_master, get_filtered
from app.components.filters import sidebar_filters, CHANNEL_LABELS
from scripts.insight.aggregate import agg_by_channel

st.set_page_config(page_title="채널 분석", page_icon="📡", layout="wide")
st.title("📡 채널별 성과 분석")

df = load_master()
f = sidebar_filters(df)
fdf = get_filtered(df, f["channels"], f["date_range"])

if fdf.empty:
    st.warning("선택한 조건에 데이터가 없습니다.")
    st.stop()

agg = agg_by_channel(fdf)
agg["채널"] = agg["channel"].map(CHANNEL_LABELS)

# 요약
st.subheader("전체 요약")
t = fdf.agg({"spend_krw": "sum", "impressions": "sum", "clicks": "sum",
             "installs": "sum", "revenue_krw_af": "sum"})
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("총 비용", f"₩{t['spend_krw']:,.0f}")
c2.metric("총 노출", f"{t['impressions']:,.0f}")
c3.metric("총 클릭", f"{t['clicks']:,.0f}")
c4.metric("총 설치", f"{t['installs']:,.0f}")
c5.metric("ROAS", f"{t['revenue_krw_af']/max(t['spend_krw'],1):.2f}x")

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("채널별 ROAS")
    fig = px.bar(agg.sort_values("roas", ascending=False), x="채널", y="roas",
                 color="채널", text_auto=".2f")
    fig.update_layout(showlegend=False, height=350, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("채널별 CPI (₩)")
    fig = px.bar(agg.sort_values("cpi_krw"), x="채널", y="cpi_krw",
                 color="채널", text_auto=",.0f")
    fig.update_layout(showlegend=False, height=350, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    st.subheader("채널별 CTR")
    agg["ctr_pct"] = agg["ctr"] * 100
    fig = px.bar(agg.sort_values("ctr_pct", ascending=False), x="채널", y="ctr_pct",
                 color="채널", text_auto=".2f")
    fig.update_layout(showlegend=False, height=350, margin=dict(t=10),
                      yaxis_title="CTR (%)")
    st.plotly_chart(fig, use_container_width=True)
with col4:
    st.subheader("채널별 비용 구성")
    fig = px.pie(agg, names="채널", values="spend_krw", hole=0.4)
    fig.update_layout(height=350, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

st.subheader("채널별 상세 지표")
cols = {"채널": "채널", "spend_krw": "비용(₩)", "impressions": "노출", "clicks": "클릭",
        "installs": "설치", "revenue_krw": "매출(₩)", "roas": "ROAS",
        "cpi_krw": "CPI(₩)", "ctr": "CTR", "cpc_krw": "CPC(₩)", "cpm_krw": "CPM(₩)"}
show = agg[[c for c in cols if c in agg.columns]].rename(columns=cols)
st.dataframe(
    show.style.format({
        "비용(₩)": "{:,.0f}", "노출": "{:,.0f}", "클릭": "{:,.0f}", "설치": "{:,.0f}",
        "매출(₩)": "{:,.0f}", "ROAS": "{:.2f}", "CPI(₩)": "{:,.0f}",
        "CTR": "{:.2%}", "CPC(₩)": "{:,.0f}", "CPM(₩)": "{:,.0f}"}),
    use_container_width=True, hide_index=True,
)
st.download_button("⬇️ 채널 집계 CSV 다운로드", show.to_csv(index=False).encode("utf-8-sig"),
                   "channel_summary.csv", "text/csv")
