import json
import os
import pytest
from unittest.mock import patch, mock_open
from datetime import datetime, timedelta
from alerts import (
    load_alert_state, save_alert_state, clear_stale_alerts,
    check_thresholds, is_duplicate_alert, mark_alert_fired,
)


def test_load_alert_state_returns_empty_when_file_missing():
    with patch("alerts.os.path.exists", return_value=False):
        result = load_alert_state()
    assert result == {}


def test_load_alert_state_returns_empty_on_corrupt_json():
    with patch("alerts.os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="not json")):
            result = load_alert_state()
    assert result == {}


def test_load_alert_state_returns_parsed_state():
    state = {"SPY_index_DOWN": "2026-05-26T10:00:00"}
    with patch("alerts.os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=json.dumps(state))):
            result = load_alert_state()
    assert result == state


def test_clear_stale_alerts_removes_old_entries():
    old_time = (datetime.now() - timedelta(minutes=90)).isoformat()
    recent_time = (datetime.now() - timedelta(minutes=10)).isoformat()
    state = {"old_alert": old_time, "recent_alert": recent_time}
    result = clear_stale_alerts(state)
    assert "old_alert" not in result
    assert "recent_alert" in result


def test_is_duplicate_alert_true_when_key_exists():
    state = {"AAPL_stock_UP": "2026-05-26T10:00:00"}
    assert is_duplicate_alert(state, "AAPL_stock_UP") is True


def test_is_duplicate_alert_false_when_key_missing():
    state = {}
    assert is_duplicate_alert(state, "AAPL_stock_UP") is False


def test_mark_alert_fired_adds_key_with_timestamp():
    state = {}
    result = mark_alert_fired(state, "NVDA_stock_UP")
    assert "NVDA_stock_UP" in result
    datetime.fromisoformat(result["NVDA_stock_UP"])


def test_check_thresholds_triggers_index_alert():
    market_data = {
        "stocks": {"SPY": {"price": 450.0, "pct_change": -2.1, "prev_close": 459.7}},
        "crypto": {},
    }
    alerts = check_thresholds(market_data)
    assert any(a["ticker"] == "SPY" for a in alerts)
    assert any(a["direction"] == "DOWN" for a in alerts)


def test_check_thresholds_no_alert_below_threshold():
    market_data = {
        "stocks": {"SPY": {"price": 450.0, "pct_change": -1.0, "prev_close": 454.5}},
        "crypto": {},
    }
    alerts = check_thresholds(market_data)
    assert not any(a["ticker"] == "SPY" for a in alerts)


def test_check_thresholds_triggers_stock_alert():
    market_data = {
        "stocks": {
            "SPY": {"price": 450.0, "pct_change": 0.2, "prev_close": 449.1},
            "NVDA": {"price": 900.0, "pct_change": 6.5, "prev_close": 845.1},
        },
        "crypto": {},
    }
    alerts = check_thresholds(market_data)
    assert any(a["ticker"] == "NVDA" for a in alerts)


def test_check_thresholds_triggers_crypto_alert():
    market_data = {
        "stocks": {},
        "crypto": {"BTC": {"price": 50000, "change_1h": -6.0}},
    }
    alerts = check_thresholds(market_data)
    assert any(a["ticker"] == "BTC" for a in alerts)
    assert any(a["direction"] == "DOWN" for a in alerts)


def test_check_thresholds_triggers_altcoin_alert():
    market_data = {
        "stocks": {},
        "crypto": {
            "BTC": {"price": 50000, "change_1h": 1.0},  # below threshold, not BTC/ETH
            "SOL": {"price": 150, "change_1h": 12.0},   # above 10% threshold
        },
    }
    alerts = check_thresholds(market_data)
    assert any(a["ticker"] == "SOL" for a in alerts)
    assert any(a["type"] == "crypto" for a in alerts)
    btc_alerts = [a for a in alerts if a["ticker"] == "BTC"]
    assert len(btc_alerts) == 0  # BTC at 1% should not trigger
