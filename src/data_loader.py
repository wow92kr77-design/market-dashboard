from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import pandas as pd
import requests

from .config import CACHE_DIR, DART_IMPORTANT_KEYWORDS, INDEX_TICKERS, THEMES_PATH, WATCHLIST_PATH, get_settings

import yfinance as yf

try:
    yf.set_tz_cache_location(str(CACHE_DIR / "yfinance"))
except Exception:
    pass


SAMPLE_INDICES = pd.DataFrame(
    [
        {"name": "KOSPI", "value": 2874.21, "change_pct": 0.82, "source": "sample"},
        {"name": "KOSDAQ", "value": 842.55, "change_pct": 1.14, "source": "sample"},
        {"name": "USD/KRW", "value": 1367.4, "change_pct": -0.28, "source": "sample"},
        {"name": "Nasdaq", "value": 18188.30, "change_pct": 0.56, "source": "sample"},
        {"name": "S&P500", "value": 5482.10, "change_pct": 0.32, "source": "sample"},
        {"name": "Nikkei", "value": 39412.88, "change_pct": 0.41, "source": "sample"},
        {"name": "Shanghai", "value": 3018.05, "change_pct": -0.16, "source": "sample"},
        {"name": "Bitcoin", "value": 64120.0, "change_pct": 1.95, "source": "sample"},
        {"name": "WTI Oil", "value": 81.2, "change_pct": -0.44, "source": "sample"},
        {"name": "VIX", "value": 13.6, "change_pct": -2.15, "source": "sample"},
    ]
)


def _safe_pct(hist: pd.DataFrame) -> Tuple[float, float]:
    """Return latest price and daily percentage change from a yfinance history frame."""
    if hist is None or hist.empty or "Close" not in hist:
        raise ValueError("No close prices")
    close = hist["Close"].dropna()
    if len(close) < 2:
        latest = float(close.iloc[-1])
        return latest, 0.0
    latest = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    change_pct = ((latest / prev) - 1) * 100 if prev else 0.0
    return latest, change_pct


def load_market_indices(use_live: bool = True) -> pd.DataFrame:
    """Load global market cards. Falls back per ticker when any provider fails."""
    rows = []
    if use_live:
        for name, ticker in INDEX_TICKERS.items():
            try:
                hist = yf.Ticker(ticker).history(period="5d", interval="1d")
                value, change_pct = _safe_pct(hist)
                rows.append({"name": name, "value": value, "change_pct": change_pct, "source": "live"})
            except Exception:
                sample = SAMPLE_INDICES[SAMPLE_INDICES["name"] == name].iloc[0].to_dict()
                rows.append(sample)
    else:
        rows = SAMPLE_INDICES.to_dict("records")
    return pd.DataFrame(rows)


def load_themes() -> pd.DataFrame:
    try:
        df = pd.read_csv(THEMES_PATH)
        df["stocks_list"] = df["stocks"].fillna("").str.split("|")
        df["keywords_list"] = df["keywords"].fillna("").str.split("|")
        return df
    except Exception:
        return pd.DataFrame(columns=["theme", "stocks", "keywords", "stocks_list", "keywords_list"])


def load_watchlist() -> pd.DataFrame:
    try:
        return pd.read_csv(WATCHLIST_PATH)
    except Exception:
        return pd.DataFrame(columns=["symbol", "name", "market", "type"])


SAMPLE_STOCK_RETURN = {
    "삼성전자": 0.7,
    "SK하이닉스": 3.2,
    "한미반도체": 2.4,
    "이수페타시스": 1.8,
    "리노공업": 1.3,
    "ISC": 1.0,
    "HD현대일렉트릭": 4.2,
    "LS ELECTRIC": 3.7,
    "효성중공업": 2.9,
    "LS": 2.2,
    "대한전선": 3.4,
    "두산에너빌리티": 2.8,
    "한전기술": 1.9,
    "한전KPS": 1.1,
    "비에이치아이": 4.8,
    "우리기술": 3.5,
    "HD한국조선해양": 2.3,
    "HD현대중공업": 1.7,
    "삼성중공업": 2.1,
    "한화오션": 3.1,
    "한화에어로스페이스": 2.6,
    "현대로템": 1.4,
    "LIG넥스원": 1.8,
    "한국항공우주": 0.9,
    "LG에너지솔루션": -1.2,
    "삼성SDI": -0.8,
    "에코프로비엠": -2.0,
    "포스코퓨처엠": -1.5,
    "HLB": -0.7,
}


