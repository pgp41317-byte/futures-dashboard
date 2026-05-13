"""Central configuration for the NSE F&O Futures Dashboard."""

# ── Risk parameters ────────────────────────────────────────────────────────
DEFAULT_CAPITAL       = 200_000      # INR 2,00,000
MAX_RISK_PCT          = 0.01         # 1 % per trade

# ── Signal thresholds ──────────────────────────────────────────────────────
BULL_SCORE_THRESHOLD  = 70
BEAR_SCORE_THRESHOLD  = 70
MIN_VOLUME_RATIO      = 1.3
MIN_RISK_REWARD       = 1.5

# ── ATR multipliers ────────────────────────────────────────────────────────
ATR_SL_MULT  = 1.2
ATR_T1_MULT  = 1.5
ATR_T2_MULT  = 2.2

# ── Refresh ────────────────────────────────────────────────────────────────
REFRESH_INTERVAL = 5
SCAN_CACHE_TTL = 300                 # seconds

# ── Index tickers ──────────────────────────────────────────────────────────
NIFTY_TICKER      = "^NSEI"
BANKNIFTY_TICKER  = "^NSEBANK"
VIX_TICKER        = "^INDIAVIX"

# ── Data window ────────────────────────────────────────────────────────────
INTRADAY_PERIOD   = "5d"
INTRADAY_INTERVAL = "5m"

# ── News RSS feeds ─────────────────────────────────────────────────────────
NEWS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "https://news.google.com/rss/search?q=NSE+stock+market+India&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=NIFTY+BANKNIFTY+futures&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=RBI+FII+DII+India+market&hl=en-IN&gl=IN&ceid=IN:en",
]

# ── Sentiment keywords ─────────────────────────────────────────────────────
POSITIVE_KEYWORDS = [
    "upgrade", "outperform", "buy", "strong demand", "order win", "capex",
    "profit", "growth", "beat", "recovery", "expansion", "rally", "surge",
    "gains", "bullish", "positive", "record", "merger", "acquisition",
    "deal", "approval", "rate cut", "fii buying", "dii buying", "stimulus",
    "reform", "earnings beat", "robust", "inflow", "optimistic",
]
NEGATIVE_KEYWORDS = [
    "downgrade", "underperform", "sell", "margin pressure", "demand slowdown",
    "loss", "decline", "miss", "recession", "fall", "drop", "bearish",
    "default", "war", "tariff", "sanction", "inflation", "rate hike",
    "fii selling", "earnings miss", "write-off", "penalty", "probe", "fraud",
    "outflow", "concern", "risk", "slowdown", "weak",
]

# ── Sector → member symbols ────────────────────────────────────────────────
SECTOR_MAP = {
    "Banking":          ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","BANKBARODA",
                         "INDUSINDBK","FEDERALBNK","IDFCFIRSTB","RBLBANK","BANDHANBNK",
                         "CANBK","UNIONBANK","PNB","AUBANK"],
    "IT":               ["TCS","INFY","WIPRO","HCLTECH","TECHM","MPHASIS","LTIM",
                         "PERSISTENT","COFORGE","OFSS"],
    "Auto":             ["MARUTI","M&M","BAJAJ-AUTO","HEROMOTOCO","EICHERMOT",
                         "ASHOKLEY","TVSMOTOR","MOTHERSON","BOSCHLTD"],
    "Pharma":           ["SUNPHARMA","CIPLA","DRREDDY","DIVISLAB","AUROPHARMA","LUPIN",
                         "BIOCON","ALKEM","TORNTPHARM","GLENMARK"],
    "Metal":            ["JSWSTEEL","TATASTEEL","HINDALCO","VEDL","SAIL","NATIONALUM",
                         "JINDALSTEL","COALINDIA","NMDC","HINDZINC"],
    "Energy":           ["RELIANCE","ONGC","BPCL","IOC","GAIL","PETRONET","OIL",
                         "NTPC","POWERGRID","TATAPOWER"],
    "FMCG":             ["ITC","HINDUNILVR","NESTLEIND","BRITANNIA","DABUR","MARICO",
                         "GODREJCP","COLPAL","EMAMILTD","VBL"],
    "Realty":           ["DLF","GODREJPROP","PRESTIGE","OBEROIRLTY","PHOENIXLTD","BRIGADE","SOBHA"],
    "Capital Goods":    ["LT","BHEL","ABB","SIEMENS","HAVELLS","VOLTAS","CUMMINSIND",
                         "THERMAX","BEL","HAL"],
    "Cement":           ["ULTRACEMCO","SHREECEM","AMBUJACEM","ACC","RAMCOCEM","JKCEMENT","DALMIA"],
    "Telecom":          ["BHARTIARTL","IDEA"],
    "Chemical":         ["PIDILITIND","AARTIIND","DEEPAKNTR","VINATIORGA","FINEORG",
                         "NAVINFLUOR","SRF","SUDARSCHEM"],
    "NBFC":             ["BAJFINANCE","BAJAJFINSV","CHOLAFIN","MUTHOOTFIN","MANAPPURAM",
                         "LICSGFIN","SBICARD","PIRAMALENT"],
    "Consumer Durables":["TITAN","VOLTAS","WHIRLPOOL","BATAINDIA","PAGEIND","VGUARD",
                         "CROMPTON","ORIENTELEC"],
    "PSU":              ["NTPC","POWERGRID","ONGC","COALINDIA","BEL","HAL","SAIL","BHEL",
                         "GAIL","CONCOR"],
}
