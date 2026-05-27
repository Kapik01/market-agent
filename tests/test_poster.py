from unittest.mock import patch, MagicMock
import pytest
from poster import post_to_discord, post_with_retry


def test_post_to_discord_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 204
    with patch("poster.requests.post", return_value=mock_resp) as mock_post:
        result = post_to_discord("https://discord.com/api/webhooks/test", "Hello")
    assert result is True
    mock_post.assert_called_once_with(
        "https://discord.com/api/webhooks/test",
        json={"content": "Hello"},
        timeout=10,
    )


def test_post_to_discord_failure():
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "Bad Request"
    with patch("poster.requests.post", return_value=mock_resp):
        result = post_to_discord("https://discord.com/api/webhooks/test", "Hello")
    assert result is False


def test_post_to_discord_truncates_long_message():
    long_msg = "x" * 3000
    mock_resp = MagicMock()
    mock_resp.status_code = 204
    with patch("poster.requests.post", return_value=mock_resp) as mock_post:
        post_to_discord("https://discord.com/api/webhooks/test", long_msg)
    sent = mock_post.call_args[1]["json"]["content"]
    assert len(sent) <= 2000


def test_post_with_retry_succeeds_first_attempt():
    with patch("poster.post_to_discord", return_value=True) as mock_post:
        result = post_with_retry("https://discord.com/api/webhooks/test", "Hi")
    assert result is True
    assert mock_post.call_count == 1


def test_post_with_retry_retries_on_failure():
    with patch("poster.post_to_discord", return_value=False):
        with patch("poster.time.sleep"):
            result = post_with_retry("https://discord.com/api/webhooks/test", "Hi", retries=3)
    assert result is False


def test_post_with_retry_succeeds_on_second_attempt():
    with patch("poster.post_to_discord", side_effect=[False, True]) as mock_post:
        with patch("poster.time.sleep"):
            result = post_with_retry("https://discord.com/api/webhooks/test", "Hi")
    assert result is True
    assert mock_post.call_count == 2
