import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-6"

DISCORD_WEBHOOK_ALERTS = os.getenv("DISCORD_WEBHOOK_ALERTS")
DISCORD_WEBHOOK_STOCKS = os.getenv("DISCORD_WEBHOOK_STOCKS")
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