def get_stock_snapshot(name: str) -> Dict[str, object]:
    """Small stock snapshot. Korean names use sample mapping until ticker mapping is expanded."""
    if name in SAMPLE_STOCK_RETURN:
        pct = SAMPLE_STOCK_RETURN[name]
        return {
            "name": name,
            "price": 50000 + abs(hash(name)) % 250000,
            "change_pct": pct,
            "volume_ratio": 1.0 + max(pct, 0) / 4,
            "trading_value": 20_000_000_000 + (abs(hash(name)) % 80) * 1_000_000_000,
            "source": "sample",
        }
    if not name.isascii():
        pseudo_pct = ((abs(hash(name)) % 41) - 15) / 10
        return {
            "name": name,
            "price": 30000 + abs(hash(name)) % 180000,
            "change_pct": pseudo_pct,
            "volume_ratio": 1.0 + max(pseudo_pct, 0) / 5,
            "trading_value": 8_000_000_000 + (abs(hash(name)) % 70) * 1_000_000_000,
            "source": "sample",
        }
    try:
        hist = yf.Ticker(name).history(period="5d")
        price, pct = _safe_pct(hist)
        return {
            "name": name,
            "price": price,
            "change_pct": pct,
            "volume_ratio": 1.0,
            "trading_value": 0,
            "source": "live",
        }
    except Exception:
        return {
            "name": name,
            "price": 0,
            "change_pct": 0.0,
            "volume_ratio": 1.0,
            "trading_value": 0,
            "source": "sample",
        }


def load_investor_flows() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch foreign/institution net buying. pykrx failures return sample frames."""
    sample_foreign = pd.DataFrame(
        [
            ["SK하이닉스", "KOSPI", 1650, 3.2],
            ["HD현대일렉트릭", "KOSPI", 980, 4.2],
            ["한화에어로스페이스", "KOSPI", 760, 2.6],
            ["삼성전자", "KOSPI", 710, 0.7],
            ["두산에너빌리티", "KOSPI", 540, 2.8],
            ["한미반도체", "KOSPI", 410, 2.4],
        ],
        columns=["종목명", "시장", "순매수금액(억원)", "등락률"],
    )
    sample_inst = pd.DataFrame(
        [
            ["LS ELECTRIC", "KOSPI", 620, 3.7],
            ["삼성중공업", "KOSPI", 510, 2.1],
            ["한화오션", "KOSPI", 455, 3.1],
            ["한전기술", "KOSPI", 330, 1.9],
            ["리노공업", "KOSDAQ", 280, 1.3],
        ],
        columns=["종목명", "시장", "순매수금액(억원)", "등락률"],
    )
    if not get_settings()["use_live_data"]:
        return sample_foreign, sample_inst
    try:
        from pykrx import stock

        day = datetime.now().strftime("%Y%m%d")
        # TODO: Expand this to market별 KOSPI/KOSDAQ aggregation once pykrx schema is stable.
        df = stock.get_market_net_purchases_of_equities(day, day, "KOSPI", "외국인")
        df = df.sort_values("순매수거래대금", ascending=False).head(20)
        foreign = pd.DataFrame(
            {
                "종목명": [stock.get_market_ticker_name(t) for t in df.index],
                "시장": "KOSPI",
                "순매수금액(억원)": (df["순매수거래대금"] / 100_000_000).round(0),
                "등락률": 0.0,
            }
        )
        return foreign, sample_inst
    except Exception:
        return sample_foreign, sample_inst


def load_program_trading() -> Dict[str, object]:
    """Placeholder for future KRX program trading integration."""
    return {
        "status": "데이터 연결 필요",
        "message": "KRX/pykrx 프로그램 매매 데이터는 추후 연결용 함수로 분리되어 있습니다.",
        "source": "sample",
    }


def load_disclosures(dart_api_key: str = "") -> pd.DataFrame:
    sample = pd.DataFrame(
        [
            {"시간": "09:12", "종목": "HD현대일렉트릭", "공시": "대규모 공급계약 체결", "분류": "호재"},
            {"시간": "10:35", "종목": "A사", "공시": "유상증자 결정", "분류": "악재"},
            {"시간": "11:20", "종목": "B사", "공시": "최대주주 변경", "분류": "중립"},
        ]
    )
    if not dart_api_key:
        sample["source"] = "sample"
        return sample
    try:
        url = "https://opendart.fss.or.kr/api/list.json"
        params = {"crtfc_key": dart_api_key, "page_count": 20}
        data = requests.get(url, params=params, timeout=8).json()
        rows = []
        for item in data.get("list", []):
            title = item.get("report_nm", "")
            label = "중립"
            if any(k in title for k in DART_IMPORTANT_KEYWORDS["호재"]):
                label = "호재"
            if any(k in title for k in DART_IMPORTANT_KEYWORDS["악재"]):
                label = "악재"
            rows.append(
                {
                    "시간": item.get("rcept_dt", ""),
                    "종목": item.get("corp_name", ""),
                    "공시": title,
                    "분류": label,
                    "source": "live",
                }
            )
        return pd.DataFrame(rows) if rows else sample
    except Exception:
        sample["source"] = "sample"
        return sample


def load_economic_calendar() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"일정": "미국 CPI", "예상 영향": "환율/성장주 변동성", "중요도": "★★★", "일자": "이번 주"},
            {"일정": "FOMC 의사록", "예상 영향": "금리 민감주", "중요도": "★★★★★", "일자": "다음 주"},
            {"일정": "한국 금통위", "예상 영향": "은행/건설/환율", "중요도": "★★★★", "일자": "월중"},
            {"일정": "엔비디아/마이크론 실적", "예상 영향": "HBM/반도체", "중요도": "★★★★★", "일자": "실적 시즌"},
            {"일정": "미국 고용지표", "예상 영향": "달러/미국 선물", "중요도": "★★★★", "일자": "월초"},
        ]
    )
