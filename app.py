from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from src.ai_summary import generate_ai_summary
from src.benefit_stock_engine import match_benefit_stocks
from src.config import get_settings
from src.data_loader import (
    load_disclosures,
    load_economic_calendar,
    load_investor_flows,
    load_market_indices,
    load_program_trading,
    load_themes,
    load_watchlist,
)
from src.market_score import calculate_risk_score, generate_investment_ideas
from src.news_loader import load_market_news, negative_news_ratio, summarize_news
from src.theme_engine import calculate_theme_scores, strong_stock_table, watchlist_impact
from src.ui_components import (
    apply_theme,
    dataframe_download,
    render_header,
    render_metric_cards,
    render_news_cards,
    render_summary,
    render_theme_expanders,
    risk_gauge,
    theme_bar,
    theme_heatmap,
)


@st.cache_data(ttl=300, show_spinner=False)
def load_dashboard_data(force_refresh_key: int = 0) -> dict:
    """One cached function keeps refresh behavior simple for local and Cloud use."""
    settings = get_settings()
    themes = load_themes()
    watchlist = load_watchlist()
    indices = load_market_indices(settings["use_live_data"])
    news = load_market_news(themes)
    theme_scores = calculate_theme_scores(themes, news)
    foreign_flow, institution_flow = load_investor_flows()
    risk = calculate_risk_score(indices, foreign_flow, negative_news_ratio(news))
    summary = generate_ai_summary(
        settings["openai_api_key"],
        settings["openai_model"],
        indices,
        theme_scores,
        foreign_flow,
        news,
    )
    return {
        "settings": settings,
        "themes": themes,
        "watchlist": watchlist,
        "indices": indices,
        "news": news,
        "theme_scores": theme_scores,
        "foreign_flow": foreign_flow,
        "institution_flow": institution_flow,
        "program": load_program_trading(),
        "disclosures": load_disclosures(settings["dart_api_key"]),
        "calendar": load_economic_calendar(),
        "risk": risk,
        "summary": summary,
        "news_summary": summarize_news(news),
        "benefits": match_benefit_stocks(news),
        "strong_stocks": strong_stock_table(theme_scores, themes, news),
        "watch_impact": watchlist_impact(watchlist, theme_scores, themes, news),
        "ideas": generate_investment_ideas(theme_scores, themes),
    }


