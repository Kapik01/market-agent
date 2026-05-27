from unittest.mock import patch, MagicMock
from datetime import datetime
import pytz
import pytest
from main import is_market_hours


ET = pytz.timezone("America/New_York")


def test_is_market_hours_true_during_session():
    fake_now = ET.localize(datetime(2026, 5, 26, 11, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        result = is_market_hours()
    assert result is True


def test_is_market_hours_false_before_open():
    fake_now = ET.localize(datetime(2026, 5, 26, 9, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        result = is_market_hours()
    assert result is False


def test_is_market_hours_false_after_close():
    fake_now = ET.localize(datetime(2026, 5, 26, 16, 30))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        result = is_market_hours()
    assert result is False


def test_is_market_hours_false_on_weekend():
    fake_now = ET.localize(datetime(2026, 5, 23, 11, 0))  # Saturday
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        result = is_market_hours()
    assert result is False


def test_run_hourly_posts_crypto_and_forex_after_hours():
    fake_now = ET.localize(datetime(2026, 5, 26, 20, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        with patch("main.fetch_crypto_data", return_value={"coins": []}) as mock_crypto:
            with patch("main.fetch_forex_data", return_value={"pairs": []}) as mock_forex:
                with patch("main.fetch_stock_movers") as mock_stocks:
                    with patch("main.analyze_crypto", return_value="msg"):
                        with patch("main.analyze_forex", return_value="msg"):
                            with patch("main.post_to_discord"):
                                from main import run_hourly
                                run_hourly()
        mock_crypto.assert_called_once()
        mock_forex.assert_called_once()
        mock_stocks.assert_not_called()


def test_run_hourly_posts_all_channels_during_market_hours():
    fake_now = ET.localize(datetime(2026, 5, 26, 11, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        with patch("main.fetch_crypto_data", return_value={"coins": []}):
            with patch("main.fetch_forex_data", return_value={"pairs": []}):
                with patch("main.fetch_stock_movers", return_value={"top_movers": []}) as mock_stocks:
                    with patch("main.fetch_commodity_data", return_value={"commodities": []}) as mock_comm:
                        with patch("main.analyze_stocks", return_value="msg"):
                            with patch("main.analyze_crypto", return_value="msg"):
                                with patch("main.analyze_forex", return_value="msg"):
                                    with patch("main.analyze_commodities", return_value="msg"):
                                        with patch("main.post_to_discord"):
                                            from main import run_hourly
                                            run_hourly()
        mock_stocks.assert_called_once()
        mock_comm.assert_called_once()
