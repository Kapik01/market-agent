import argparse
import logging
from datetime import datetime
import pytz

from config import (
    DISCORD_WEBHOOK_STOCKS, DISCORD_WEBHOOK_CRYPTO, DISCORD_WEBHOOK_FOREX,
    DISCORD_WEBHOOK_COMMODITIES, DISCORD_WEBHOOK_DAILY_SUMMARY,
    DISCORD_WEBHOOK_ALERTS, LOG_PATH,
    MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE, MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE,
)
from fetcher import (
    fetch_stock_movers, fetch_crypto_data, fetch_forex_data,
    fetch_commodity_data, fetch_alert_prices, fetch_stock_news,
    fetch_stock_fundamentals, fetch_speculative_picks,
)
from analyzer import (
    analyze_stocks, analyze_crypto, analyze_forex,
    analyze_commodities, analyze_eod, analyze_alert,
)
from poster import post_to_discord, post_with_retry
from alerts import (
    load_alert_state, save_alert_state, clear_stale_alerts,
    check_thresholds, is_duplicate_alert, mark_alert_fired,
)

logging.basicConfig(
    filename=LOG_PATH, level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

ET = pytz.timezone("America/New_York")


def is_market_hours() -> bool:
    now = datetime.now(ET)
    if now.weekday() >= 5:
        return False
    open_time = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    close_time = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
    return open_time <= now <= close_time


def run_hourly() -> None:
    channels = [
        (fetch_crypto_data, analyze_crypto, DISCORD_WEBHOOK_CRYPTO, "crypto"),
        (fetch_forex_data, analyze_forex, DISCORD_WEBHOOK_FOREX, "forex"),
    ]
    if is_market_hours():
        channels += [
            (fetch_stock_movers, analyze_stocks, DISCORD_WEBHOOK_STOCKS, "stocks"),
            (fetch_commodity_data, analyze_commodities, DISCORD_WEBHOOK_COMMODITIES, "commodities"),
        ]

    for fetch_fn, analyze_fn, webhook, name in channels:
        try:
            data = fetch_fn()
            message = analyze_fn(data)
            post_to_discord(webhook, message)
            logging.info(f"Posted {name} hourly update")
        except Exception as e:
            logging.error(f"Hourly {name} failed: {e}")
            post_to_discord(webhook, f"⚠️ Data unavailable for {name} this hour.")


def run_eod() -> None:
    try:
        all_data = {
            "stocks": fetch_stock_movers(),
            "crypto": fetch_crypto_data(),
            "forex": fetch_forex_data(),
            "commodities": fetch_commodity_data(),
            "fundamentals": fetch_stock_fundamentals(),
            "speculative": fetch_speculative_picks(),
        }
        message = analyze_eod(all_data)
        post_to_discord(DISCORD_WEBHOOK_DAILY_SUMMARY, message)
        logging.info("Posted EOD summary")
    except Exception as e:
        logging.error(f"EOD summary failed: {e}")


def run_alerts() -> None:
    try:
        state = load_alert_state()
        state = clear_stale_alerts(state)

        market_data = fetch_alert_prices()
        triggered = check_thresholds(market_data)

        news_hits = fetch_stock_news(list(market_data["stocks"].keys()))

        for alert in triggered:
            if is_duplicate_alert(state, alert["key"]):
                continue
            try:
                message = analyze_alert(alert)
                if post_with_retry(DISCORD_WEBHOOK_ALERTS, message, retries=3):
                    state = mark_alert_fired(state, alert["key"])
                    logging.info(f"Alert fired: {alert['key']}")
            except Exception as e:
                logging.error(f"Alert message failed for {alert['key']}: {e}")

        for news in news_hits:
            news_key = f"news_{news['ticker']}_{news['published']}"
            if is_duplicate_alert(state, news_key):
                continue
            try:
                message = analyze_alert({"type": "news", **news})
                if post_with_retry(DISCORD_WEBHOOK_ALERTS, message, retries=3):
                    state = mark_alert_fired(state, news_key)
                    logging.info(f"News alert fired: {news_key}")
            except Exception as e:
                logging.error(f"News alert failed for {news_key}: {e}")

        save_alert_state(state)
    except Exception as e:
        logging.error(f"Alert run failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["hourly", "eod", "alerts"], required=True)
    args = parser.parse_args()

    if args.mode == "hourly":
        run_hourly()
    elif args.mode == "eod":
        run_eod()
    elif args.mode == "alerts":
        run_alerts()
