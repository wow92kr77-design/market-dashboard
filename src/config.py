from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / ".cache"
THEMES_PATH = DATA_DIR / "themes.csv"
WATCHLIST_PATH = DATA_DIR / "watchlist.csv"

CACHE_DIR.mkdir(exist_ok=True)
(CACHE_DIR / "matplotlib").mkdir(exist_ok=True)
(CACHE_DIR / "yfinance").mkdir(exist_ok=True)

# Some desktop sandboxes block default home cache folders. Keep library caches local.
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))
os.environ.setdefault("YFINANCE_CACHE_DIR", str(CACHE_DIR / "yfinance"))

load_dotenv(BASE_DIR / ".env")


def get_settings() -> Dict[str, str]:
    """Read environment settings in one place so beginners can find them."""
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY", "").strip(),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
        "dart_api_key": os.getenv("DART_API_KEY", "").strip(),
        "use_live_data": os.getenv("USE_LIVE_DATA", "false").lower() == "true",
    }


INDEX_TICKERS = {
    "KOSPI": "^KS11",
    "KOSDAQ": "^KQ11",
    "USD/KRW": "KRW=X",
    "Nasdaq": "^IXIC",
    "S&P500": "^GSPC",
    "Nikkei": "^N225",
    "Shanghai": "000001.SS",
    "Bitcoin": "BTC-USD",
    "WTI Oil": "CL=F",
    "VIX": "^VIX",
}


DART_IMPORTANT_KEYWORDS = {
    "호재": ["수주", "공급계약", "자사주", "무상증자", "배당", "신규시설투자"],
    "악재": ["유상증자", "투자경고", "거래정지", "횡령", "최대주주 변경", "감사의견"],
}
