"""Bloomberg-style dark theme for the Streamlit dashboard."""


def inject_css():
    import streamlit as st
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'IBM Plex Sans', sans-serif;
            background-color: #0a0e14;
            color: #c9d1d9;
        }
        .stApp { background: #0a0e14; }

        .dash-title {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.55rem;
            font-weight: 700;
            color: #f0b429;
            letter-spacing: 2px;
            border-bottom: 1px solid #f0b42940;
            padding-bottom: 10px;
            margin-bottom: 14px;
        }

        .sig-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 14px 18px;
            margin-bottom: 8px;
        }
        .sig-card h4 {
            margin: 0 0 4px;
            font-size: 0.72rem;
            color: #8b949e;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }
        .sig-card .val {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.25rem;
            font-weight: 700;
        }

        .buy-badge     { color: #3fb950; }
        .sell-badge    { color: #f85149; }
        .notrade-badge { color: #8b949e; }
        .neutral-badge { color: #d29922; }

        .section-header {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.78rem;
            color: #f0b429;
            letter-spacing: 2px;
            border-left: 3px solid #f0b429;
            padding-left: 8px;
            margin: 20px 0 10px;
            text-transform: uppercase;
        }

        .news-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 6px;
            font-size: 0.82rem;
            line-height: 1.45;
        }
        .news-pos { border-left: 3px solid #3fb950; }
        .news-neg { border-left: 3px solid #f85149; }
        .news-neu { border-left: 3px solid #8b949e; }

        [data-testid="stMetricValue"] {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.3rem !important;
        }
        div[data-testid="column"] { padding: 0 4px; }

        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: #0a0e14; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def signal_badge(signal: str) -> str:
    if signal == "BUY":
        return "<span class='buy-badge'>▲ BUY</span>"
    elif signal == "SELL":
        return "<span class='sell-badge'>▼ SELL</span>"
    return "<span class='notrade-badge'>● NO TRADE</span>"


def sentiment_badge(label: str) -> str:
    cls = {"POSITIVE": "buy-badge", "NEGATIVE": "sell-badge"}.get(label, "neutral-badge")
    return f"<span class='{cls}'>{label}</span>"


def news_cls(label: str) -> str:
    return {"POSITIVE": "news-pos", "NEGATIVE": "news-neg"}.get(label, "news-neu")
