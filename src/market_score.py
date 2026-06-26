from __future__ import annotations

import math
from typing import Dict, List

import pandas as pd


def calculate_risk_score(indices: pd.DataFrame, foreign_flow: pd.DataFrame, negative_news_ratio: float) -> Dict[str, object]:
    def _number(value: object, fallback: float = 0.0) -> float:
        try:
            number = float(value)
            return number if math.isfinite(number) else fallback
        except Exception:
            return fallback

    def pct(name: str, limit: float = 15.0) -> float:
        row = indices[indices["name"] == name]
        value = _number(row["change_pct"].iloc[0]) if not row.empty else 0.0
        # Bad provider ticks can occasionally report impossible daily changes.
        return value if abs(value) <= limit else 0.0

    def val(name: str) -> float:
        row = indices[indices["name"] == name]
        return _number(row["value"].iloc[0]) if not row.empty else 0.0

    score = 50.0
    score += pct("KOSPI") * 8
    score += pct("KOSDAQ") * 6
    score -= max(pct("USD/KRW", limit=5.0), 0) * 5
    score += pct("Nasdaq") * 4
    score += pct("S&P500") * 4

    vix = val("VIX")
    if not 0 < vix < 100:
        vix = 15.0
    score -= min(max(vix - 15, 0) * 1.2, 35)

    flow_col = "순매수금액(억원)"
    if not foreign_flow.empty and flow_col in foreign_flow and foreign_flow[flow_col].sum() > 0:
        score += 8
    score -= max(0.0, min(1.0, _number(negative_news_ratio))) * 20
    score = round(max(0, min(100, score)), 1)
    label = "위험" if score <= 30 else "보통" if score <= 60 else "양호" if score <= 80 else "매우 좋음"
    return {"score": score, "label": label}


def generate_rule_summary(indices: pd.DataFrame, theme_scores: pd.DataFrame, foreign_flow: pd.DataFrame, news: pd.DataFrame) -> List[str]:
    top_themes = theme_scores.head(3)["theme"].tolist()
    weak_theme = theme_scores.tail(1)["theme"].iloc[0] if not theme_scores.empty else "일부 테마"
    kospi = indices[indices["name"] == "KOSPI"]["change_pct"].iloc[0] if not indices.empty else 0
    usdkrw = indices[indices["name"] == "USD/KRW"]["change_pct"].iloc[0] if not indices.empty else 0
    foreign_sum = foreign_flow["순매수금액(억원)"].sum() if not foreign_flow.empty else 0
    lines = [
        f"오늘 국내증시는 KOSPI {kospi:+.2f}% 흐름 속에 {', '.join(top_themes[:2])}가 주도하고 있습니다.",
        f"외국인 순매수 상위에는 {', '.join(foreign_flow.head(3)['종목명'].tolist()) if not foreign_flow.empty else '대형주'}가 올라와 있습니다.",
        "환율 안정은 긍정적입니다." if usdkrw <= 0 else "USD/KRW 상승은 단기 수급 부담으로 작용할 수 있습니다.",
        f"{weak_theme} 쪽은 상대적으로 힘이 약해 선별 접근이 필요합니다.",
        f"단기적으로는 {', '.join(top_themes)} 테마의 거래대금과 뉴스 강도를 함께 확인할 필요가 있습니다.",
    ]
    return lines


def generate_investment_ideas(theme_scores: pd.DataFrame, themes: pd.DataFrame) -> pd.DataFrame:
    theme_to_stocks = dict(zip(themes["theme"], themes["stocks"]))
    rows = []
    for _, row in theme_scores.head(3).iterrows():
        caution = "단기 급등 부담" if row["avg_return"] > 3 else "뉴스 소멸 시 변동성"
        rows.append(
            {
                "테마": row["theme"],
                "점수": row["score"],
                "관련 종목": theme_to_stocks.get(row["theme"], "").replace("|", ", "),
                "근거": f"평균 수익률 {row['avg_return']}%, 뉴스 언급 {row['news_mentions']}건, 거래량 지표 {row['volume_ratio']}배",
                "주의": caution,
            }
        )
    return pd.DataFrame(rows)
