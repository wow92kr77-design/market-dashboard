from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Tuple
from zoneinfo import ZoneInfo

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

YAHOO_KR_TICKERS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "한미반도체": "042700.KS",
    "이수페타시스": "007660.KS",
    "리노공업": "058470.KQ",
    "ISC": "095340.KQ",
    "HD현대일렉트릭": "267260.KS",
    "LS ELECTRIC": "010120.KS",
    "효성중공업": "298040.KS",
    "일진전기": "103590.KS",
    "LS": "006260.KS",
    "대한전선": "001440.KS",
    "두산에너빌리티": "034020.KS",
    "한전기술": "052690.KS",
    "한전KPS": "051600.KS",
    "비에이치아이": "083650.KQ",
    "우리기술": "032820.KQ",
    "HD한국조선해양": "009540.KS",
    "HD현대중공업": "329180.KS",
    "삼성중공업": "010140.KS",
    "한화오션": "042660.KS",
    "한화에어로스페이스": "012450.KS",
    "현대로템": "064350.KS",
    "LIG넥스원": "079550.KS",
    "한국항공우주": "047810.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "현대모비스": "012330.KS",
    "HL만도": "204320.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성SDI": "006400.KS",
    "에코프로비엠": "247540.KQ",
    "포스코퓨처엠": "003670.KS",
    "삼성바이오로직스": "207940.KS",
    "셀트리온": "068270.KS",
    "유한양행": "000100.KS",
    "HLB": "028300.KQ",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
    "하나금융지주": "086790.KS",
    "우리금융지주": "316140.KS",
    "레인보우로보틱스": "277810.KQ",
    "두산로보틱스": "454910.KS",
    "로보티즈": "108490.KQ",
    "아모레퍼시픽": "090430.KS",
    "LG생활건강": "051900.KS",
    "한국콜마": "161890.KS",
    "코스맥스": "192820.KS",
    "CJ제일제당": "097950.KS",
    "오리온": "271560.KS",
    "삼양식품": "003230.KS",
    "농심": "004370.KS",
}


def _snapshot_from_yfinance(name: str, ticker: str) -> Dict[str, object]:
    hist = yf.Ticker(ticker).history(period="30d", interval="1d", auto_adjust=False)
    if hist is None or hist.empty or "Close" not in hist:
        raise ValueError("No close prices")
    close = hist["Close"].dropna()
    if len(close) < 2:
        raise ValueError("Not enough close prices")
    latest = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    change_pct = ((latest / prev) - 1) * 100 if prev else 0.0
    latest_volume = float(hist["Volume"].dropna().iloc[-1]) if "Volume" in hist and not hist["Volume"].dropna().empty else 0.0
    avg_volume = float(hist["Volume"].dropna().tail(20).mean()) if "Volume" in hist and not hist["Volume"].dropna().empty else 0.0
    trading_value = latest * latest_volume
    volume_ratio = latest_volume / avg_volume if avg_volume else 1.0
    return {
        "name": name,
        "price": latest,
        "change_pct": change_pct,
        "volume_ratio": volume_ratio,
        "trading_value": trading_value,
        "date": str(close.index[-1].date()) if hasattr(close.index[-1], "date") else "",
        "source": "live",
    }


@lru_cache(maxsize=256)
def get_stock_snapshot(name: str) -> Dict[str, object]:
    """Small stock snapshot. Live mode tries Yahoo tickers, then falls back safely."""
    settings = get_settings()
    if settings["use_live_data"]:
        ticker = YAHOO_KR_TICKERS.get(name, name if name.isascii() else "")
        if ticker:
            try:
                return _snapshot_from_yfinance(name, ticker)
            except Exception:
                pass
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


def load_investor_flows() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fetch latest available foreign/institution net buying and selling."""
    empty_buy = _empty_investor_frame("순매수금액(억원)")
    empty_sell = _empty_investor_frame("순매도금액(억원)")
    if not get_settings()["use_live_data"]:
        return empty_buy, empty_buy, empty_sell, empty_sell
    try:
        from pykrx import stock

        foreign_buy = _fetch_investor_top(stock, "외국인", "buy")
        institution_buy = _fetch_investor_top(stock, "기관합계", "buy")
        foreign_sell = _fetch_investor_top(stock, "외국인", "sell")
        institution_sell = _fetch_investor_top(stock, "기관합계", "sell")
        return foreign_buy, institution_buy, foreign_sell, institution_sell
    except Exception:
        return empty_buy, empty_buy, empty_sell, empty_sell


def _empty_investor_frame(amount_column: str) -> pd.DataFrame:
    return pd.DataFrame(columns=["종목명", "시장", amount_column, "등락률(%)", "데이터기준일"])


def _fetch_investor_top(stock_api, investor: str, direction: str) -> pd.DataFrame:
    markets = ["KOSPI", "KOSDAQ"]
    amount_column = "순매수금액(억원)" if direction == "buy" else "순매도금액(억원)"
    for offset in range(0, 14):
        day = (datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=offset)).strftime("%Y%m%d")
        rows = []
        for market in markets:
            try:
                flow = stock_api.get_market_net_purchases_of_equities(day, day, market, investor)
                if flow is None or flow.empty or "순매수거래대금" not in flow:
                    continue
                ohlcv = stock_api.get_market_ohlcv_by_ticker(day, market)
                flow = flow.copy()
                flow["시장"] = market
                flow["등락률(%)"] = 0.0
                if ohlcv is not None and not ohlcv.empty and "등락률" in ohlcv:
                    flow["등락률(%)"] = ohlcv["등락률"].reindex(flow.index).fillna(0.0)
                rows.append(flow)
            except Exception:
                continue
        if rows:
            data = pd.concat(rows)
            if direction == "buy":
                data = data[data["순매수거래대금"] > 0].sort_values("순매수거래대금", ascending=False).head(20)
                amount = data["순매수거래대금"]
            else:
                data = data[data["순매수거래대금"] < 0].sort_values("순매수거래대금", ascending=True).head(20)
                amount = data["순매수거래대금"].abs()
            if data.empty:
                continue
            return pd.DataFrame(
                {
                    "종목명": [stock_api.get_market_ticker_name(ticker) for ticker in data.index],
                    "시장": data["시장"].values,
                    amount_column: (amount / 100_000_000).round(1).values,
                    "등락률(%)": data["등락률(%)"].round(2).values,
                    "데이터기준일": day,
                }
            )
    return _empty_investor_frame(amount_column)


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
