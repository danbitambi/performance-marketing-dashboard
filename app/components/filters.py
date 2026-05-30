"""페이지 공용 사이드바 필터 (session_state로 상태 유지)"""
import streamlit as st

CHANNEL_LABELS = {"google": "구글", "meta": "메타", "naver": "네이버", "tiktok": "틱톡"}


def sidebar_filters(df, *, show_creative=False, show_category=False):
    """
    공용 사이드바 필터를 렌더링하고 선택값을 반환.
    반환: dict(channels, date_range, creative_types, categories)
    """
    all_channels = sorted(df["channel"].unique())
    all_dates = sorted(df["date"].unique())
    all_types = sorted(df["creative_type"].unique())
    all_cats = sorted(df["category"].unique())

    # 기본값 초기화 (최초 1회) — key만 쓰는 위젯이 session_state에서 값을 읽음
    st.session_state.setdefault("f_channels", all_channels)
    st.session_state.setdefault("f_date_range", (all_dates[0], all_dates[-1]))
    st.session_state.setdefault("f_types", all_types)
    st.session_state.setdefault("f_cats", all_cats)

    with st.sidebar:
        st.header("🔎 필터")

        channels = st.multiselect(
            "채널", all_channels,
            format_func=lambda c: CHANNEL_LABELS.get(c, c),
            key="f_channels",
        )

        date_range = st.date_input(
            "기간",
            min_value=all_dates[0], max_value=all_dates[-1],
            key="f_date_range",
        )

        creative_types = None
        if show_creative:
            creative_types = st.multiselect("소재 타입", all_types, key="f_types")

        categories = None
        if show_category:
            categories = st.multiselect("카테고리", all_cats, key="f_cats")

        st.divider()
        st.caption(f"📅 {all_dates[0]} ~ {all_dates[-1]}")
        st.caption("AppsFlyer × 채널 조인 데이터")

    # 날짜 단일 선택 방어
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        dr = (date_range[0], date_range[1])
    else:
        dr = st.session_state["f_date_range"]

    if not channels:
        channels = all_channels

    return {
        "channels": channels,
        "date_range": dr,
        "creative_types": creative_types,
        "categories": categories,
    }
