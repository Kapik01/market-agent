import anthropic
from datetime import datetime
import pytz
from config import ANTHROPIC_API_KEY, MODEL
from prompts import (
    STOCKS_SYSTEM_PROMPT, CRYPTO_SYSTEM_PROMPT, FOREX_SYSTEM_PROMPT,
    COMMODITIES_SYSTEM_PROMPT, EOD_SYSTEM_PROMPT, ALERT_SYSTEM_PROMPT,
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
ET = pytz.timezone("America/New_York")


def _now_et() -> str:
    return datetime.now(ET).strftime("%A, %b %d %I:%M %p ET")


def _call_claude(system_prompt: str, user_content: str, max_tokens: int = 1500) -> str:
    message = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_content}],
    )
    if not message.content:
        raise ValueError(f"Claude returned empty content (stop_reason={message.stop_reason})")
    return message.content[0].text


def analyze_stocks(data: dict) -> str:
    return _call_claude(STOCKS_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nCurrent US stock market data:\n{data}")


def analyze_crypto(data: dict) -> str:
    return _call_claude(CRYPTO_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nCurrent crypto market data:\n{data}")


def analyze_forex(data: dict) -> str:
    return _call_claude(FOREX_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nCurrent forex data:\n{data}")


def analyze_commodities(data: dict) -> str:
    return _call_claude(COMMODITIES_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nCurrent commodities data:\n{data}")


def analyze_eod(all_data: dict) -> str:
    return _call_claude(EOD_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nFull trading day data:\n{all_data}", max_tokens=2500)


def analyze_alert(alert: dict) -> str:
    return _call_claude(ALERT_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nAlert triggered:\n{alert}", max_tokens=500)
