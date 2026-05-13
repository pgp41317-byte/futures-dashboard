"""
signal_engine.py
Core scoring and signal generation engine.
scan_full_universe() fetches the live NSE F&O list every call and scans
every symbol independently — one failure never stops the rest.
"""

import numpy as np
import streamlit as st

from config import (
    BULL_SCORE_THRESHOLD, BEAR_SCORE_THRESHOLD,
    MIN_VOLUME_RATIO, MIN_RISK_REWARD,
    ATR_SL_MULT, ATR_T1_MULT, ATR_T2_MULT,
    DEFAULT_CAPITAL, MAX_RISK_PCT,
    INTRADAY_PERIOD, INTRADAY_INTERVAL,
)
from data_fetcher    import fetch_ohlcv, fetch_live_fno_list, get_fno_tickers
from indicators      import compute_indicators, extract_scalars
from news_sentiment  import fetch_news, get_stock_sentiment
from sector_engine   import get_stock_sector


# ─────────────────────────────────────────────────────────────────────────────
# Index signal
# ─────────────────────────────────────────────────────────────────────────────

def get_index_signal(ticker: str, label: str) -> dict:
    df = fetch_ohlcv(ticker, period=INTRADAY_PERIOD, interval=INTRADAY_INTERVAL)
    if df is None:
        return {"symbol": label, "signal": "NO DATA", "score": 0,
                "close": 0, "reason": "Data unavailable", "atr": 0}
    ind  = compute_indicators(df)
    sc   = extract_scalars(ind, df)
    bull, bear, reasons = _score(sc, 0)
    signal = _decide_signal(bull, bear, sc)
    return {
        "symbol":     label,
        "signal":     signal,
        "bull_score": bull,
        "bear_score": bear,
        "close":      round(sc["close"], 2),
        "rsi":        round(sc["rsi"], 1)   if sc.get("rsi")  else None,
        "vwap":       round(sc["vwap"], 2)  if sc.get("vwap") else None,
        "atr":        round(sc["atr"], 2)   if sc.get("atr")  else None,
        "reason":     "; ".join(reasons[:3]) or "Insufficient data",
    }

@st.cache_data(ttl=300, show_spinner=False)
# ─────────────────────────────────────────────────────────────────────────────
# Full F&O universe scan (runs every refresh cycle)
# ─────────────────────────────────────────────────────────────────────────────

