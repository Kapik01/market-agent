from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import pytest
from fetcher import (
    fetch_crypto_data, fetch_forex_data, fetch_commodity_data, fetch_alert_prices,
    fetch_stock_news, fetch_london_movers, fetch_japan_movers, fetch_asia_movers,
)


# --- Crypto ---

def _mock_coingecko_response(coins=None):
    if coins is None:
        coins = [
            {
                "name": "Bitcoin", "symbol": "btc",
                "current_price": 50000,
                "price_change_percentage_1h_in_currency": 1.5,
                "price_change_percentage_24h": 3.2,
                "total_volume": 25_000_000_000,
                "market_cap": 1_000_000_000_000,
            }
        ]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = coins
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def test_fetch_crypto_data_returns_coins():
    with patch("fetcher.requests.get", return_value=_mock_coingecko_response()):
        result = fetch_crypto_data()
    assert len(result["coins"]) == 1
    assert result["coins"][0]["symbol"] == "BTC"
    assert result["coins"][0]["price"] == 50000
    assert result["coins"][0]["change_1h"] == 1.5
    assert "timestamp" in result


def test_fetch_crypto_data_handles_api_failure():
    with patch("fetcher.requests.get", side_effect=Exception("timeout")):
        result = fetch_crypto_data()
    assert result["coins"] == []
    assert "error" in result


# --- Forex ---

def _mock_yf_download(tickers, close_values):
    """Build a fake yfinance download DataFrame for forex pairs."""
    close_data = {t: pd.Series([v1, v2]) for t, (v1, v2) in zip(tickers, close_values)}
    close_df = pd.DataFrame(close_data)
    mock_df = MagicMock()
    mock_df.__getitem__ = MagicMock(side_effect=lambda key: close_df if key == "Close" else MagicMock())
    return mock_df


def test_fetch_forex_data_returns_pairs():
    pairs = ["EURUSD=X", "GBPUSD=X", "JPYUSD=X", "CHFUSD=X", "CADUSD=X", "AUDUSD=X"]
    close_values = [(1.08, 1.09), (1.27, 1.28), (0.0067, 0.0068), (1.12, 1.11), (0.73, 0.74), (0.65, 0.66)]
    mock_data = _mock_yf_download(pairs, close_values)
    with patch("fetcher.yf.download", return_value=mock_data):
        result = fetch_forex_data()
    assert len(result["pairs"]) == 6
    assert result["pairs"][0]["pair"] == "EUR/USD"
    assert isinstance(result["pairs"][0]["pct_change"], float)


# --- Commodities ---

def test_fetch_commodity_data_returns_commodities():
    tickers = ["USO", "GLD", "SLV", "UNG"]
    close_values = [(75.0, 76.5), (180.0, 182.0), (22.0, 21.5), (10.0, 9.8)]
    mock_data = _mock_yf_download(tickers, close_values)
    with patch("fetcher.yf.download", return_value=mock_data):
        result = fetch_commodity_data()
    assert len(result["commodities"]) == 4
    assert result["commodities"][0]["name"] in ("Oil", "Gold", "Silver", "Natural Gas")


# --- Alert prices ---

def test_fetch_alert_prices_returns_stocks_and_crypto():
    tickers = ["SPY", "QQQ", "USO", "GLD"] + ["AAPL", "MSFT"]
    close_values = [(450.0, 453.0)] * len(tickers)
    mock_stock_data = _mock_yf_download(tickers, close_values)
    mock_crypto_resp = _mock_coingecko_response([
        {"name": "Bitcoin", "symbol": "btc", "current_price": 50000,
         "price_change_percentage_1h_in_currency": 1.0,
         "price_change_percentage_24h": 2.0,
         "total_volume": 1e10, "market_cap": 1e12},
        {"name": "Ethereum", "symbol": "eth", "current_price": 3000,
         "price_change_percentage_1h_in_currency": -0.5,
         "price_change_percentage_24h": 1.0,
         "total_volume": 5e9, "market_cap": 3e11},
    ])
    with patch("fetcher.yf.download", return_value=mock_stock_data):
        with patch("fetcher.requests.get", return_value=mock_crypto_resp):
            result = fetch_alert_prices()
    assert "stocks" in result
    assert "crypto" in result
    assert "BTC" in result["crypto"]
    assert "ETH" in result["crypto"]


