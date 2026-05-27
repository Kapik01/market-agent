import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-6"

DISCORD_WEBHOOK_ALERTS = os.getenv("DISCORD_WEBHOOK_ALERTS")
DISCORD_WEBHOOK_STOCKS_USA = os.getenv("DISCORD_WEBHOOK_STOCKS_USA")
DISCORD_WEBHOOK_STOCKS_LONDON = os.getenv("DISCORD_WEBHOOK_STOCKS_LONDON")
DISCORD_WEBHOOK_STOCKS_ASIA = os.getenv("DISCORD_WEBHOOK_STOCKS_ASIA")
DISCORD_WEBHOOK_STOCKS_JAPAN = os.getenv("DISCORD_WEBHOOK_STOCKS_JAPAN")
DISCORD_WEBHOOK_CRYPTO = os.getenv("DISCORD_WEBHOOK_CRYPTO")
DISCORD_WEBHOOK_FOREX = os.getenv("DISCORD_WEBHOOK_FOREX")
DISCORD_WEBHOOK_COMMODITIES = os.getenv("DISCORD_WEBHOOK_COMMODITIES")
DISCORD_WEBHOOK_DAILY_SUMMARY = os.getenv("DISCORD_WEBHOOK_DAILY_SUMMARY")

# Alert thresholds
ALERT_INDEX_THRESHOLD = 1.5
ALERT_STOCK_THRESHOLD = 5.0
ALERT_CRYPTO_BTC_ETH_THRESHOLD = 5.0
ALERT_CRYPTO_TOP10_THRESHOLD = 10.0
ALERT_COMMODITY_THRESHOLD = 3.0
ALERT_COOLDOWN_MINUTES = 60

ALERT_STATE_PATH = "alert_state.json"
LOG_PATH = "market_agent.log"

MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0

# Timezones for regional market hours checks
TZ_LONDON = "Europe/London"
TZ_TOKYO = "Asia/Tokyo"
TZ_HONG_KONG = "Asia/Hong_Kong"

TOP_SP500_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "BRK-B",
    "LLY", "AVGO", "JPM", "TSLA", "UNH", "XOM", "V", "COST",
    "MA", "JNJ", "PG", "HD", "ABBV", "BAC", "MRK", "CVX", "CRM",
    "ORCL", "ACN", "NFLX", "AMD", "PEP", "KO", "TMO", "ADBE",
    "WMT", "LIN", "MCD", "CSCO", "ABT", "IBM", "GE", "NOW",
    "QCOM", "PM", "INTU", "TXN", "DIS", "VZ", "CAT", "GS", "RTX", "AMGN"
]

SPECULATIVE_TICKERS = [
    "SOFI", "RIVN", "LCID", "PLUG", "SOUN", "IONQ", "ARRY", "JOBY",
    "OPEN", "UPST", "HOOD", "MVIS", "FCEL", "BLNK", "CHPT", "PSFE",
    "NNDM", "HYLN", "MULN", "WKHS", "SPCE", "BARK", "CLOV", "GOEV",
    "NKLA", "XL", "SOLO", "AYRO", "PTRA", "RIDE"
]

LONDON_TICKERS = [
    "HSBA.L", "BP.L", "SHEL.L", "GSK.L", "AZN.L",
    "ULVR.L", "RIO.L", "DGE.L", "BTI.L", "NG.L",
    "VOD.L", "BARC.L", "LLOY.L", "GLEN.L", "AAL.L",
    "PRU.L", "REL.L", "RKT.L", "EXPN.L", "III.L",
]

JAPAN_TICKERS = [
    "7203.T", "6758.T", "8306.T", "9984.T", "6861.T",
    "7974.T", "6501.T", "8035.T", "4063.T", "6367.T",
    "9432.T", "7267.T", "6902.T", "8001.T", "8316.T",
    "9433.T", "7751.T", "4661.T", "6594.T", "2802.T",
]

ASIA_TICKERS = [
    "0700.HK", "9988.HK", "0941.HK", "0005.HK", "1299.HK",
    "0939.HK", "1398.HK", "2318.HK", "3690.HK", "9618.HK",
    "1810.HK", "0388.HK", "2020.HK", "9999.HK", "0883.HK",
    "1177.HK", "2382.HK", "0016.HK", "1211.HK", "0027.HK",
]

COMMODITY_TICKERS = {
    "Oil": "USO",
    "Gold": "GLD",
    "Silver": "SLV",
    "Natural Gas": "UNG",
}

FOREX_PAIRS = ["EURUSD=X", "GBPUSD=X", "JPYUSD=X", "CHFUSD=X", "CADUSD=X", "AUDUSD=X"]
FOREX_LABELS = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "JPYUSD=X": "JPY/USD",
    "CHFUSD=X": "CHF/USD",
    "CADUSD=X": "CAD/USD",
    "AUDUSD=X": "AUD/USD",
}

HIGH_IMPACT_KEYWORDS = [
    "fed", "rate hike", "rate cut", "recession", "crash", "bankruptcy",
    "merger", "acquisition", "fda approval", "fda rejection",
    "earnings beat", "earnings miss", "indictment", "sanctions",
    "war", "default", "layoffs", "fraud", "investigation",
]
