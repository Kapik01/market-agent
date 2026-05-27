from unittest.mock import patch, MagicMock
from datetime import datetime
import pytz
import pytest
from main import is_usa_market_hours, is_london_market_hours, is_japan_market_hours, is_asia_market_hours


ET = pytz.timezone("America/New_York")
LONDON_TZ = pytz.timezone("Europe/London")
TOKYO_TZ = pytz.timezone("Asia/Tokyo")
HK_TZ = pytz.timezone("Asia/Hong_Kong")


# --- USA market hours ---

def test_is_usa_market_hours_true_during_session():
    fake_now = ET.localize(datetime(2026, 5, 26, 11, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_usa_market_hours() is True


def test_is_usa_market_hours_false_before_open():
    fake_now = ET.localize(datetime(2026, 5, 26, 9, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_usa_market_hours() is False


def test_is_usa_market_hours_false_after_close():
    fake_now = ET.localize(datetime(2026, 5, 26, 16, 30))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_usa_market_hours() is False


def test_is_usa_market_hours_false_on_weekend():
    fake_now = ET.localize(datetime(2026, 5, 23, 11, 0))  # Saturday
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_usa_market_hours() is False


# --- London market hours ---

def test_is_london_market_hours_true_during_session():
    # 10 AM London time on a weekday
    fake_now = LONDON_TZ.localize(datetime(2026, 5, 26, 10, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_london_market_hours() is True


def test_is_london_market_hours_false_after_close():
    fake_now = LONDON_TZ.localize(datetime(2026, 5, 26, 17, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_london_market_hours() is False


def test_is_london_market_hours_false_on_weekend():
    fake_now = LONDON_TZ.localize(datetime(2026, 5, 23, 10, 0))  # Saturday
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_london_market_hours() is False


# --- Japan market hours ---

def test_is_japan_market_hours_true_during_session():
    fake_now = TOKYO_TZ.localize(datetime(2026, 5, 26, 10, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_japan_market_hours() is True


def test_is_japan_market_hours_false_after_close():
    fake_now = TOKYO_TZ.localize(datetime(2026, 5, 26, 16, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_japan_market_hours() is False


def test_is_japan_market_hours_false_on_weekend():
    fake_now = TOKYO_TZ.localize(datetime(2026, 5, 23, 10, 0))  # Saturday
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_japan_market_hours() is False


# --- Asia market hours ---

def test_is_asia_market_hours_true_during_session():
    fake_now = HK_TZ.localize(datetime(2026, 5, 26, 11, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_asia_market_hours() is True


def test_is_asia_market_hours_false_after_close():
    fake_now = HK_TZ.localize(datetime(2026, 5, 26, 17, 0))
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_asia_market_hours() is False


def test_is_asia_market_hours_false_on_weekend():
    fake_now = HK_TZ.localize(datetime(2026, 5, 23, 11, 0))  # Saturday
    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.return_value = fake_now
        assert is_asia_market_hours() is False


# --- run_hourly routing ---

def test_run_hourly_posts_crypto_and_forex_when_all_markets_closed():
    # 8 PM ET on a weekday — all stock markets closed
    fake_now_et = ET.localize(datetime(2026, 5, 26, 20, 0))
    fake_now_london = LONDON_TZ.localize(datetime(2026, 5, 27, 1, 0))   # 1 AM London
    fake_now_tokyo = TOKYO_TZ.localize(datetime(2026, 5, 27, 9, 0))     # 9 AM Tokyo — OPEN
    fake_now_hk = HK_TZ.localize(datetime(2026, 5, 27, 8, 0))           # 8 AM HK — before open

    def fake_now(tz):
        tz_str = str(tz)
        if "New_York" in tz_str:
            return fake_now_et
        if "London" in tz_str:
            return fake_now_london
        if "Tokyo" in tz_str:
            return fake_now_tokyo
        if "Hong_Kong" in tz_str:
            return fake_now_hk
        return fake_now_et

    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.side_effect = fake_now
        with patch("main.fetch_crypto_data", return_value={"coins": []}) as mock_crypto:
            with patch("main.fetch_forex_data", return_value={"pairs": []}) as mock_forex:
                with patch("main.fetch_stock_movers") as mock_usa:
                    with patch("main.fetch_japan_movers", return_value={"top_movers": []}) as mock_japan:
                        with patch("main.analyze_crypto", return_value="msg"):
                            with patch("main.analyze_forex", return_value="msg"):
                                with patch("main.analyze_stocks_japan", return_value="msg"):
                                    with patch("main.post_to_discord"):
                                        from main import run_hourly
                                        run_hourly()
        mock_crypto.assert_called_once()
        mock_forex.assert_called_once()
        mock_usa.assert_not_called()
        mock_japan.assert_called_once()


def test_run_hourly_posts_usa_during_us_market_hours():
    fake_now_et = ET.localize(datetime(2026, 5, 26, 11, 0))       # 11 AM ET — USA open
    fake_now_london = LONDON_TZ.localize(datetime(2026, 5, 26, 16, 0))  # 4 PM London — closed
    fake_now_tokyo = TOKYO_TZ.localize(datetime(2026, 5, 27, 0, 0))     # midnight Tokyo — closed
    fake_now_hk = HK_TZ.localize(datetime(2026, 5, 26, 23, 0))          # 11 PM HK — closed

    def fake_now(tz):
        tz_str = str(tz)
        if "New_York" in tz_str:
            return fake_now_et
        if "London" in tz_str:
            return fake_now_london
        if "Tokyo" in tz_str:
            return fake_now_tokyo
        if "Hong_Kong" in tz_str:
            return fake_now_hk
        return fake_now_et

    with patch("main.datetime") as mock_dt_cls:
        mock_dt_cls.now.side_effect = fake_now
        with patch("main.fetch_crypto_data", return_value={"coins": []}):
            with patch("main.fetch_forex_data", return_value={"pairs": []}):
                with patch("main.fetch_stock_movers", return_value={"top_movers": []}) as mock_usa:
                    with patch("main.fetch_commodity_data", return_value={"commodities": []}) as mock_comm:
                        with patch("main.fetch_japan_movers") as mock_japan:
                            with patch("main.analyze_stocks_usa", return_value="msg"):
                                with patch("main.analyze_crypto", return_value="msg"):
                                    with patch("main.analyze_forex", return_value="msg"):
                                        with patch("main.analyze_commodities", return_value="msg"):
                                            with patch("main.post_to_discord"):
                                                from main import run_hourly
                                                run_hourly()
        mock_usa.assert_called_once()
        mock_comm.assert_called_once()
        mock_japan.assert_not_called()
