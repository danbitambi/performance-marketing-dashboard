import os, sys
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.data_loader import load_master, get_filtered
from app.components.filters import sidebar_filters, CHANNEL_LABELS
from scripts.insight.aggregate import agg_ab_test

st.set_page_config(page_title="AB 테스트", page_icon="🔬", layout="wide")
st.title("🔬 AB 테스트 분석")
st.caption("A안(컨트롤) vs B안(변형) 소재 성과 비교")

df = load_master()
f = sidebar_filters(df)
fdf = get_filtered(df, f["channels"], f["date_range"])

if fdf.empty:
    st.warning("선택한 조건에 데이터가 없습니다.")
    st.stop()

ab = agg_ab_test(fdf)
if ab.empty:
    st.info("선택한 조건에 AB 테스트(A/B) 소재가 없습니다.")
    st.stop()
ab["채널"] = ab["channel"].map(CHANNEL_LABELS)

kpi_labels = {"roas": "ROAS", "ctr": "CTR", "cvr": "CVR", "cpi_krw": "CPI (₩)"}
kpi = st.radio("비교 KPI", list(kpi_labels), horizontal=True, format_func=lambda x: kpi_labels[x])

st.subheader(f"카테고리 × 채널별 A vs B — {kpi_labels[kpi]}")
fig = px.bar(ab, x="category", y=kpi, color="ab_flag", barmode="group",
             facet_col="채널", text_auto=".2f",
             color_discrete_map={"A": "#4F8EF7", "B": "#F7724F"},
             labels={"ab_flag": "안", "category": "카테고리"})
fig.update_layout(height=420, margin=dict(t=40))
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("AB 승자 판별 (ROAS 기준)")
w = ab.pivot_table(index=["채널", "category"], columns="ab_flag", values="roas").reset_index()
if "A" in w.columns and "B" in w.columns:
    def winner(r):
        a, b = r.get("A"), r.get("B")
        if pd.isna(a) or pd.isna(b):
            return "데이터부족"
        return "🅰️ A 우세" if a > b else ("🅱️ B 우세" if b > a else "동률")
    w["승자"] = w.apply(winner, axis=1)
    w["ROAS 차이(A-B)"] = (w["A"] - w["B"]).round(2)
    st.dataframe(
        w.rename(columns={"category": "카테고리"}).style.format(
            {"A": "{:.2f}", "B": "{:.2f}", "ROAS 차이(A-B)": "{:+.2f}"}),
        use_container_width=True, hide_index=True,
    )
    a_win = (w["승자"] == "🅰️ A 우세").sum()
    b_win = (w["승자"] == "🅱️ B 우세").sum()
    c1, c2 = st.columns(2)
    c1.metric("A안 우세 조합", f"{a_win}개")
    c2.metric("B안 우세 조합", f"{b_win}개")

with st.expander("전체 AB 집계 데이터"):
    st.dataframe(
        ab.drop(columns="channel").style.format({
            "spend_krw": "{:,.0f}", "revenue_krw": "{:,.0f}", "installs": "{:,.0f}",
            "roas": "{:.2f}", "ctr": "{:.2%}", "cvr": "{:.2%}", "cpi_krw": "{:,.0f}"}),
        use_container_width=True, hide_index=True,
    )
