import os, sys
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.data_loader import load_master, get_filtered
from app.components.filters import sidebar_filters, CHANNEL_LABELS
from scripts.insight.aggregate import agg_daily_trend

st.set_page_config(page_title="일별 트렌드", page_icon="📈", layout="wide")
st.title("📈 일별 성과 트렌드")

df = load_master()
f = sidebar_filters(df)
fdf = get_filtered(df, f["channels"], f["date_range"])

if fdf.empty:
    st.warning("선택한 조건에 데이터가 없습니다.")
    st.stop()

trend = agg_daily_trend(fdf)
trend["채널"] = trend["channel"].map(CHANNEL_LABELS)

kpi_labels = {"roas": "ROAS", "ctr": "CTR", "installs": "설치수",
              "spend_krw": "비용(₩)", "revenue_krw": "매출(₩)"}
kpi = st.selectbox("메인 KPI", list(kpi_labels), format_func=lambda x: kpi_labels[x])

st.subheader(f"일별 {kpi_labels[kpi]} 추이 (채널별)")
fig = px.line(trend, x="date", y=kpi, color="채널", markers=True,
              labels={"date": "날짜"}, color_discrete_sequence=px.colors.qualitative.Set2)
fig.update_layout(height=400, margin=dict(t=10))
st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)
dt = trend.groupby("date").agg(spend_krw=("spend_krw", "sum"),
                               revenue_krw=("revenue_krw", "sum")).reset_index()
with col1:
    fig = go.Figure()
    fig.add_bar(x=dt["date"], y=dt["spend_krw"], name="비용", marker_color="#4F8EF7")
    fig.add_bar(x=dt["date"], y=dt["revenue_krw"], name="매출", marker_color="#2ECC71")
    fig.update_layout(barmode="group", height=320, margin=dict(t=30), title="일별 비용 vs 매출")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    dt["roas"] = dt["revenue_krw"] / dt["spend_krw"].replace(0, float("nan"))
    fig = px.line(dt, x="date", y="roas", markers=True, labels={"date": "날짜", "roas": "ROAS"})
    fig.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="ROAS=1")
    fig.update_layout(height=320, margin=dict(t=30), title="일별 전체 ROAS")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("채널별 일별 비용 구성")
fig = px.area(trend, x="date", y="spend_krw", color="채널",
              labels={"date": "날짜", "spend_krw": "비용(₩)"},
              color_discrete_sequence=px.colors.qualitative.Set2)
fig.update_layout(height=350, margin=dict(t=10))
st.plotly_chart(fig, use_container_width=True)