# --- News ---

def test_fetch_stock_news_returns_high_impact_hits():
    mock_ticker = MagicMock()
    mock_ticker.news = [
        {"title": "Fed signals rate cut ahead of meeting", "link": "http://a.com", "providerPublishTime": 1234},
        {"title": "AAPL releases new phone", "link": "http://b.com", "providerPublishTime": 1235},
    ]
    with patch("fetcher.yf.Ticker", return_value=mock_ticker):
        result = fetch_stock_news(["AAPL"])
    assert len(result) == 1
    assert "Fed" in result[0]["title"]


def test_fetch_stock_news_returns_empty_when_no_keywords():
    mock_ticker = MagicMock()
    mock_ticker.news = [
        {"title": "Company releases quarterly report", "link": "http://a.com", "providerPublishTime": 1234},
    ]
    with patch("fetcher.yf.Ticker", return_value=mock_ticker):
        result = fetch_stock_news(["AAPL"])
    assert result == []


# --- Regional equity fetchers ---

def _mock_group_by_ticker_data(tickers, close_values):
    """Build a fake multi-ticker yfinance download (group_by='ticker')."""
    outer = MagicMock()

    def getitem(ticker):
        inner = MagicMock()
        if ticker in tickers:
            idx = tickers.index(ticker)
            v1, v2 = close_values[idx]
            close_series = pd.Series([v1] * 30 + [v2])
            vol_series = pd.Series([1_000_000] * 30 + [2_000_000])
            inner.__getitem__ = lambda self, key: close_series if key == "Close" else vol_series
        else:
            inner.__getitem__ = lambda self, key: (_ for _ in ()).throw(KeyError(ticker))
        return inner

    outer.__getitem__ = getitem
    return outer


def test_fetch_london_movers_returns_movers():
    from config import LONDON_TICKERS
    tickers = LONDON_TICKERS[:2]
    close_values = [(500.0, 510.0), (300.0, 295.0)]
    mock_data = _mock_group_by_ticker_data(tickers, close_values)
    with patch("fetcher.yf.download", return_value=mock_data):
        with patch("fetcher.LONDON_TICKERS", tickers):
            result = fetch_london_movers()
    assert "top_movers" in result
    assert "on_the_rise" in result
    assert "timestamp" in result


def test_fetch_japan_movers_returns_movers():
    from config import JAPAN_TICKERS
    tickers = JAPAN_TICKERS[:2]
    close_values = [(2500.0, 2550.0), (15000.0, 14900.0)]
    mock_data = _mock_group_by_ticker_data(tickers, close_values)
    with patch("fetcher.yf.download", return_value=mock_data):
        with patch("fetcher.JAPAN_TICKERS", tickers):
            result = fetch_japan_movers()
    assert "top_movers" in result
    assert "on_the_rise" in result
    assert "timestamp" in result


def test_fetch_asia_movers_returns_movers():
    from config import ASIA_TICKERS
    tickers = ASIA_TICKERS[:2]
    close_values = [(350.0, 360.0), (80.0, 78.0)]
    mock_data = _mock_group_by_ticker_data(tickers, close_values)
    with patch("fetcher.yf.download", return_value=mock_data):
        with patch("fetcher.ASIA_TICKERS", tickers):
            result = fetch_asia_movers()
    assert "top_movers" in result
    assert "on_the_rise" in result
    assert "timestamp" in result


def test_fetch_regional_movers_handles_download_error():
    with patch("fetcher.yf.download", side_effect=Exception("network error")):
        result = fetch_london_movers()
    assert result["top_movers"] == []
    assert "error" in result
