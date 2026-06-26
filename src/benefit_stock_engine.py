from __future__ import annotations

from typing import Dict, List

import pandas as pd


BENEFIT_RULES = [
    {
        "keywords": ["AI 데이터센터", "데이터센터", "전력", "전선", "변압기", "구리"],
        "themes": ["전력기기", "AI"],
        "stocks": ["HD현대일렉트릭", "LS ELECTRIC", "효성중공업", "LS", "대한전선"],
        "reason": "데이터센터 투자 확대는 전력망, 변압기, 전선 수요 증가 기대와 연결됩니다.",
    },
    {
        "keywords": ["원전", "SMR", "원자력", "체코"],
        "themes": ["원전/SMR"],
        "stocks": ["두산에너빌리티", "한전기술", "비에이치아이", "우리기술"],
        "reason": "원전 수출 및 SMR 모멘텀은 기자재와 설계 기업에 기대감을 만듭니다.",
    },
    {
        "keywords": ["HBM", "AI 반도체", "엔비디아", "고대역폭"],
        "themes": ["HBM", "반도체"],
        "stocks": ["SK하이닉스", "한미반도체", "이수페타시스", "ISC"],
        "reason": "AI 가속기 수요는 HBM과 반도체 장비 공급망에 우호적입니다.",
    },
    {
        "keywords": ["조선", "수주", "LNG선", "선박"],
        "themes": ["조선"],
        "stocks": ["HD한국조선해양", "삼성중공업", "한화오션"],
        "reason": "선박 발주와 수주 잔고 증가는 조선사 실적 가시성을 높입니다.",
    },
    {
        "keywords": ["방산", "K2", "K9", "미사일", "수출"],
        "themes": ["방산"],
        "stocks": ["한화에어로스페이스", "현대로템", "LIG넥스원"],
        "reason": "방산 수출 뉴스는 수주 기대와 밸류에이션 재평가로 이어질 수 있습니다.",
    },
]


def match_benefit_stocks(news: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if news.empty:
        return pd.DataFrame(columns=["뉴스", "테마", "예상 수혜주", "근거", "중요도"])
    for _, item in news.head(20).iterrows():
        title = item.get("title", "")
        body = f"{title} {item.get('summary', '')}"
        for rule in BENEFIT_RULES:
            if any(keyword.lower() in body.lower() for keyword in rule["keywords"]):
                rows.append(
                    {
                        "뉴스": title,
                        "테마": ", ".join(rule["themes"]),
                        "예상 수혜주": ", ".join(rule["stocks"]),
                        "근거": rule["reason"],
                        "중요도": item.get("importance", 3),
                    }
                )
                break
    return pd.DataFrame(rows).head(10)
