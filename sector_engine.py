"""
sector_engine.py
Sector-level strength using member stock daily price changes.
"""

import yfinance as yf
import streamlit as st
from config import SECTOR_MAP


@st.cache_data(ttl=180, show_spinner=False)
def compute_sector_strength() -> dict:
    """
    Returns {sector: {"avg_chg": float, "signal": str, "members_ok": int}}
    Uses first 5 members of each sector to keep API calls light.
    """
    results = {}
    for sector, symbols in SECTOR_MAP.items():
        tickers = [s + ".NS" for s in symbols[:5]]
        changes = []
        for t in tickers:
            try:
                df = yf.download(
                    t, period="2d", interval="1d",
                    progress=False, auto_adjust=True
                )
                if df is not None and len(df) >= 2:
                    df.columns = [
                        c[0] if isinstance(c, tuple) else c
                        for c in df.columns
                    ]
                    chg = (
                        float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-2])
                    ) / float(df["Close"].iloc[-2]) * 100
                    changes.append(chg)
            except Exception:
                pass
        if changes:
            avg = sum(changes) / len(changes)
            sig = "STRONG ▲" if avg > 0.5 else ("WEAK ▼" if avg < -0.5 else "NEUTRAL ─")
            results[sector] = {
                "avg_chg": round(avg, 2),
                "signal": sig,
                "members_ok": len(changes),
            }
        else:
            results[sector] = {"avg_chg": 0.0, "signal": "N/A", "members_ok": 0}
    return results


def get_stock_sector(symbol: str) -> str:
    bare = symbol.replace(".NS", "")
    for sector, members in SECTOR_MAP.items():
        if bare in members:
            return sector
    return "Other"
