from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
import feedparser
import pandas as pd


NEWS_KEYWORDS = [
    "국내증시",
    "코스피",
    "코스닥",
    "반도체",
    "HBM",
    "원전",
    "조선",
    "방산",
    "2차전지",
    "전력기기",
    "환율",
    "금리",
]

NEGATIVE_WORDS = ["급락", "침체", "우려", "하락", "매도", "리스크", "부진", "적자", "전쟁"]
POSITIVE_WORDS = ["상승", "강세", "수주", "호조", "확대", "투자", "신고가", "순매수"]


def _fallback_news() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "title": "AI 데이터센터 투자 확대에 전력기기주 강세",
                "publisher": "Sample News",
                "published": "방금 전",
                "link": "",
                "importance": 5,
                "tags": "전력기기,AI",
                "summary": "데이터센터 전력수요 확대 기대가 관련주로 확산되고 있습니다.",
                "source": "sample",
            },
            {
                "title": "HBM 수요 기대 지속, 반도체 대형주에 외국인 매수",
                "publisher": "Sample News",
                "published": "15분 전",
                "link": "",
                "importance": 4,
                "tags": "HBM,반도체",
                "summary": "AI 반도체 공급망에 대한 투자심리가 유지되고 있습니다.",
                "source": "sample",
            },
            {
                "title": "2차전지주는 차익실현 매물 출회",
                "publisher": "Sample News",
                "published": "30분 전",
                "link": "",
                "importance": 3,
                "tags": "2차전지",
                "summary": "단기 반등 이후 일부 종목에서 매물이 나오고 있습니다.",
                "source": "sample",
            },
            {
                "title": "원전 수출 기대감에 SMR 관련주 부각",
                "publisher": "Sample News",
                "published": "45분 전",
                "link": "",
                "importance": 4,
                "tags": "원전/SMR",
                "summary": "정책 및 수출 모멘텀이 테마 강도를 높이고 있습니다.",
                "source": "sample",
            },
        ]
    )


def score_news_importance(title: str) -> int:
    score = 1
    score += min(2, sum(word in title for word in POSITIVE_WORDS))
    score += min(2, sum(word in title for word in NEGATIVE_WORDS))
    if any(word in title for word in ["외국인", "수주", "급락", "FOMC", "환율"]):
        score += 1
    return max(1, min(5, score))


def tag_news(title: str, themes: pd.DataFrame) -> str:
    tags: List[str] = []
    for _, row in themes.iterrows():
        keywords = row.get("keywords_list", [])
        if any(str(keyword).lower() in title.lower() for keyword in keywords):
            tags.append(row["theme"])
    return ",".join(tags[:4]) if tags else "시장"


def load_market_news(themes: pd.DataFrame, limit: int = 30) -> pd.DataFrame:
    """Read Google News RSS. RSS outages return a sample table."""
    rows = []
    seen = set()
    try:
        for keyword in NEWS_KEYWORDS:
            rss_url = f"https://news.google.com/rss/search?q={quote_plus(keyword + ' 한국증시')}&hl=ko&gl=KR&ceid=KR:ko"
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:6]:
                title = entry.get("title", "").strip()
                if not title or title in seen:
                    continue
                seen.add(title)
                rows.append(
                    {
                        "title": title,
                        "publisher": entry.get("source", {}).get("title", "Google News"),
                        "published": entry.get("published", ""),
                        "link": entry.get("link", ""),
                        "importance": score_news_importance(title),
                        "tags": tag_news(title, themes),
                        "summary": entry.get("summary", ""),
                        "source": "live",
                    }
                )
                if len(rows) >= limit:
                    break
            if len(rows) >= limit:
                break
        return pd.DataFrame(rows) if rows else _fallback_news()
    except Exception:
        return _fallback_news()


def negative_news_ratio(news: pd.DataFrame) -> float:
    if news.empty:
        return 0.0
    negatives = news["title"].fillna("").apply(lambda title: any(word in title for word in NEGATIVE_WORDS)).sum()
    return float(negatives / len(news))


def summarize_news(news: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    """Make a compact Korean summary table from RSS news without paid APIs."""
    rows = []
    for _, item in news.head(limit).iterrows():
        title = str(item.get("title", "")).strip()
        raw_summary = str(item.get("summary", "")).strip()
        plain_summary = BeautifulSoup(raw_summary, "html.parser").get_text(" ", strip=True)
        if not plain_summary or plain_summary == title:
            plain_summary = _rule_news_summary(title, str(item.get("tags", "시장")))
        rows.append(
            {
                "중요도": "★" * int(item.get("importance", 1)),
                "테마": item.get("tags", "시장"),
                "뉴스": title,
                "요약": plain_summary[:150],
                "출처": item.get("publisher", ""),
                "링크": item.get("link", ""),
            }
        )
    return pd.DataFrame(rows)


def _rule_news_summary(title: str, tags: str) -> str:
    if any(word in title for word in ["수주", "공급계약", "수출"]):
        return f"{tags} 관련 수주/수출 모멘텀이 부각되는 뉴스입니다."
    if any(word in title for word in ["강세", "상승", "신고가"]):
        return f"{tags} 투자심리가 개선되며 관련 종목 흐름이 강한 뉴스입니다."
    if any(word in title for word in ["하락", "급락", "부진", "우려"]):
        return f"{tags} 쪽 단기 부담 또는 리스크를 점검해야 하는 뉴스입니다."
    if any(word in title for word in ["환율", "금리", "FOMC", "CPI"]):
        return "거시 변수 변화가 국내 증시 수급과 성장주 변동성에 영향을 줄 수 있습니다."
    return f"{tags} 관련 시장 관심이 확인되는 뉴스입니다."