def scan_full_universe() -> dict:
    """
    1. Fetches the live NSE F&O list (or fallback ~200 symbols).
    2. Downloads 5m OHLCV for every symbol independently.
    3. Computes 20+ indicators and a bull/bear score for each.
    4. Returns ranked BUY / SELL / high-conviction lists.

    One bad symbol is skipped silently — the scan continues.
    """
    symbols   = fetch_live_fno_list()
    tickers   = get_fno_tickers(symbols)
    headlines = fetch_news()

    all_signals = []
    skipped     = []

    for ticker in tickers:
        try:
            result = _analyse_stock(ticker, headlines)
            if result:
                all_signals.append(result)
            else:
                skipped.append(ticker)
        except Exception:
            skipped.append(ticker)

    buy_signals  = sorted(
        [s for s in all_signals if s["signal"] == "BUY"],
        key=lambda x: x.get("bull_score", 0), reverse=True
    )
    sell_signals = sorted(
        [s for s in all_signals if s["signal"] == "SELL"],
        key=lambda x: x.get("bear_score", 0), reverse=True
    )
    conviction = sorted(
        [s for s in all_signals if s["signal"] in ("BUY", "SELL")],
        key=lambda x: max(x.get("bull_score", 0), x.get("bear_score", 0)),
        reverse=True
    )

    return {
        "top_buy":        buy_signals[:5],
        "top_sell":       sell_signals[:5],
        "top_conviction": conviction[:5],
        "all_signals":    all_signals,
        "scanned":        len(all_signals),
        "skipped":        len(skipped),
        "skipped_list":   skipped,
        "universe_size":  len(tickers),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Per-stock analysis
# ─────────────────────────────────────────────────────────────────────────────

def _analyse_stock(ticker: str, headlines: list):
    df = fetch_ohlcv(ticker, period=INTRADAY_PERIOD, interval=INTRADAY_INTERVAL)
    if df is None:
        return None

    ind = compute_indicators(df)
    sc  = extract_scalars(ind, df)
    if not sc or not sc.get("atr") or sc["atr"] == 0:
        return None

    news_sent = get_stock_sentiment(headlines, ticker)
    sector    = get_stock_sector(ticker)

    bull, bear, reasons = _score(sc, news_sent)
    signal = _decide_signal(bull, bear, sc)

    entry = sc["close"]
    atr   = sc["atr"]
    risk  = atr * ATR_SL_MULT

    if signal == "BUY":
        sl = round(entry - risk, 2)
        t1 = round(entry + risk * ATR_T1_MULT, 2)
        t2 = round(entry + risk * ATR_T2_MULT, 2)
        rr = round((t1 - entry) / risk, 2) if risk > 0 else 0
    elif signal == "SELL":
        sl = round(entry + risk, 2)
        t1 = round(entry - risk * ATR_T1_MULT, 2)
        t2 = round(entry - risk * ATR_T2_MULT, 2)
        rr = round((entry - t1) / risk, 2) if risk > 0 else 0
    else:
        sl = t1 = t2 = rr = 0

    max_loss = DEFAULT_CAPITAL * MAX_RISK_PCT
    qty      = int(max_loss / risk) if risk > 0 else 0

    return {
        "symbol":     ticker.replace(".NS", ""),
        "ticker":     ticker,
        "sector":     sector,
        "signal":     signal,
        "entry":      round(entry, 2),
        "sl":         sl,
        "t1":         t1,
        "t2":         t2,
        "rr":         rr,
        "qty":        qty,
        "bull_score": bull,
        "bear_score": bear,
        "confidence": max(bull, bear),
        "rsi":        round(sc["rsi"], 1)         if sc.get("rsi")          else None,
        "vwap":       round(sc["vwap"], 2)        if sc.get("vwap")         else None,
        "atr":        round(sc["atr"], 2),
        "vol_ratio":  round(sc["volume_ratio"], 2) if sc.get("volume_ratio") else None,
        "chg_pct":    round(sc.get("chg_pct", 0), 2),
        "reason":     "; ".join(reasons[:4]) or "Computed signal",
        "note":       "Signal approximated using cash market momentum.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Scoring model  (0-100 for bull and bear independently)
# ─────────────────────────────────────────────────────────────────────────────

def _score(sc: dict, news_sent: int):
    bull    = 0
    bear    = 0
    reasons = []

    close  = sc.get("close") or 0
    vwap   = sc.get("vwap")
    ema9   = sc.get("ema9")
    ema20  = sc.get("ema20")
    ema50  = sc.get("ema50")
    rsi    = sc.get("rsi")
    macdh  = sc.get("macd_hist")
    vol_r  = sc.get("volume_ratio")
    day_h  = sc.get("day_high")
    day_l  = sc.get("day_low")
    supt   = sc.get("supertrend_dir")
    orb_h  = sc.get("orb_high")
    orb_l  = sc.get("orb_low")
    ts     = sc.get("trend_strength", 0) or 0

    # VWAP (12 pts)
    if vwap:
        if close > vwap:
            bull += 12; reasons.append("Above VWAP")
        else:
            bear += 12; reasons.append("Below VWAP")

    # EMA 20 (10 pts)
    if ema20:
        if close > ema20:
            bull += 10; reasons.append("Close > EMA20")
        else:
            bear += 10; reasons.append("Close < EMA20")

    # EMA 9/20 cross (8 pts)
    if ema9 and ema20:
        if ema9 > ema20:
            bull += 8; reasons.append("EMA9 > EMA20")
        else:
            bear += 8; reasons.append("EMA9 < EMA20")

    # EMA 50 trend (4 pts)
    if ema50:
        if close > ema50:
            bull += 4
        else:
            bear += 4

    # RSI (10 pts)
    if rsi is not None:
        if   rsi > 65: bull += 10; reasons.append(f"RSI {rsi:.0f} strong")
        elif rsi > 55: bull +=  6; reasons.append(f"RSI {rsi:.0f}")
        elif rsi < 35: bear += 10; reasons.append(f"RSI {rsi:.0f} weak")
        elif rsi < 45: bear +=  6; reasons.append(f"RSI {rsi:.0f}")

    # MACD histogram (8 pts)
    if macdh is not None:
        if macdh > 0:
            bull += 8; reasons.append("MACD positive")
        else:
            bear += 8; reasons.append("MACD negative")

    # Volume ratio (8 pts each direction on spike, confirms trend)
    if vol_r is not None:
        if vol_r >= 2.0:
            bull += 8; bear += 8; reasons.append(f"Vol spike {vol_r:.1f}x")
        elif vol_r >= 1.5:
            bull += 5; bear += 5; reasons.append(f"High volume {vol_r:.1f}x")
        elif vol_r >= 1.3:
            bull += 3; bear += 3

    # Day high/low proximity (8 pts)
    if day_h and day_l and close:
        rng = day_h - day_l
        if rng > 0:
            pos = (close - day_l) / rng
            if pos > 0.85:
                bull += 8; reasons.append("Near day high")
            elif pos < 0.15:
                bear += 8; reasons.append("Near day low")

    # ORB breakout (6 pts)
    if orb_h and orb_l:
        if close > orb_h:
            bull += 6; reasons.append("ORB breakout ▲")
        elif close < orb_l:
            bear += 6; reasons.append("ORB breakdown ▼")

    # Supertrend (10 pts)
    if supt is not None:
        if supt > 0:
            bull += 10; reasons.append("Supertrend bullish")
        else:
            bear += 10; reasons.append("Supertrend bearish")

    # Trend strength R² bonus (up to 6 pts)
    if ts > 0.8:
        bull += 6; bear += 6
    elif ts > 0.6:
        bull += 3; bear += 3

    # News sentiment (up to 10 pts)
    if news_sent > 0:
        bull += min(news_sent * 5, 10); reasons.append("Positive news")
    elif news_sent < 0:
        bear += min(abs(news_sent) * 5, 10); reasons.append("Negative news")

    return min(bull, 100), min(bear, 100), reasons


# ─────────────────────────────────────────────────────────────────────────────
# Final signal decision gate
# ─────────────────────────────────────────────────────────────────────────────

def _decide_signal(bull: int, bear: int, sc: dict) -> str:
    close = sc.get("close", 0)
    vwap  = sc.get("vwap")
    ema20 = sc.get("ema20")
    vol_r = sc.get("volume_ratio") or 0
    atr   = sc.get("atr") or 0

    # Hard filters
    if atr == 0 or vol_r < MIN_VOLUME_RATIO:
        return "NO TRADE"

    bull_ok = (
        bull >= BULL_SCORE_THRESHOLD
        and vwap  and close > vwap
        and ema20 and close > ema20
    )
    bear_ok = (
        bear >= BEAR_SCORE_THRESHOLD
        and vwap  and close < vwap
        and ema20 and close < ema20
    )

    if bull_ok and bull > bear:
        return "BUY"
    if bear_ok and bear > bull:
        return "SELL"
    return "NO TRADE"
