from __future__ import annotations

from typing import Dict, List

import pandas as pd

from .data_loader import get_stock_snapshot


def calculate_theme_scores(themes: pd.DataFrame, news: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, theme in themes.iterrows():
        stocks = theme.get("stocks_list", [])
        snapshots = [get_stock_snapshot(stock_name) for stock_name in stocks if stock_name]
        returns = [float(item["change_pct"]) for item in snapshots]
        avg_return = sum(returns) / len(returns) if returns else 0.0
        volume_score = sum(float(item["volume_ratio"]) for item in snapshots) / len(snapshots) if snapshots else 1.0
        mention_count = news["tags"].fillna("").str.contains(theme["theme"], regex=False).sum() if not news.empty else 0
        score = 50 + avg_return * 8 + (volume_score - 1) * 12 + min(mention_count * 4, 16)
        rows.append(
            {
                "theme": theme["theme"],
                "avg_return": round(avg_return, 2),
                "volume_ratio": round(volume_score, 2),
                "news_mentions": int(mention_count),
                "score": round(max(0, min(100, score)), 1),
                "stocks": ", ".join(stocks),
                "source": "mixed",
            }
        )
    return pd.DataFrame(rows).sort_values("score", ascending=False)


def build_money_flow(theme_scores: pd.DataFrame) -> List[str]:
    if theme_scores.empty:
        return ["데이터 대기"]
    weak = theme_scores.sort_values("score").head(1)["theme"].tolist()
    strong = theme_scores.head(3)["theme"].tolist()
    return weak + strong


def strong_stock_table(theme_scores: pd.DataFrame, themes: pd.DataFrame, news: pd.DataFrame) -> pd.DataFrame:
    rows = []
    theme_map = dict(zip(themes["theme"], themes["stocks_list"]))
    for _, theme in theme_scores.head(8).iterrows():
        for stock_name in theme_map.get(theme["theme"], [])[:4]:
            snap = get_stock_snapshot(stock_name)
            if snap.get("source") != "live":
                continue
            news_bonus = int(news["title"].fillna("").str.contains(stock_name, regex=False).sum()) if not news.empty else 0
            ai_score = max(0, min(100, theme["score"] * 0.55 + float(snap["change_pct"]) * 8 + news_bonus * 5))
            rows.append(
                {
                    "종목명": stock_name,
                    "테마": theme["theme"],
                    "현재가": round(float(snap["price"]), 0),
                    "등락률(%)": round(float(snap["change_pct"]), 2),
                    "거래대금(억원)": round(float(snap["trading_value"]) / 100_000_000, 1),
                    "AI 점수": round(ai_score, 1),
                    "데이터기준일": snap.get("date", ""),
                    "근거": f"{theme['theme']} 테마 점수 {theme['score']}점, 등락률 {snap['change_pct']:.1f}%",
                }
            )
    columns = ["종목명", "테마", "현재가", "등락률(%)", "거래대금(억원)", "AI 점수", "데이터기준일", "근거"]
    if not rows:
        return pd.DataFrame(columns=columns)
    return (
        pd.DataFrame(rows)
        .sort_values("AI 점수", ascending=False)
        .drop_duplicates(subset=["종목명"], keep="first")
        .head(20)
        .loc[:, columns]
    )


def watchlist_impact(watchlist: pd.DataFrame, theme_scores: pd.DataFrame, themes: pd.DataFrame, news: pd.DataFrame) -> pd.DataFrame:
    rows = []
    theme_rank = {row["theme"]: row["score"] for _, row in theme_scores.iterrows()}
    for _, item in watchlist.iterrows():
        name = item.get("name", item.get("symbol", ""))
        matched_theme = "시장"
        for _, theme in themes.iterrows():
            if name in theme.get("stocks_list", []) or item.get("symbol", "") in theme.get("stocks_list", []):
                matched_theme = theme["theme"]
                break
        score = theme_rank.get(matched_theme, 50)
        tone = "긍정적" if score >= 65 else "중립적" if score >= 45 else "부담"
        rows.append(
            {
                "종목": name,
                "시장": item.get("market", ""),
                "연결 테마": matched_theme,
                "영향": f"{matched_theme} 흐름이 {score:.0f}점으로 {tone}입니다.",
            }
        )
    return pd.DataFrame(rows)
