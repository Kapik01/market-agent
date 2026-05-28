import anthropic
from datetime import datetime
import pytz
from config import ANTHROPIC_API_KEY, MODEL
from prompts import (
    STOCKS_USA_SYSTEM_PROMPT, STOCKS_LONDON_SYSTEM_PROMPT,
    STOCKS_JAPAN_SYSTEM_PROMPT, STOCKS_ASIA_SYSTEM_PROMPT,
    PREMARKET_USA_SYSTEM_PROMPT, PREMARKET_LONDON_SYSTEM_PROMPT,
    PREMARKET_JAPAN_SYSTEM_PROMPT, PREMARKET_ASIA_SYSTEM_PROMPT,
    CRYPTO_SYSTEM_PROMPT, FOREX_SYSTEM_PROMPT,
    COMMODITIES_SYSTEM_PROMPT, EOD_SYSTEM_PROMPT, ALERT_SYSTEM_PROMPT,
    WATCHLIST_SYSTEM_PROMPT,
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


def analyze_stocks_usa(data: dict) -> str:
    return _call_claude(STOCKS_USA_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nCurrent US stock market data:\n{data}")


def analyze_stocks_london(data: dict) -> str:
    return _call_claude(STOCKS_LONDON_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nCurrent London (LSE) stock market data:\n{data}")


def analyze_stocks_japan(data: dict) -> str:
    return _call_claude(STOCKS_JAPAN_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nCurrent Japan (TSE) stock market data:\n{data}")


def analyze_stocks_asia(data: dict) -> str:
    return _call_claude(STOCKS_ASIA_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nCurrent Asia (HKEX) stock market data:\n{data}")


def analyze_crypto(data: dict) -> str:
    return _call_claude(CRYPTO_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nCurrent crypto market data:\n{data}")


def analyze_forex(data: dict) -> str:
    return _call_claude(FOREX_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nCurrent forex data:\n{data}")


def analyze_commodities(data: dict) -> str:
    return _call_claude(COMMODITIES_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nCurrent commodities data:\n{data}")


def analyze_eod(all_data: dict) -> str:
    return _call_claude(
        EOD_SYSTEM_PROMPT,
        f"Current datetime: {_now_et()}\n\nFull trading day data (all sessions):\n{all_data}",
        max_tokens=2500,
    )


def analyze_eod_speculative(speculative_data: list) -> str:
    prompt = """You are MarketPulse writing the speculative picks section of an end-of-day summary for Discord.

Rules:
- Use Discord Markdown formatting
- Be honest about risk — these are high-risk plays
- Never say "you should buy/sell"
- Only include tickers where price, pct_change, and volume_ratio are provided

Output this exact structure:
---
**🚀 Speculative Picks — Rising Stars**
*These are high-risk plays. Small positions only.*

**[TICKER]** | $X.XX (under $15)
• Volume: [X.Xx average]
• Move today: [+/-X.X%]
• Catalyst: [one sentence on what drove it]
• Thesis: [1–2 sentences on why this could run given current sector trends]
• ⚠️ Risk: [one sentence — be honest about downside]

(repeat for 2–3 picks)
---"""
    return _call_claude(prompt, f"Current datetime: {_now_et()}\n\nSpeculative picks data:\n{speculative_data}", max_tokens=1000)


def analyze_premarket_usa(data: dict) -> str:
    return _call_claude(PREMARKET_USA_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nPre-market data:\n{data}")


def analyze_premarket_london(data: dict) -> str:
    return _call_claude(PREMARKET_LONDON_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nOvernight data for London pre-market:\n{data}")


def analyze_premarket_japan(data: dict) -> str:
    return _call_claude(PREMARKET_JAPAN_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nOvernight data for Japan pre-market:\n{data}")


def analyze_premarket_asia(data: dict) -> str:
    return _call_claude(PREMARKET_ASIA_SYSTEM_PROMPT, f"Current datetime: {_now_et()}\n\nOvernight data for Asia pre-market:\n{data}")


def analyze_watchlist(data: dict) -> str:
    return _call_claude(
        WATCHLIST_SYSTEM_PROMPT,
        f"Current datetime: {_now_et()}\n\nToday's market data for watchlist analysis:\n{data}",
        max_tokens=1500,
    )


def analyze_alert(alert: dict, news_headlines: list[str] | None = None) -> str:
    context = f"Current datetime: {_now_et()}\n\nAlert triggered:\n{alert}"
    if news_headlines:
        lines = "\n".join(f"- {h}" for h in news_headlines)
        context += f"\n\nRecent news headlines for {alert.get('ticker', 'this asset')}:\n{lines}"
    else:
        context += "\n\nRecent news headlines: None available."
    return _call_claude(ALERT_SYSTEM_PROMPT, context, max_tokens=800)
