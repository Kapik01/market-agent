from unittest.mock import patch, MagicMock
import pytest
from analyzer import analyze_stocks, analyze_crypto, analyze_eod, analyze_alert


def _mock_claude_response(text: str):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=text)]
    return mock_msg


def test_analyze_stocks_returns_string():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_claude_response("📊 **MARKET PULSE — STOCKS**")
    with patch("analyzer.anthropic.Anthropic", return_value=mock_client):
        import importlib
        import analyzer
        importlib.reload(analyzer)
        result = analyzer.analyze_stocks({"top_movers": [], "on_the_rise": []})
    assert isinstance(result, str)
    assert len(result) > 0


def test_analyze_stocks_passes_system_prompt_with_cache_control():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_claude_response("ok")
    with patch("analyzer.anthropic.Anthropic", return_value=mock_client):
        import importlib
        import analyzer
        importlib.reload(analyzer)
        analyzer.analyze_stocks({"top_movers": [], "on_the_rise": []})

    call_kwargs = mock_client.messages.create.call_args[1]
    system = call_kwargs["system"]
    assert isinstance(system, list)
    assert system[0]["cache_control"] == {"type": "ephemeral"}


def test_analyze_crypto_calls_claude_with_crypto_prompt():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_claude_response("🪙 **MARKET PULSE — CRYPTO**")
    with patch("analyzer.anthropic.Anthropic", return_value=mock_client):
        import importlib
        import analyzer
        importlib.reload(analyzer)
        result = analyzer.analyze_crypto({"coins": []})
    assert isinstance(result, str)


def test_analyze_eod_calls_claude_with_eod_prompt():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_claude_response("📋 **END OF DAY**")
    with patch("analyzer.anthropic.Anthropic", return_value=mock_client):
        import importlib
        import analyzer
        importlib.reload(analyzer)
        result = analyzer.analyze_eod({"stocks": {}, "crypto": {}, "fundamentals": []})
    assert isinstance(result, str)


def test_analyze_alert_calls_claude_with_alert_prompt():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_claude_response("🚨 **BREAKING ALERT**")
    with patch("analyzer.anthropic.Anthropic", return_value=mock_client):
        import importlib
        import analyzer
        importlib.reload(analyzer)
        result = analyzer.analyze_alert({"type": "stock", "ticker": "NVDA", "pct_change": 6.5})
    assert isinstance(result, str)
