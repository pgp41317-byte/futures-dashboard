"""
option_chain.py
Fetches NIFTY option chain from NSE public API.
Computes PCR and max-pain level.
"""

import requests
import streamlit as st

NSE_OC_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer":    "https://www.nseindia.com/",
    "Accept":     "application/json",
}


@st.cache_data(ttl=120, show_spinner=False)
def fetch_option_chain() -> dict:
    """Returns {"pcr": float, "max_pain": float, "bias": str, "status": str}"""
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=6)
        resp = session.get(NSE_OC_URL, headers=NSE_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        records = data["records"]["data"]
        ce_oi   = sum(r.get("CE", {}).get("openInterest", 0) for r in records if "CE" in r)
        pe_oi   = sum(r.get("PE", {}).get("openInterest", 0) for r in records if "PE" in r)
        pcr     = round(pe_oi / ce_oi, 2) if ce_oi > 0 else 1.0

        strikes = {}
        for r in records:
            s = r.get("strikePrice", 0)
            strikes[s] = {
                "ce": r.get("CE", {}).get("openInterest", 0),
                "pe": r.get("PE", {}).get("openInterest", 0),
            }
        max_pain = _calc_max_pain(strikes) if strikes else 0
        bias     = "BULLISH" if pcr > 1.2 else ("BEARISH" if pcr < 0.8 else "NEUTRAL")
        return {"pcr": pcr, "max_pain": max_pain, "bias": bias, "status": "live"}

    except Exception as e:
        return {"pcr": 1.0, "max_pain": 0, "bias": "NEUTRAL",
                "status": f"unavailable ({str(e)[:40]})"}


def _calc_max_pain(strikes: dict) -> float:
    pain = {}
    for s in strikes:
        total = 0
        for k, v in strikes.items():
            total += max(0, s - k) * v["ce"]
            total += max(0, k - s) * v["pe"]
        pain[s] = total
    return min(pain, key=pain.get) if pain else 0