def build_html_report(data: dict) -> str:
    """Simple downloadable report. Users can print this HTML to PDF."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sections = [
        "<h1>국내증시 AI 터미널 리포트</h1>",
        f"<p>생성 시각: {now}</p>",
        "<h2>AI 시장요약</h2>",
        "<ol>" + "".join(f"<li>{line}</li>" for line in data["summary"]) + "</ol>",
        "<h2>지표</h2>",
        data["indices"].to_html(index=False),
        "<h2>테마 점수 TOP10</h2>",
        data["theme_scores"].head(10).to_html(index=False),
        "<h2>강한 종목 TOP20</h2>",
        data["strong_stocks"].to_html(index=False),
        "<h2>주요 뉴스</h2>",
        data["news"].head(10).to_html(index=False),
    ]
    return """
    <html><head><meta charset="utf-8">
    <style>
    body{font-family:Arial,'Malgun Gothic',sans-serif;background:#08111d;color:#e6edf3;padding:24px}
    table{border-collapse:collapse;width:100%;margin:12px 0} th,td{border:1px solid #263241;padding:8px}
    th{background:#121a24}
    </style></head><body>
    """ + "\n".join(sections) + "</body></html>"


def main() -> None:
    apply_theme()
    if "refresh_key" not in st.session_state:
        st.session_state.refresh_key = 0

    render_header()

    top_left, top_mid, top_right = st.columns([1.2, 1, 1])
    with top_left:
        st.caption("샘플 데이터와 실시간 데이터가 섞일 수 있으며 각 카드에 source가 표시됩니다.")
    with top_mid:
        if st.button("대시보드 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.session_state.refresh_key += 1
            st.rerun()
    with top_right:
        st.caption(f"업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    with st.spinner("시장 데이터를 불러오는 중입니다..."):
        data = load_dashboard_data(st.session_state.refresh_key)

    render_metric_cards(data["indices"])
    render_summary(data["summary"])

    left, right = st.columns([1.45, 1])
    with left:
        st.markdown('<div class="section-title">업종/테마 히트맵</div>', unsafe_allow_html=True)
        st.plotly_chart(theme_heatmap(data["theme_scores"]), use_container_width=True)
    with right:
        st.markdown('<div class="section-title">시장 위험도</div>', unsafe_allow_html=True)
        st.plotly_chart(risk_gauge(data["risk"]["score"], data["risk"]["label"]), use_container_width=True)
        st.markdown('<div class="section-title">오늘 돈이 몰리는 업종 TOP10</div>', unsafe_allow_html=True)
        st.plotly_chart(theme_bar(data["theme_scores"]), use_container_width=True)

    st.markdown('<div class="section-title">오늘의 강한 종목 TOP20</div>', unsafe_allow_html=True)
    st.dataframe(data["strong_stocks"], use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">주요 뉴스 요약</div>', unsafe_allow_html=True)
    st.dataframe(
        data["news_summary"][["중요도", "테마", "뉴스", "요약"]],
        use_container_width=True,
        hide_index=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["수급", "뉴스·수혜주", "테마·종목", "공시·일정", "관심종목·공유"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("외국인 순매수 TOP20")
            st.dataframe(data["foreign_flow"], use_container_width=True, hide_index=True)
        with col2:
            st.subheader("기관 순매수 TOP20")
            st.dataframe(data["institution_flow"], use_container_width=True, hide_index=True)
        st.subheader("프로그램 매매/시장 수급")
        st.info(f"{data['program']['status']}: {data['program']['message']}")

    with tab2:
        col1, col2 = st.columns([1.1, 1])
        with col1:
            st.subheader("주요 뉴스 요약")
            st.dataframe(data["news_summary"], use_container_width=True, hide_index=True)
            st.subheader("뉴스 원문 링크")
            render_news_cards(data["news"], limit=10)
        with col2:
            st.subheader("예상 수혜주 엔진")
            if data["benefits"].empty:
                st.info("매칭된 뉴스가 아직 없습니다. 뉴스 키워드가 들어오면 자동으로 테마와 예상 수혜주를 표시합니다.")
            else:
                for _, row in data["benefits"].iterrows():
                    st.markdown(
                        f"**뉴스**: {row['뉴스']}\n\n"
                        f"**테마**: {row['테마']}\n\n"
                        f"**예상 수혜주**: {row['예상 수혜주']}\n\n"
                        f"**근거**: {row['근거']}"
                    )
                    st.divider()

    with tab3:
        col1, col2 = st.columns([1.1, 1])
        with col1:
            st.subheader("오늘의 강한 종목 TOP20")
            st.dataframe(data["strong_stocks"], use_container_width=True, hide_index=True)
        with col2:
            st.subheader("오늘의 테마")
            render_theme_expanders(data["themes"], data["theme_scores"])
        st.subheader("AI 투자아이디어")
        st.dataframe(data["ideas"], use_container_width=True, hide_index=True)

    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("공시")
            if not data["settings"]["dart_api_key"]:
                st.warning("DART API 키 입력 시 공시 자동 조회 가능")
            st.dataframe(data["disclosures"], use_container_width=True, hide_index=True)
        with col2:
            st.subheader("경제일정")
            st.dataframe(data["calendar"], use_container_width=True, hide_index=True)

    with tab5:
        col1, col2 = st.columns([1.2, 1])
        with col1:
            st.subheader("관심종목/보유종목 영향 분석")
            st.dataframe(data["watch_impact"], use_container_width=True, hide_index=True)
        with col2:
            st.subheader("공유/저장")
            dataframe_download("강한 종목 CSV 다운로드", data["strong_stocks"], "strong_stocks.csv")
            dataframe_download("테마 점수 CSV 다운로드", data["theme_scores"], "theme_scores.csv")
            html_report = build_html_report(data)
            st.download_button(
                "HTML 리포트 저장",
                data=html_report.encode("utf-8"),
                file_name="market_dashboard_report.html",
                mime="text/html",
                use_container_width=True,
            )
            st.download_button(
                "PDF 저장용 HTML 다운로드",
                data=html_report.encode("utf-8"),
                file_name="market_dashboard_print_to_pdf.html",
                mime="text/html",
                use_container_width=True,
                help="다운로드한 HTML 파일을 브라우저에서 열고 인쇄 메뉴에서 PDF로 저장하세요.",
            )

    st.caption("투자 판단의 최종 책임은 사용자에게 있습니다. 본 앱은 시장 흐름 파악을 위한 보조 도구입니다.")


if __name__ == "__main__":
    main()
