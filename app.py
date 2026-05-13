"""
app.py — NSE F&O Futures Intraday Signal Dashboard
Bloomberg-style dark theme.  Auto-refreshes every 5 seconds.
Scans the FULL live NSE F&O universe each cycle.
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import traceback

from config         import REFRESH_INTERVAL, NIFTY_TICKER, BANKNIFTY_TICKER
from styles         import inject_css, signal_badge, sentiment_badge, news_cls
from data_fetcher   import get_ist_time
from signal_engine  import get_index_signal, scan_full_universe
from news_sentiment import fetch_news, get_market_sentiment
from sector_engine  import compute_sector_strength
from option_chain   import fetch_option_chain

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NSE F&O Futures Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()
st_autorefresh(interval=REFRESH_INTERVAL * 1000, key="main_refresh")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""<div class="dash-title">
    📊 &nbsp;NSE F&amp;O FUTURES INTRADAY SIGNAL DASHBOARD
    <span style="font-size:0.8rem;color:#8b949e;float:right;font-weight:400;">
    🕐 {get_ist_time()}
    </span>
    </div>""",
    unsafe_allow_html=True,
)
st.caption(
    "⚠️  For educational purposes only · Does NOT guarantee profits · "
    "Always apply your own judgment · "
    "Signals use cash-market data as proxy for futures · Not SEBI-registered advice"
)

# ── Load all data ─────────────────────────────────────────────────────────────
load_error  = None
nifty_sig   = {}
bnf_sig     = {}
headlines   = []
mkt_sent    = {"label": "NEUTRAL", "bias": "Sideways", "score": 0}
sector_data = {}
oc_data     = {}
scan_result = {"top_buy": [], "top_sell": [], "top_conviction": [],
               "all_signals": [], "scanned": 0, "skipped": 0,
               "skipped_list": [], "universe_size": 0}

with st.spinner("🔍 Scanning full NSE F&O universe …"):
    try:
        nifty_sig   = get_index_signal(NIFTY_TICKER,    "NIFTY")
        bnf_sig     = get_index_signal(BANKNIFTY_TICKER,"BANKNIFTY")
        headlines   = fetch_news()
        mkt_sent    = get_market_sentiment(headlines)
        sector_data = compute_sector_strength()
        oc_data     = fetch_option_chain()
        scan_result = scan_full_universe()
    except Exception:
        load_error = traceback.format_exc()

if load_error:
    st.error(
        f"Partial load error — some cards may be empty.\n\n{load_error[:400]}"
    )

# ── Helper: signal colour ─────────────────────────────────────────────────────
def _sc(sig):
    return "#3fb950" if sig == "BUY" else ("#f85149" if sig == "SELL" else "#8b949e")


# ── Top status bar ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">MARKET OVERVIEW</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    ns = nifty_sig.get("signal", "—")
    st.markdown(
        f"""<div class="sig-card">
        <h4>NIFTY 50</h4>
        <div class="val" style="color:{_sc(ns)}">{ns}</div>
        <div style="font-size:0.75rem;color:#8b949e">
            ₹{nifty_sig.get('close','—')} &nbsp;|&nbsp; RSI {nifty_sig.get('rsi','—')}
        </div></div>""",
        unsafe_allow_html=True,
    )

with c2:
    bs = bnf_sig.get("signal", "—")
    st.markdown(
        f"""<div class="sig-card">
        <h4>BANKNIFTY</h4>
        <div class="val" style="color:{_sc(bs)}">{bs}</div>
        <div style="font-size:0.75rem;color:#8b949e">
            ₹{bnf_sig.get('close','—')} &nbsp;|&nbsp; RSI {bnf_sig.get('rsi','—')}
        </div></div>""",
        unsafe_allow_html=True,
    )

with c3:
    ml  = mkt_sent.get("label", "NEUTRAL")
    mc  = "#3fb950" if ml == "POSITIVE" else ("#f85149" if ml == "NEGATIVE" else "#d29922")
    st.markdown(
        f"""<div class="sig-card">
        <h4>MARKET SENTIMENT</h4>
        <div class="val" style="color:{mc}">{mkt_sent.get('bias','—')}</div>
        <div style="font-size:0.75rem;color:#8b949e">Score {mkt_sent.get('score','—')}</div>
        </div>""",
        unsafe_allow_html=True,
    )

with c4:
    pcr   = oc_data.get("pcr", "—")
    pbias = oc_data.get("bias", "—")
    pc    = "#3fb950" if pbias == "BULLISH" else ("#f85149" if pbias == "BEARISH" else "#d29922")
    st.markdown(
        f"""<div class="sig-card">
        <h4>OPTION CHAIN PCR</h4>
        <div class="val" style="color:{pc}">{pcr}</div>
        <div style="font-size:0.75rem;color:#8b949e">
            {pbias} &nbsp;|&nbsp; MaxPain {oc_data.get('max_pain','—')}
        </div></div>""",
        unsafe_allow_html=True,
    )

with c5:
    scanned = scan_result.get("scanned", 0)
    skipped = scan_result.get("skipped", 0)
    univ    = scan_result.get("universe_size", 0)
    st.markdown(
        f"""<div class="sig-card">
        <h4>UNIVERSE SCANNED</h4>
        <div class="val" style="color:#f0b429">{scanned}</div>
        <div style="font-size:0.75rem;color:#8b949e">
            of {univ} F&amp;O stocks &nbsp;|&nbsp; skipped {skipped}
        </div></div>""",
        unsafe_allow_html=True,
    )

st.markdown("---")


# ── Signal table renderer ─────────────────────────────────────────────────────

def _render_signal_table(signals: list, title: str):
    if not signals:
        st.info(f"No {title} signals this cycle — market conditions not met.")
        return

    rows = []
    for s in signals:
        rows.append({
            "Symbol":      s.get("symbol", ""),
            "Signal":      s.get("signal", ""),
            "Entry ₹":     s.get("entry", ""),
            "SL ₹":        s.get("sl", ""),
            "Target 1 ₹":  s.get("t1", ""),
            "Target 2 ₹":  s.get("t2", ""),
            "R:R":         s.get("rr", ""),
            "Confidence":  f"{s.get('confidence', 0):.0f}%",
            "RSI":         s.get("rsi", ""),
            "Vol Ratio":   s.get("vol_ratio", ""),
            "Chg %":       s.get("chg_pct", ""),
            "Sector":      s.get("sector", ""),
            "Qty (est)":   s.get("qty", ""),
            "Reason":      (s.get("reason", "") or "")[:60],
        })

    df = pd.DataFrame(rows)

    def _row_style(row):
        sig = row["Signal"]
        if sig == "BUY":
            return ["background-color:#0d2117; color:#3fb950"] + [""] * (len(row) - 1)
        if sig == "SELL":
            return ["background-color:#200d0d; color:#f85149"] + [""] * (len(row) - 1)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(_row_style, axis=1),
        use_container_width=True,
        hide_index=True,
    )


# ── Top BUY setups ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">TOP 5 BUY SETUPS</div>', unsafe_allow_html=True)
_render_signal_table(scan_result.get("top_buy", []), "BUY")

# ── Top SELL setups ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">TOP 5 SELL SETUPS</div>', unsafe_allow_html=True)
_render_signal_table(scan_result.get("top_sell", []), "SELL")

# ── High conviction ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">TOP 5 HIGH-CONVICTION TRADES</div>', unsafe_allow_html=True)
_render_signal_table(scan_result.get("top_conviction", []), "high-conviction")

st.markdown("---")

# ── Full scan summary ─────────────────────────────────────────────────────────
with st.expander("📋 Full Scan Summary — all signals this cycle"):
    all_sigs = scan_result.get("all_signals", [])
    if all_sigs:
        summary_rows = []
        for s in sorted(all_sigs, key=lambda x: max(x.get("bull_score",0), x.get("bear_score",0)), reverse=True):
            summary_rows.append({
                "Symbol":     s.get("symbol",""),
                "Signal":     s.get("signal",""),
                "Bull Score": s.get("bull_score",0),
                "Bear Score": s.get("bear_score",0),
                "Confidence": f"{s.get('confidence',0):.0f}%",
                "RSI":        s.get("rsi",""),
                "Chg %":      s.get("chg_pct",""),
                "Sector":     s.get("sector",""),
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No scan data yet.")

# ── Sector strength ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">SECTOR STRENGTH</div>', unsafe_allow_html=True)
if sector_data:
    sec_rows = [
        {
            "Sector":   sec,
            "Avg Chg %": v["avg_chg"],
            "Signal":    v["signal"],
            "Members OK": v["members_ok"],
        }
        for sec, v in sector_data.items()
    ]
    sec_df = pd.DataFrame(sec_rows)

    def _sec_style(row):
        sig = row["Signal"]
        if "▲" in str(sig): return ["", "color:#3fb950", "", ""]
        if "▼" in str(sig): return ["", "color:#f85149", "", ""]
        return [""] * 4

    st.dataframe(
        sec_df.style.apply(_sec_style, axis=1),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")

# ── News sentiment ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">LATEST MARKET NEWS & SENTIMENT</div>', unsafe_allow_html=True)
if headlines:
    for h in headlines[:100]:
        cls   = news_cls(h["label"])
        badge = sentiment_badge(h["label"])
        st.markdown(
            f'<div class="news-card {cls}">'
            f'{badge} &nbsp; {h["title"]}'
            f'<span style="float:right;font-size:0.68rem;color:#8b949e">{h["source"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
else:
    st.info("News feeds currently unavailable — check internet connection.")

st.markdown("---")

# ── Skipped stocks ────────────────────────────────────────────────────────────
with st.expander(f"⚠️  Skipped / Unavailable Stocks ({scan_result.get('skipped', 0)})"):
    skipped_list = scan_result.get("skipped_list", [])
    if skipped_list:
        st.write(", ".join(skipped_list))
    else:
        st.success("None — full F&O universe scanned successfully ✓")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;color:#30363d;font-size:0.7rem;margin-top:30px;">'
    'NSE F&amp;O Futures Dashboard &nbsp;·&nbsp; '
    'Auto-refresh every 5 s &nbsp;·&nbsp; '
    'Educational use only &nbsp;·&nbsp; '
    'Not SEBI-registered investment advice'
    '</div>',
    unsafe_allow_html=True,
)
