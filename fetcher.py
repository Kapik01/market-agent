import logging
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime
from config import (
    TOP_SP500_TICKERS, SPECULATIVE_TICKERS, COMMODITY_TICKERS,
    FOREX_PAIRS, FOREX_LABELS, HIGH_IMPACT_KEYWORDS,
)

COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"


def fetch_stock_movers() -> dict:
    """Fetch top S&P 500 movers with volume and breakout signals."""
    try:
        data = yf.download(
            TOP_SP500_TICKERS, period="60d", interval="1d",
            progress=False, group_by="ticker", auto_adjust=True,
        )
        results = []
        for ticker in TOP_SP500_TICKERS:
            try:
                close = data[ticker]["Close"].dropna()
                volume = data[ticker]["Volume"].dropna()
                if len(close) < 2:
                    continue

                current, prev = float(close.iloc[-1]), float(close.iloc[-2])
                vol_today = float(volume.iloc[-1])
                avg_vol = float(volume.iloc[:-1].mean())
                volume_ratio = vol_today / avg_vol if avg_vol > 0 else 0
                pct_change = ((current - prev) / prev) * 100

                ma20 = float(close.iloc[-20:].mean()) if len(close) >= 20 else None
                ma50 = float(close.iloc[-50:].mean()) if len(close) >= 50 else None
                high_60d = float(close.max())

                signals = []
                if volume_ratio > 2.0:
                    signals.append(f"Volume {volume_ratio:.1f}x average")
                if ma20 and prev <= ma20 and current > ma20:
                    signals.append("Crossed above 20-day MA")
                if ma50 and prev <= ma50 and current > ma50:
                    signals.append("Crossed above 50-day MA")
                if current >= high_60d * 0.99:
                    signals.append("Near 60-day high")

                results.append({
                    "ticker": ticker,
                    "price": round(current, 2),
                    "pct_change": round(pct_change, 2),
                    "volume": int(vol_today),
                    "volume_ratio": round(volume_ratio, 2),
                    "on_the_rise_signals": signals,
                })
            except (KeyError, IndexError, ValueError):
                continue

        results.sort(key=lambda x: abs(x["pct_change"]), reverse=True)
        return {
            "top_movers": results[:10],
            "on_the_rise": [r for r in results if r["on_the_rise_signals"]][:5],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"top_movers": [], "on_the_rise": [], "error": str(e), "timestamp": datetime.now().isoformat()}


