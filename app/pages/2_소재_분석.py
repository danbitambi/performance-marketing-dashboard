import os, sys
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.data_loader import load_master, get_filtered
from app.components.filters import sidebar_filters, CHANNEL_LABELS
from scripts.insight.aggregate import agg_by_creative_type, agg_by_category

st.set_page_config(page_title="소재 분석", page_icon="🎨", layout="wide")
st.title("🎨 소재 성과 분석")

df = load_master()
f = sidebar_filters(df, show_creative=True, show_category=True)
fdf = get_filtered(df, f["channels"], f["date_range"], f["creative_types"], f["categories"])

if fdf.empty:
    st.warning("선택한 조건에 데이터가 없습니다.")
    st.stop()

kpi = st.radio("주요 KPI", ["roas", "ctr", "cvr", "cpi_krw"], horizontal=True,
               format_func=lambda x: {"roas": "ROAS", "ctr": "CTR", "cvr": "CVR", "cpi_krw": "CPI"}[x])

by_type = agg_by_creative_type(fdf)
by_type["채널"] = by_type["channel"].map(CHANNEL_LABELS)
by_cat = agg_by_category(fdf)
by_cat["채널"] = by_cat["channel"].map(CHANNEL_LABELS)

st.subheader("소재 타입별 성과")
col1, col2 = st.columns(2)
with col1:
    fig = px.bar(by_type.sort_values(kpi, ascending=False), x="creative_type", y=kpi,
                 color="채널", barmode="group", text_auto=".2f",
                 labels={"creative_type": "소재 타입"})
    fig.update_layout(height=380, margin=dict(t=30), title=f"소재 타입 × 채널 {kpi.upper()}")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = px.scatter(by_type, x="ctr", y="cvr", size="spend_krw", color="creative_type",
                     hover_data=["채널"], labels={"ctr": "CTR", "cvr": "CVR", "creative_type": "소재타입"})
    fig.update_layout(height=380, margin=dict(t=30), title="CTR vs CVR (버블=비용)")
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("카테고리별 성과")
col3, col4 = st.columns(2)
with col3:
    fig = px.bar(by_cat.sort_values(kpi, ascending=False), x="category", y=kpi,
                 color="채널", barmode="group", text_auto=".2f", labels={"category": "카테고리"})
    fig.update_layout(height=380, margin=dict(t=30), title=f"카테고리 × 채널 {kpi.upper()}")
    st.plotly_chart(fig, use_container_width=True)
with col4:
    fig = px.treemap(by_cat, path=["채널", "category"], values="spend_krw",
                     color=kpi, color_continuous_scale="RdYlGn")
    fig.update_layout(height=380, margin=dict(t=30), title="채널>카테고리 비용 (색=KPI)")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("소재별 성과 랭킹 (Top 20)")
ca = (
    fdf.groupby(["ad_name", "creative_type", "category", "season", "ab_flag", "channel"])
    .agg(spend_krw=("spend_krw", "sum"), installs=("installs", "sum"),
         revenue_krw=("revenue_krw_af", "sum"), clicks=("clicks", "sum"),
         impressions=("impressions", "sum"))
    .assign(roas=lambda x: x.revenue_krw / x.spend_krw.replace(0, float("nan")),
            ctr=lambda x: x.clicks / x.impressions.replace(0, float("nan")),
            cvr=lambda x: x.installs / x.clicks.replace(0, float("nan")),
            cpi_krw=lambda x: x.spend_krw / x.installs.replace(0, float("nan")))
    .reset_index().sort_values(kpi, ascending=(kpi == "cpi_krw")).head(20)
)
ca["채널"] = ca["channel"].map(CHANNEL_LABELS)
st.dataframe(
    ca.drop(columns="channel").style.format({
        "spend_krw": "{:,.0f}", "revenue_krw": "{:,.0f}", "installs": "{:,.0f}",
        "roas": "{:.2f}", "ctr": "{:.2%}", "cvr": "{:.2%}", "cpi_krw": "{:,.0f}"}),
    use_container_width=True, hide_index=True,
)
