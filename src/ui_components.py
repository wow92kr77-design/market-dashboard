from __future__ import annotations

from typing import Iterable, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


GREEN = "#16c784"
RED = "#ea3943"
YELLOW = "#f5c542"
GRAY = "#8b949e"
CARD = "#121a24"
BORDER = "#263241"


def apply_theme() -> None:
    st.set_page_config(
        page_title="국내증시 AI 터미널",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        .stApp {
            background: #08111d;
            color: #e6edf3;
        }
        [data-testid="stHeader"] {
            background: rgba(8, 17, 29, 0.86);
        }
        .main .block-container {
            padding-top: 1.4rem;
            max-width: 1500px;
        }
        .terminal-title {
            font-size: clamp(1.7rem, 3vw, 2.8rem);
            font-weight: 850;
            letter-spacing: 0;
            margin-bottom: 0.1rem;
        }
        .terminal-subtitle {
            color: #9fb0c3;
            margin-bottom: 1rem;
        }
        .metric-card, .soft-card {
            background: #121a24;
            border: 1px solid #263241;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            min-height: 94px;
        }
        .metric-name {
            color: #9fb0c3;
            font-size: 0.82rem;
            white-space: nowrap;
        }
        .metric-value {
            color: #f0f6fc;
            font-size: clamp(1.05rem, 1.6vw, 1.45rem);
            font-weight: 750;
            margin-top: 0.25rem;
            word-break: break-word;
        }
        .metric-change {
            font-size: 0.9rem;
            margin-top: 0.25rem;
            font-weight: 700;
        }
        .section-title {
            font-size: 1.05rem;
            font-weight: 800;
            margin: 1rem 0 0.55rem 0;
            color: #f0f6fc;
        }
        .pill {
            display: inline-block;
            border: 1px solid #334456;
            color: #c9d1d9;
            padding: 0.15rem 0.45rem;
            border-radius: 999px;
            margin: 0.1rem;
            font-size: 0.78rem;
        }
        .source-chip {
            color: #9fb0c3;
            font-size: 0.78rem;
        }
        .news-card {
            background: #101923;
            border-left: 3px solid #f5c542;
            border-radius: 8px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.55rem;
        }
        .small-muted {
            color: #9fb0c3;
            font-size: 0.82rem;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #263241;
            border-radius: 8px;
        }
        @media (max-width: 700px) {
            .metric-card { min-height: 86px; padding: 0.75rem; }
            .main .block-container { padding-left: 0.8rem; padding-right: 0.8rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def pct_color(value: float) -> str:
    return GREEN if value > 0 else RED if value < 0 else GRAY


def render_header() -> None:
    st.markdown('<div class="terminal-title">국내증시 AI 터미널</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="terminal-subtitle">오늘 한국증시에서 돈이 어디로 흐르는지 한눈에 보기</div>',
        unsafe_allow_html=True,
    )


def render_metric_cards(indices: pd.DataFrame) -> None:
    cols = st.columns(5)
    for idx, row in indices.iterrows():
        col = cols[idx % 5]
        value = float(row["value"])
        change = float(row["change_pct"])
        source = row.get("source", "sample")
        formatted = f"{value:,.2f}" if abs(value) < 100000 else f"{value:,.0f}"
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-name">{row['name']} <span class="source-chip">{source}</span></div>
                    <div class="metric-value">{formatted}</div>
                    <div class="metric-change" style="color:{pct_color(change)}">{change:+.2f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_summary(lines: List[str]) -> None:
    st.markdown('<div class="section-title">AI 시장요약</div>', unsafe_allow_html=True)
    st.markdown(
        "<div class='soft-card'>" + "<br>".join(f"{i + 1}. {line}" for i, line in enumerate(lines[:5])) + "</div>",
        unsafe_allow_html=True,
    )


def theme_heatmap(theme_scores: pd.DataFrame) -> go.Figure:
    fig = px.treemap(
        theme_scores,
        path=["theme"],
        values="score",
        color="avg_return",
        color_continuous_scale=[[0, RED], [0.5, "#596274"], [1, GREEN]],
        hover_data=["avg_return", "volume_ratio", "news_mentions"],
    )
    fig.update_layout(
        paper_bgcolor="#08111d",
        plot_bgcolor="#08111d",
        font_color="#e6edf3",
        margin=dict(l=0, r=0, t=8, b=0),
        height=420,
    )
    return fig


def theme_bar(theme_scores: pd.DataFrame) -> go.Figure:
    df = theme_scores.sort_values("score").tail(10)
    colors = [GREEN if x >= 65 else YELLOW if x >= 50 else RED for x in df["score"]]
    fig = go.Figure(go.Bar(x=df["score"], y=df["theme"], orientation="h", marker_color=colors))
    fig.update_layout(
        paper_bgcolor="#08111d",
        plot_bgcolor="#08111d",
        font_color="#e6edf3",
        xaxis=dict(range=[0, 100], gridcolor="#263241"),
        yaxis=dict(gridcolor="#263241"),
        margin=dict(l=8, r=8, t=8, b=8),
        height=390,
    )
    return fig


def risk_gauge(score: float, label: str) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "점", "font": {"color": "#f0f6fc"}},
            title={"text": label, "font": {"color": "#f0f6fc", "size": 18}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#9fb0c3"},
                "bar": {"color": GREEN if score > 60 else YELLOW if score > 30 else RED},
                "bgcolor": "#121a24",
                "borderwidth": 1,
                "bordercolor": "#263241",
                "steps": [
                    {"range": [0, 30], "color": "#421b24"},
                    {"range": [31, 60], "color": "#403b21"},
                    {"range": [61, 80], "color": "#153b30"},
                    {"range": [81, 100], "color": "#0e4a38"},
                ],
            },
        )
    )
    fig.update_layout(paper_bgcolor="#08111d", margin=dict(l=8, r=8, t=24, b=8), height=280)
    return fig


def sankey_flow(flow: List[str]) -> go.Figure:
    labels = flow
    if len(labels) < 2:
        labels = ["대기", "데이터"]
    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(pad=18, thickness=15, line=dict(color="#263241", width=1), label=labels, color="#1f6feb"),
                link=dict(
                    source=list(range(len(labels) - 1)),
                    target=list(range(1, len(labels))),
                    value=[8 + i * 2 for i in range(len(labels) - 1)],
                    color="rgba(22,199,132,0.28)",
                ),
            )
        ]
    )
    fig.update_layout(
        paper_bgcolor="#08111d",
        plot_bgcolor="#08111d",
        font_color="#e6edf3",
        margin=dict(l=0, r=0, t=8, b=8),
        height=250,
    )
    return fig


