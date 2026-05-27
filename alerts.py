import json
import os
import tempfile
import logging
from datetime import datetime, timedelta
from config import (
    ALERT_INDEX_THRESHOLD, ALERT_STOCK_THRESHOLD,
    ALERT_CRYPTO_BTC_ETH_THRESHOLD, ALERT_COMMODITY_THRESHOLD,
    ALERT_COOLDOWN_MINUTES, ALERT_STATE_PATH,
)

logger = logging.getLogger(__name__)


def load_alert_state() -> dict:
    if not os.path.exists(ALERT_STATE_PATH):
        return {}
    try:
        with open(ALERT_STATE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_alert_state(state: dict) -> None:
    dir_ = os.path.dirname(os.path.abspath(ALERT_STATE_PATH))
    with tempfile.NamedTemporaryFile("w", dir=dir_, delete=False, suffix=".tmp") as f:
        json.dump(state, f)
        tmp_path = f.name
    os.replace(tmp_path, ALERT_STATE_PATH)


def clear_stale_alerts(state: dict) -> dict:
    cutoff = (datetime.now() - timedelta(minutes=ALERT_COOLDOWN_MINUTES)).isoformat()
    return {k: v for k, v in state.items() if v > cutoff}


def is_duplicate_alert(state: dict, alert_key: str) -> bool:
    return alert_key in state


def mark_alert_fired(state: dict, alert_key: str) -> dict:
    state[alert_key] = datetime.now().isoformat()
    return state


def check_thresholds(market_data: dict) -> list[dict]:
    alerts = []
    stocks = market_data.get("stocks", {})
    crypto = market_data.get("crypto", {})

    for ticker, label in [("SPY", "S&P 500"), ("QQQ", "Nasdaq")]:
        if ticker not in stocks:
            continue
        pct = stocks[ticker]["pct_change"]
        if abs(pct) >= ALERT_INDEX_THRESHOLD:
            direction = "UP" if pct > 0 else "DOWN"
            alerts.append({
                "key": f"{ticker}_index_{direction}",
                "type": "index", "ticker": ticker, "label": label,
                "pct_change": pct, "price": stocks[ticker]["price"],
                "direction": direction,
            })

    index_tickers = {"SPY", "QQQ", "USO", "GLD"}
    for ticker, data in stocks.items():
        if ticker in index_tickers:
            continue
        pct = data["pct_change"]
        if abs(pct) >= ALERT_STOCK_THRESHOLD:
            direction = "UP" if pct > 0 else "DOWN"
            alerts.append({
                "key": f"{ticker}_stock_{direction}",
                "type": "stock", "ticker": ticker,
                "pct_change": pct, "price": data["price"],
                "direction": direction,
            })

    for ticker, label in [("USO", "Oil"), ("GLD", "Gold")]:
        if ticker not in stocks:
            continue
        pct = stocks[ticker]["pct_change"]
        if abs(pct) >= ALERT_COMMODITY_THRESHOLD:
            direction = "UP" if pct > 0 else "DOWN"
            alerts.append({
                "key": f"{ticker}_commodity_{direction}",
                "type": "commodity", "ticker": ticker, "label": label,
                "pct_change": pct, "price": stocks[ticker]["price"],
                "direction": direction,
            })

    for symbol in ["BTC", "ETH"]:
        if symbol not in crypto:
            continue
        change_1h = crypto[symbol].get("change_1h") or 0
        if abs(change_1h) >= ALERT_CRYPTO_BTC_ETH_THRESHOLD:
            direction = "UP" if change_1h > 0 else "DOWN"
            alerts.append({
                "key": f"{symbol}_crypto_1h_{direction}",
                "type": "crypto", "ticker": symbol,
                "pct_change": change_1h, "price": crypto[symbol]["price"],
                "direction": direction, "timeframe": "1h",
            })

    return alerts