def fetch_crypto_data() -> dict:
    """Fetch top 20 cryptos by market cap from CoinGecko."""
    try:
        resp = requests.get(
            COINGECKO_MARKETS_URL,
            params={
                "vs_currency": "usd", "order": "market_cap_desc",
                "per_page": 20, "page": 1,
                "price_change_percentage": "1h,24h",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return {
            "coins": [
                {
                    "name": c["name"],
                    "symbol": c["symbol"].upper(),
                    "price": c["current_price"],
                    "change_1h": c.get("price_change_percentage_1h_in_currency") or 0,
                    "change_24h": c.get("price_change_percentage_24h") or 0,
                    "volume": c["total_volume"],
                    "market_cap": c["market_cap"],
                }
                for c in resp.json()
            ],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"coins": [], "error": str(e), "timestamp": datetime.now().isoformat()}


def fetch_forex_data() -> dict:
    """Fetch major forex pairs via yfinance."""
    try:
        data = yf.download(FOREX_PAIRS, period="5d", interval="1d", progress=False)
        results = []
        for pair in FOREX_PAIRS:
            try:
                close = data["Close"][pair].dropna()
                if len(close) < 2:
                    continue
                current, prev = float(close.iloc[-1]), float(close.iloc[-2])
                results.append({
                    "pair": FOREX_LABELS[pair],
                    "rate": round(current, 4),
                    "pct_change": round(((current - prev) / prev) * 100, 4),
                })
            except (KeyError, IndexError):
                continue
        return {"pairs": results, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"pairs": [], "error": str(e), "timestamp": datetime.now().isoformat()}


def fetch_commodity_data() -> dict:
    """Fetch commodity ETF prices via yfinance."""
    try:
        tickers = list(COMMODITY_TICKERS.values())
        data = yf.download(tickers, period="5d", interval="1d", progress=False)
        results = []
        for name, ticker in COMMODITY_TICKERS.items():
            try:
                close = data["Close"][ticker].dropna()
                if len(close) < 2:
                    continue
                current, prev = float(close.iloc[-1]), float(close.iloc[-2])
                results.append({
                    "name": name, "ticker": ticker,
                    "price": round(current, 2),
                    "pct_change": round(((current - prev) / prev) * 100, 2),
                })
            except (KeyError, IndexError):
                continue
        return {"commodities": results, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"commodities": [], "error": str(e), "timestamp": datetime.now().isoformat()}


def fetch_alert_prices() -> dict:
    """Fast fetch of key prices for alert threshold checking."""
    alert_tickers = ["SPY", "QQQ", "USO", "GLD"] + TOP_SP500_TICKERS[:20]
    stocks = {}
    try:
        data = yf.download(alert_tickers, period="2d", interval="1d", progress=False, group_by="ticker", auto_adjust=True)
        for ticker in alert_tickers:
            try:
                close = data[ticker]["Close"].dropna()
                if len(close) < 2:
                    continue
                current, prev = float(close.iloc[-1]), float(close.iloc[-2])
                stocks[ticker] = {
                    "price": round(current, 2),
                    "prev_close": round(prev, 2),
                    "pct_change": round(((current - prev) / prev) * 100, 2),
                }
            except (KeyError, IndexError, ValueError):
                continue
    except Exception as e:
        logging.getLogger(__name__).warning(f"fetch_alert_prices stocks download failed: {e}")

    crypto = {}
    try:
        resp = requests.get(
            COINGECKO_MARKETS_URL,
            params={"vs_currency": "usd", "ids": "bitcoin,ethereum", "price_change_percentage": "1h"},
            timeout=10,
        )
        if resp.status_code == 200:
            for coin in resp.json():
                crypto[coin["symbol"].upper()] = {
                    "price": coin["current_price"],
                    "change_1h": coin.get("price_change_percentage_1h_in_currency") or 0,
                }
    except Exception:
        pass

    return {"stocks": stocks, "crypto": crypto, "timestamp": datetime.now().isoformat()}


def fetch_stock_news(tickers: list[str]) -> list[dict]:
    """Fetch recent news for tickers and return only high-impact headlines."""
    hits = []
    for ticker in tickers[:10]:
        try:
            news = yf.Ticker(ticker).news
            for article in news[:3]:
                title = article.get("title", "").lower()
                if any(kw in title for kw in HIGH_IMPACT_KEYWORDS):
                    hits.append({
                        "ticker": ticker,
                        "title": article["title"],
                        "link": article.get("link", ""),
                        "published": article.get("providerPublishTime", 0),
                    })
        except Exception:
            continue
    return hits


def fetch_stock_fundamentals() -> list[dict]:
    """Fetch fundamental data for the top 20 S&P 500 tickers for EOD picks. Makes 20 serial HTTP calls — expect 20-60s latency."""
    results = []
    for ticker in TOP_SP500_TICKERS[:20]:
        try:
            info = yf.Ticker(ticker).info
            results.append({
                "ticker": ticker,
                "name": info.get("longName", ticker),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "revenue_growth": info.get("revenueGrowth"),
                "analyst_target": info.get("targetMeanPrice"),
                "sector": info.get("sector", "Unknown"),
                "market_cap": info.get("marketCap"),
            })
        except Exception:
            continue
    return results


def fetch_speculative_picks() -> list[dict]:
    """Fetch data for speculative tickers under $15 with volume spikes."""
    results = []
    try:
        data = yf.download(SPECULATIVE_TICKERS, period="30d", interval="1d", progress=False, group_by="ticker", auto_adjust=True)
        for ticker in SPECULATIVE_TICKERS:
            try:
                close = data[ticker]["Close"].dropna()
                volume = data[ticker]["Volume"].dropna()
                if len(close) < 2:
                    continue
                current = float(close.iloc[-1])
                if current > 15:
                    continue
                prev = float(close.iloc[-2])
                vol_today = float(volume.iloc[-1])
                avg_vol = float(volume.iloc[:-1].mean())
                volume_ratio = vol_today / avg_vol if avg_vol > 0 else 0
                recent_high = float(close.iloc[-10:].max())
                results.append({
                    "ticker": ticker,
                    "price": round(current, 2),
                    "pct_change": round(((current - prev) / prev) * 100, 2),
                    "volume_ratio": round(volume_ratio, 2),
                    "near_recent_high": current >= recent_high * 0.98,
                })
            except (KeyError, IndexError, ValueError):
                continue
    except Exception as e:
        logging.getLogger(__name__).warning(f"fetch_speculative_picks download failed: {e}")
    results.sort(key=lambda x: x["volume_ratio"], reverse=True)
    return results[:10]