def render_news_cards(news: pd.DataFrame, limit: int = 8) -> None:
    for _, row in news.head(limit).iterrows():
        stars = "★" * int(row.get("importance", 1))
        link = row.get("link", "")
        title = row.get("title", "")
        title_html = f"<a href='{link}' target='_blank' style='color:#f0f6fc;text-decoration:none'>{title}</a>" if link else title
        st.markdown(
            f"""
            <div class="news-card">
                <div style="font-weight:750">{title_html}</div>
                <div class="small-muted">{row.get('publisher', '')} · {row.get('published', '')} · <span style="color:{YELLOW}">{stars}</span></div>
                <div>{''.join(f'<span class="pill">{tag}</span>' for tag in str(row.get('tags', '시장')).split(','))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_theme_expanders(themes: pd.DataFrame, theme_scores: pd.DataFrame) -> None:
    scores = dict(zip(theme_scores["theme"], theme_scores["score"]))
    for _, row in themes.iterrows():
        with st.expander(f"{row['theme']} · {scores.get(row['theme'], 0):.0f}점"):
            st.write("관련 종목")
            st.markdown(" ".join(f"<span class='pill'>{stock}</span>" for stock in row["stocks_list"]), unsafe_allow_html=True)
            st.caption(f"키워드: {row['keywords']}")


def dataframe_download(label: str, df: pd.DataFrame, filename: str) -> None:
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )
