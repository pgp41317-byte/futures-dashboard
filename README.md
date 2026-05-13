# NSE F&O Futures Intraday Signal Dashboard

Bloomberg-style Streamlit dashboard.
Dynamically fetches the **full NSE F&O universe** from NSE's public API every session,
then scans every eligible stock and ranks signals every 5 seconds.

## Quick Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Key features
* Live F&O list from NSE (200+ symbols) with comprehensive hardcoded fallback
* Top 5 BUY / SELL / High-Conviction signals with entry, SL, T1, T2, R:R
* ATR-based risk management — never over-sizes a trade
* 20+ technical indicators (VWAP, EMAs, RSI, MACD, Supertrend, Bollinger, ATR …)
* News sentiment from RSS feeds (ET, Moneycontrol, Google News)
* Sector strength table
* NIFTY option chain PCR & max-pain
* Skipped/unavailable stocks clearly listed

## Disclaimer
For **educational/informational purposes only**. Does NOT guarantee profits.
Always use your own judgment. Signals use cash-market data as proxy for futures.
