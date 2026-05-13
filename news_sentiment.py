"""
news_sentiment.py
Fetches headlines from free RSS feeds and produces sentiment scores.
"""

import feedparser
import re
import streamlit as st
from config import NEWS_FEEDS, POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS


@st.cache_data(ttl=120, show_spinner=False)
def fetch_news() -> list:
    headlines = []
    for url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                text    = (title + " " + summary).lower()
                score   = _score_text(text)
                headlines.append({
                    "title":  title[:130],
                    "source": _domain(url),
                    "score":  score,
                    "label":  "POSITIVE" if score > 0 else ("NEGATIVE" if score < 0 else "NEUTRAL"),
                })
        except Exception:
            pass
    return headlines[:40]


def _score_text(text: str) -> int:
    pos = sum(1 for k in POSITIVE_KEYWORDS if k in text)
    neg = sum(1 for k in NEGATIVE_KEYWORDS if k in text)
    return pos - neg


def _domain(url: str) -> str:
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1).split(".")[0].capitalize() if m else "News"


def get_market_sentiment(headlines: list) -> dict:
    if not headlines:
        return {"score": 0, "label": "NEUTRAL", "bias": "Sideways"}
    total = sum(h["score"] for h in headlines)
    avg   = total / len(headlines)
    label = "POSITIVE" if avg > 0.3 else ("NEGATIVE" if avg < -0.3 else "NEUTRAL")
    bias  = "Bullish"  if avg > 0.3 else ("Bearish"  if avg < -0.3 else "Sideways")
    return {"score": round(avg, 2), "label": label, "bias": bias}


def get_sector_sentiment(headlines: list, sector: str) -> int:
    kw_map = {
        "Banking":   ["bank","rbi","credit","nbfc","interest rate","npa","loan"],
        "IT":        ["it ","tech","software","digital","cloud","infosys","wipro","tcs"],
        "Auto":      ["auto","vehicle","ev","electric vehicle","maruti","tata motors"],
        "Pharma":    ["pharma","drug","medicine","fda","usfda","hospital"],
        "Metal":     ["steel","metal","iron","aluminium","zinc","copper"],
        "Energy":    ["oil","crude","gas","energy","petroleum","refinery"],
        "FMCG":      ["fmcg","consumer","food","beverage"],
    }
    keywords = kw_map.get(sector, [sector.lower()])
    score = 0
    for h in headlines:
        if any(k in h["title"].lower() for k in keywords):
            score += h["score"]
    return score


def get_stock_sentiment(headlines: list, symbol: str) -> int:
    name = symbol.replace(".NS", "").lower()
    return sum(h["score"] for h in headlines if name in h["title"].lower())
