"""
indicators.py
Computes 20+ technical indicators on a 5-minute OHLCV DataFrame.
All computations are vectorised; no external TA library required.
"""

import pandas as pd
import numpy as np


def _s(series, n=-1):
    """Safely extract a scalar from a Series."""
    try:
        v = float(series.iloc[n])
        return v if np.isfinite(v) else None
    except Exception:
        return None


def compute_indicators(df: pd.DataFrame) -> dict:
    """Return a dict of pd.Series (indicator arrays) for the full DataFrame."""
    if df is None or len(df) < 20:
        return {}

    close  = df["Close"].astype(float)
    high   = df["High"].astype(float)
    low    = df["Low"].astype(float)
    volume = df["Volume"].astype(float)
    open_  = df["Open"].astype(float)

    ind = {}

    # ── EMAs ──────────────────────────────────────────────────────────────────
    ind["ema9"]  = close.ewm(span=9,  adjust=False).mean()
    ind["ema20"] = close.ewm(span=20, adjust=False).mean()
    ind["ema50"] = close.ewm(span=50, adjust=False).mean()

    # ── VWAP (resets each calendar day) ───────────────────────────────────────
    try:
        df2 = df.copy()
        df2["date"] = df2.index.normalize()
        df2["tp"]   = (df2["High"] + df2["Low"] + df2["Close"]) / 3
        df2["tpv"]  = df2["tp"] * df2["Volume"]
        df2["cum_tpv"] = df2.groupby("date")["tpv"].transform("cumsum")
        df2["cum_vol"] = df2.groupby("date")["Volume"].transform("cumsum")
        ind["vwap"] = df2["cum_tpv"] / df2["cum_vol"]
    except Exception:
        ind["vwap"] = close.rolling(20).mean()

    # ── RSI 14 ─────────────────────────────────────────────────────────────────
    delta = close.diff()
    gain  = delta.clip(lower=0).ewm(span=14, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(span=14, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    ind["rsi"] = 100 - (100 / (1 + rs))

    # ── MACD ───────────────────────────────────────────────────────────────────
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd  = ema12 - ema26
    sig   = macd.ewm(span=9, adjust=False).mean()
    ind["macd"]        = macd
    ind["macd_signal"] = sig
    ind["macd_hist"]   = macd - sig

    # ── ATR 14 ─────────────────────────────────────────────────────────────────
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    ind["atr"] = tr.ewm(span=14, adjust=False).mean()

    # ── Bollinger Bands (20, 2σ) ───────────────────────────────────────────────
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    ind["bb_upper"] = bb_mid + 2 * bb_std
    ind["bb_lower"] = bb_mid - 2 * bb_std
    ind["bb_mid"]   = bb_mid

    # ── Supertrend (period=7, mult=3) ─────────────────────────────────────────
    atr14   = ind["atr"]
    hl2     = (high + low) / 2
    ub_raw  = hl2 + 3 * atr14
    lb_raw  = hl2 - 3 * atr14

    ub = ub_raw.copy()
    lb = lb_raw.copy()
    direction  = pd.Series(1, index=close.index)
    supertrend = pd.Series(np.nan, index=close.index)

    for i in range(1, len(close)):
        ub.iloc[i] = ub_raw.iloc[i] if (ub_raw.iloc[i] < ub.iloc[i-1] or close.iloc[i-1] > ub.iloc[i-1]) else ub.iloc[i-1]
        lb.iloc[i] = lb_raw.iloc[i] if (lb_raw.iloc[i] > lb.iloc[i-1] or close.iloc[i-1] < lb.iloc[i-1]) else lb.iloc[i-1]
        if supertrend.iloc[i-1] == ub.iloc[i-1]:
            direction.iloc[i] = -1 if close.iloc[i] > ub.iloc[i] else -1
            direction.iloc[i] = 1  if close.iloc[i] > ub.iloc[i] else -1
        else:
            direction.iloc[i] = -1 if close.iloc[i] < lb.iloc[i] else 1
        supertrend.iloc[i] = lb.iloc[i] if direction.iloc[i] == 1 else ub.iloc[i]

    ind["supertrend"]     = supertrend
    ind["supertrend_dir"] = direction

    # ── Volume ratio ───────────────────────────────────────────────────────────
    vol_avg = volume.rolling(20).mean().replace(0, np.nan)
    ind["volume_ratio"] = volume / vol_avg

    # ── Opening Range Breakout (first 30 min = 6 × 5m bars) ───────────────────
    try:
        today     = df.index.normalize()[-1]
        today_df  = df[df.index.normalize() == today]
        orb_high  = float(today_df["High"].iloc[:6].max())
        orb_low   = float(today_df["Low"].iloc[:6].min())
    except Exception:
        orb_high  = float(high.rolling(6).max().iloc[-1])
        orb_low   = float(low.rolling(6).min().iloc[-1])
    ind["orb_high"] = pd.Series(orb_high, index=df.index)
    ind["orb_low"]  = pd.Series(orb_low,  index=df.index)

    # ── Day high / low ─────────────────────────────────────────────────────────
    try:
        today    = df.index.normalize()[-1]
        today_df = df[df.index.normalize() == today]
        ind["day_high"] = float(today_df["High"].max())
        ind["day_low"]  = float(today_df["Low"].min())
    except Exception:
        ind["day_high"] = float(high.rolling(78).max().iloc[-1])
        ind["day_low"]  = float(low.rolling(78).min().iloc[-1])

    # ── Gap from previous close ────────────────────────────────────────────────
    ind["prev_close"] = float(close.iloc[-2]) if len(close) >= 2 else float(close.iloc[-1])
    try:
        today     = df.index.normalize()[-1]
        today_df  = df[df.index.normalize() == today]
        today_open = float(today_df["Open"].iloc[0])
        ind["gap_pct"] = (today_open - ind["prev_close"]) / ind["prev_close"] * 100
    except Exception:
        ind["gap_pct"] = 0.0

    # ── Intraday price change % ────────────────────────────────────────────────
    ind["chg_pct"] = (float(close.iloc[-1]) - ind["prev_close"]) / ind["prev_close"] * 100

    # ── Candle body strength ───────────────────────────────────────────────────
    body   = (close - open_).abs()
    rng    = (high - low).replace(0, np.nan)
    ind["candle_strength"] = body / rng

    # ── Trend strength (R² over last 20 bars) ─────────────────────────────────
    x = np.arange(20, dtype=float)
    y = close.values[-20:].astype(float)
    if len(y) == 20:
        xm, ym  = x.mean(), y.mean()
        ss_tot  = ((y - ym)**2).sum()
        coeffs  = np.polyfit(x, y, 1)
        ss_res  = ((y - np.polyval(coeffs, x))**2).sum()
        ind["trend_strength"] = float(max(0.0, 1 - ss_res / ss_tot)) if ss_tot > 0 else 0.0
    else:
        ind["trend_strength"] = 0.0

    return ind


def extract_scalars(ind: dict, df: pd.DataFrame) -> dict:
    """Collapse all Series to their latest scalar value."""

    def last(key):
        s = ind.get(key)
        if s is None:
            return None
        if isinstance(s, pd.Series):
            return _s(s, -1)
        try:
            v = float(s)
            return v if np.isfinite(v) else None
        except Exception:
            return None

    return {
        "close":          float(df["Close"].iloc[-1]),
        "ema9":           last("ema9"),
        "ema20":          last("ema20"),
        "ema50":          last("ema50"),
        "vwap":           last("vwap"),
        "rsi":            last("rsi"),
        "macd":           last("macd"),
        "macd_signal":    last("macd_signal"),
        "macd_hist":      last("macd_hist"),
        "atr":            last("atr"),
        "bb_upper":       last("bb_upper"),
        "bb_lower":       last("bb_lower"),
        "bb_mid":         last("bb_mid"),
        "supertrend":     last("supertrend"),
        "supertrend_dir": last("supertrend_dir"),
        "volume_ratio":   last("volume_ratio"),
        "orb_high":       last("orb_high"),
        "orb_low":        last("orb_low"),
        "day_high":       ind.get("day_high"),
        "day_low":        ind.get("day_low"),
        "prev_close":     ind.get("prev_close"),
        "gap_pct":        ind.get("gap_pct", 0.0),
        "chg_pct":        ind.get("chg_pct", 0.0),
        "candle_strength":last("candle_strength"),
        "trend_strength": ind.get("trend_strength", 0.0),
    }
