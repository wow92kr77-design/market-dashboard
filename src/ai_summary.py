from __future__ import annotations

from typing import List

import pandas as pd

from .market_score import generate_rule_summary


def generate_ai_summary(
    api_key: str,
    model: str,
    indices: pd.DataFrame,
    theme_scores: pd.DataFrame,
    foreign_flow: pd.DataFrame,
    news: pd.DataFrame,
) -> List[str]:
    """Use OpenAI when configured, otherwise return a transparent rule-based summary."""
    if not api_key:
        return generate_rule_summary(indices, theme_scores, foreign_flow, news)
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt = f"""
        한국증시 데일리 대시보드용 5줄 요약을 한국어로 작성해줘.
        과장하지 말고 데이터 기반으로 써줘.
        지수: {indices[['name', 'change_pct']].to_dict('records')}
        강한 테마: {theme_scores.head(5)[['theme', 'score', 'avg_return', 'news_mentions']].to_dict('records')}
        외국인 순매수: {foreign_flow.head(5).to_dict('records')}
        주요 뉴스: {news.head(5)[['title', 'tags']].to_dict('records')}
        출력은 줄바꿈으로 구분한 정확히 5문장.
        """
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.35,
        )
        content = response.choices[0].message.content or ""
        lines = [line.strip(" -0123456789.").strip() for line in content.splitlines() if line.strip()]
        return lines[:5] if lines else generate_rule_summary(indices, theme_scores, foreign_flow, news)
    except Exception:
        return generate_rule_summary(indices, theme_scores, foreign_flow, news)
