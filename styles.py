"""Bloomberg-style dark theme for the Streamlit dashboard."""


def inject_css():
    import streamlit as st
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'IBM Plex Sans', sans-serif;
            background-color: #111827;
            color: #f8fafc;
        }

        .stApp {
            background: #111827;
            color: #f8fafc;
        }

        .dash-title {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.55rem;
            font-weight: 700;
            color: #facc15;
            letter-spacing: 2px;
            border-bottom: 1px solid #facc1555;
            padding-bottom: 10px;
            margin-bottom: 14px;
        }

        .sig-card {
            background: #1f2937;
            border: 1px solid #475569;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        }

        .sig-card h4 {
            margin: 0 0 4px;
            font-size: 0.72rem;
            color: #cbd5e1;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }

        .sig-card .val {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.25rem;
            font-weight: 700;
            color: #f8fafc;
        }

        .buy-badge     { color: #22c55e; font-weight: 700; }
        .sell-badge    { color: #ef4444; font-weight: 700; }
        .notrade-badge { color: #eab308; font-weight: 700; }
        .neutral-badge { color: #facc15; font-weight: 700; }

        .section-header {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.82rem;
            color: #facc15;
            letter-spacing: 2px;
            border-left: 4px solid #facc15;
            padding-left: 10px;
            margin: 22px 0 12px;
            text-transform: uppercase;
            font-weight: 700;
        }

        .news-card {
            background: #1f2937;
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 8px;
            font-size: 0.84rem;
            line-height: 1.45;
            color: #f8fafc;
        }

        .news-pos { border-left: 4px solid #22c55e; }
        .news-neg { border-left: 4px solid #ef4444; }
        .news-neu { border-left: 4px solid #eab308; }

        [data-testid="stMetricValue"] {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.3rem !important;
            color: #f8fafc !important;
        }

        [data-testid="metric-container"] {
            background-color: #1f2937;
            border: 1px solid #475569;
            border-radius: 10px;
            padding: 10px;
        }

        [data-testid="stDataFrame"] {
            background-color: #1f2937;
            border: 1px solid #475569;
            border-radius: 10px;
        }

        div[data-testid="column"] {
            padding: 0 4px;
        }

        ::-webkit-scrollbar { width: 7px; }
        ::-webkit-scrollbar-track { background: #111827; }
        ::-webkit-scrollbar-thumb { background: #64748b; border-radius: 4px; }

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
