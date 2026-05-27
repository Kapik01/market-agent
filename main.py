import argparse
import logging
from datetime import datetime
import pytz

from config import (
    DISCORD_WEBHOOK_STOCKS_USA, DISCORD_WEBHOOK_STOCKS_LONDON,
    DISCORD_WEBHOOK_STOCKS_ASIA, DISCORD_WEBHOOK_STOCKS_JAPAN,
    DISCORD_WEBHOOK_CRYPTO, DISCORD_WEBHOOK_FOREX,
    DISCORD_WEBHOOK_COMMODITIES, DISCORD_WEBHOOK_DAILY_SUMMARY,
    DISCORD_WEBHOOK_ALERTS, LOG_PATH,
    MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE, MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE,
    TZ_LONDON, TZ_TOKYO, TZ_HONG_KONG,
)
from fetcher import (
    fetch_stock_movers, fetch_london_movers, fetch_japan_movers, fetch_asia_movers,
    fetch_usa_premarket, fetch_london_premarket, fetch_japan_premarket, fetch_asia_premarket,
    fetch_crypto_data, fetch_forex_data,
    fetch_commodity_data, fetch_alert_prices, fetch_stock_news,
    fetch_stock_fundamentals, fetch_speculative_picks,
)
from analyzer import (
    analyze_stocks_usa, analyze_stocks_london, analyze_stocks_japan, analyze_stocks_asia,
    analyze_premarket_usa, analyze_premarket_london, analyze_premarket_japan, analyze_premarket_asia,
    analyze_crypto, analyze_forex,
    analyze_commodities, analyze_eod, analyze_alert,
    analyze_eod_speculative,
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
LONDON_TZ = pytz.timezone(TZ_LONDON)
TOKYO_TZ = pytz.timezone(TZ_TOKYO)
HK_TZ = pytz.timezone(TZ_HONG_KONG)


def is_usa_market_hours() -> bool:
    now = datetime.now(ET)
    if now.weekday() >= 5:
        return False
    open_time = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
    close_time = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
    return open_time <= now <= close_time


def is_london_market_hours() -> bool:
    now = datetime.now(LONDON_TZ)
    if now.weekday() >= 5:
        return False
    open_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    close_time = now.replace(hour=16, minute=30, second=0, microsecond=0)
    return open_time <= now <= close_time


def is_japan_market_hours() -> bool:
    now = datetime.now(TOKYO_TZ)
    if now.weekday() >= 5:
        return False
    open_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return open_time <= now <= close_time


def is_asia_market_hours() -> bool:
    now = datetime.now(HK_TZ)
    if now.weekday() >= 5:
        return False
    open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_time <= now <= close_time


def is_usa_premarket() -> bool:
    now = datetime.now(ET)
    if now.weekday() >= 5:
        return False
    start = now.replace(hour=8, minute=30, second=0, microsecond=0)
    end = now.replace(hour=9, minute=30, second=0, microsecond=0)
    return start <= now < end


def is_london_premarket() -> bool:
    now = datetime.now(LONDON_TZ)
    if now.weekday() >= 5:
        return False
    start = now.replace(hour=7, minute=0, second=0, microsecond=0)
    end = now.replace(hour=8, minute=0, second=0, microsecond=0)
    return start <= now < end


def is_japan_premarket() -> bool:
    now = datetime.now(TOKYO_TZ)
    if now.weekday() >= 5:
        return False
    start = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end = now.replace(hour=9, minute=0, second=0, microsecond=0)
    return start <= now < end


def is_asia_premarket() -> bool:
    now = datetime.now(HK_TZ)
    if now.weekday() >= 5:
        return False
    start = now.replace(hour=8, minute=30, second=0, microsecond=0)
    end = now.replace(hour=9, minute=30, second=0, microsecond=0)
    return start <= now < end


# Keep old name as alias so existing tests still pass during transition
is_market_hours = is_usa_market_hours


def run_hourly() -> None:
    channels = [
        (fetch_crypto_data, analyze_crypto, DISCORD_WEBHOOK_CRYPTO, "crypto"),
        (fetch_forex_data, analyze_forex, DISCORD_WEBHOOK_FOREX, "forex"),
    ]

    # Pre-market briefings (~1 hour before each session opens)
    if is_asia_premarket():
        channels.append((fetch_asia_premarket, analyze_premarket_asia, DISCORD_WEBHOOK_STOCKS_ASIA, "premarket-asia"))
    if is_japan_premarket():
        channels.append((fetch_japan_premarket, analyze_premarket_japan, DISCORD_WEBHOOK_STOCKS_JAPAN, "premarket-japan"))
    if is_london_premarket():
        channels.append((fetch_london_premarket, analyze_premarket_london, DISCORD_WEBHOOK_STOCKS_LONDON, "premarket-london"))
    if is_usa_premarket():
        channels.append((fetch_usa_premarket, analyze_premarket_usa, DISCORD_WEBHOOK_STOCKS_USA, "premarket-usa"))

    # Live session updates
    if is_asia_market_hours():
        channels.append((fetch_asia_movers, analyze_stocks_asia, DISCORD_WEBHOOK_STOCKS_ASIA, "stocks-asia"))
    if is_japan_market_hours():
        channels.append((fetch_japan_movers, analyze_stocks_japan, DISCORD_WEBHOOK_STOCKS_JAPAN, "stocks-japan"))
    if is_london_market_hours():
        channels.append((fetch_london_movers, analyze_stocks_london, DISCORD_WEBHOOK_STOCKS_LONDON, "stocks-london"))
    if is_usa_market_hours():
        channels.append((fetch_stock_movers, analyze_stocks_usa, DISCORD_WEBHOOK_STOCKS_USA, "stocks-usa"))
        channels.append((fetch_commodity_data, analyze_commodities, DISCORD_WEBHOOK_COMMODITIES, "commodities"))

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
            "stocks_usa": fetch_stock_movers(),
            "stocks_london": fetch_london_movers(),
            "stocks_japan": fetch_japan_movers(),
            "stocks_asia": fetch_asia_movers(),
            "crypto": fetch_crypto_data(),
            "forex": fetch_forex_data(),
            "commodities": fetch_commodity_data(),
            "fundamentals": fetch_stock_fundamentals(),
            "speculative": fetch_speculative_picks(),
        }
        # Post day review + long-term picks
        main_summary = analyze_eod(all_data)
        post_to_discord(DISCORD_WEBHOOK_DAILY_SUMMARY, main_summary)
        # Post speculative picks separately (avoids 2000-char Discord truncation)
        spec_summary = analyze_eod_speculative(all_data.get("speculative", []))  # noqa: E501
        post_to_discord(DISCORD_WEBHOOK_DAILY_SUMMARY, spec_summary)
        logging.info("Posted EOD summary (2 parts)")
    except Exception as e:
        logging.error(f"EOD summary failed: {e}")


def run_alerts() -> None:
    try:
        state = load_alert_state()
        state = clear_stale_alerts(state)

        market_data = fetch_alert_prices()
        triggered = check_thresholds(market_data)

        news_hits = fetch_stock_news(list(market_data.get("stocks", {}).keys()))

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
