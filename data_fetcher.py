"""
data_fetcher.py
Fetches the LIVE NSE F&O stock universe from NSE public endpoint each session.
Falls back to a comprehensive hardcoded list (~200 symbols) when NSE is unreachable.
Every stock fetch is isolated — one failure never crashes the rest.
"""

import requests
import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
import pytz

# ── NSE public API ────────────────────────────────────────────────────────────
NSE_FNO_URL = (
    "https://www.nseindia.com/api/equity-stockIndices"
    "?index=SECURITIES%20IN%20F%26O"
)
NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
    "Accept": "application/json, text/plain, */*",
}

# ── Comprehensive fallback F&O universe (~200 symbols) ────────────────────────
FALLBACK_FNO_SYMBOLS = [
    # Index heavyweights
    "RELIANCE","HDFCBANK","ICICIBANK","INFY","TCS","LT","ITC","KOTAKBANK","AXISBANK",
    "SBIN","HINDUNILVR","BHARTIARTL","BAJFINANCE","MARUTI","HCLTECH",
    "WIPRO","ADANIENT","ADANIPORTS","ULTRACEMCO","ASIANPAINT","TITAN","NESTLEIND",
    "TECHM","SUNPHARMA","DIVISLAB","DRREDDY","CIPLA","BAJAJFINSV","ONGC",
    "NTPC","POWERGRID","COALINDIA","GRASIM","JSWSTEEL","TATASTEEL","HINDALCO",
    "VEDL","M&M","EICHERMOT","HEROMOTOCO","BAJAJ-AUTO","BPCL","IOC","GAIL",
    "TATAPOWER","SIEMENS","ABB","HAVELLS","VOLTAS",
    # Banking & NBFC
    "BANKBARODA","INDUSINDBK","FEDERALBNK","IDFCFIRSTB","RBLBANK","BANDHANBNK",
    "CANBK","UNIONBANK","PNB","AUBANK","CHOLAFIN","MUTHOOTFIN","MANAPPURAM",
    "LICSGFIN","SBICARD","PIRAMALENT","MASFIN","ABCAPITAL","ANGELONE","CDSL",
    # IT & Tech
    "MPHASIS","LTIM","PERSISTENT","COFORGE","OFSS","KPITTECH","ZENSARTECH",
    "TATAELXSI","LTTS","CYIENT",
    # Auto & Auto-ancillary
    "TVSMOTOR","MOTHERSON","BOSCHLTD","APOLLOTYRE","MRF","CEATLTD","BHARATFORG",
    "BALKRISIND","ASHOKLEY","SUNDARMFIN","ENDURANCE","SCHAEFFLER","TIMKEN","SKFINDIA",
    # Pharma & Healthcare
    "AUROPHARMA","LUPIN","BIOCON","ALKEM","TORNTPHARM","GLENMARK","IPCALAB",
    "NATCOPHARM","LALPATHLAB","METROPOLIS","MAXHEALTH","FORTIS","APOLLOHOSP",
    # Metal & Mining
    "SAIL","NATIONALUM","JINDALSTEL","NMDC","HINDZINC","MOIL","WELCORP","RATNAMANI",
    # Energy & Utilities
    "PETRONET","OIL","CESC","TORNTPOWER","ADANIGREEN","TPWR",
    # FMCG & Beverages
    "BRITANNIA","DABUR","MARICO","GODREJCP","COLPAL","EMAMILTD","VBL",
    "RADICO","UBL","MCDOWELL-N","TATACONSUM",
    # Realty
    "DLF","GODREJPROP","PRESTIGE","OBEROIRLTY","PHOENIXLTD","BRIGADE","SOBHA",
    "MAHINDCIE","SUNTECK",
    # Capital Goods & Infra
    "BHEL","CUMMINSIND","THERMAX","BEL","HAL","BEML","NCC","KNRCON",
    "AIAENG","GMRINFRA","IRB","GRINFRA","POLYCAB","KEI","FINOLEX",
    # Cement
    "SHREECEM","AMBUJACEM","ACC","RAMCOCEM","JKCEMENT","DALMIA","HEIDELBERG",
    "JKLAKSHMI","ORIENTCEM",
    # Telecom
    "IDEA","TATACOMM","HFCL",
    # Chemical
    "PIDILITIND","AARTIIND","DEEPAKNTR","VINATIORGA","FINEORG","NAVINFLUOR",
    "ALKYLAMINE","CLEAN","SRF","SUDARSCHEM","TATACHEM","GNFC","GSPL",
    "CHAMBLFERT","COROMANDEL","NFL","RCF","FACT","EIDPARRY","BALRAMCHIN",
    # Consumer Durables & Retail
    "BATAINDIA","PAGEIND","VGUARD","CROMPTON","ORIENTELEC","TRENT","DMART",
    "SHOPERSTOP","METRO","PATANJALI",
    # PSU & Defence
    "CONCOR","IRCTC","RVNL","RITES","IRFC","BDL","MAZAGON","COCHINSHIP",
    # Diversified mid-cap
    "MFSL","POLICYBZR","NYKAA","ZOMATO","INDIGO","PVR","INOXLEISUR",
    "JUSTDIAL","RATEGAIN","DELHIVERY","CAMPUS","NIACL","BSE","MCDOWELL-N",
    "GLOBUSSPR","HINDPETRO","MRPL","CHENNPETRO","ASTRAL","SUPREMEIND",
    "POLYPLEX","NOCIL","ATUL","GALAXYSURF","ZEEL","SUNTV","SAREGAMA",
    "SPARC","STRIDES","GRANULES","SOLARA","AAVAS","CREDITACC","SPANDANA",
    "LICI","GICRE","NIACL","STARHEALTH","SBILIFE","HDFCLIFE","ICICIGI",
]


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_live_fno_list() -> list:
    """
    1. Try NSE public API for live F&O list.
    2. On failure, fall back to FALLBACK_FNO_SYMBOLS.
    Returns list of bare symbols (no .NS suffix), deduplicated and sorted.
    """
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=8)
        resp = session.get(NSE_FNO_URL, headers=NSE_HEADERS, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        symbols = [
            item["symbol"].strip()
            for item in data.get("data", [])
            if item.get("symbol") and item["symbol"] not in ("NIFTY 50", "NIFTY")
        ]
        if len(symbols) > 50:
            return sorted(set(symbols))
    except Exception:
        pass
    # Fallback
    return sorted(set(FALLBACK_FNO_SYMBOLS))


def get_fno_tickers(symbols: list) -> list:
    """Convert bare NSE symbols → yfinance .NS tickers."""
    return [s + ".NS" for s in symbols]


@st.cache_data(ttl=60, show_spinner=False)
def fetch_ohlcv(ticker: str, period: str = "5d", interval: str = "5m"):
    """
    Download OHLCV for a single ticker.
    Bad/delisted tickers are skipped silently.
    """

    BAD_TICKERS = {
        "TPWR.NS",
        "INOXLEISUR.NS",
        "MASFIN.NS",
        "PATANJALI.NS",
    }

    if ticker in BAD_TICKERS:
        return None

    try:
        import contextlib
        import io

        buffer = io.StringIO()

        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            df = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
                threads=False,
            )

        if df is None or df.empty:
            return None

        df.columns = [
            c[0] if isinstance(c, tuple) else c
            for c in df.columns
        ]

        df = df.dropna(subset=["Close", "Volume"])

        if len(df) < 20:
            return None

        return df

    except Exception:
        return None


def fetch_index_data(ticker: str):
    return fetch_ohlcv(ticker, period="5d", interval="5m")


def get_ist_time() -> str:
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).strftime("%d-%b-%Y %H:%M:%S IST")
