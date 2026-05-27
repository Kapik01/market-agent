import requests
import logging
import time

logger = logging.getLogger(__name__)

DISCORD_MAX_LENGTH = 2000


def post_to_discord(webhook_url: str, message: str) -> bool:
    if len(message) > DISCORD_MAX_LENGTH:
        message = message[: DISCORD_MAX_LENGTH - 3] + "..."
    response = requests.post(webhook_url, json={"content": message}, timeout=10)
    if response.status_code == 204:
        return True
    logger.error(f"Discord post failed: {response.status_code} {response.text}")
    return False


def post_with_retry(webhook_url: str, message: str, retries: int = 3) -> bool:
    for attempt in range(retries):
        if post_to_discord(webhook_url, message):
            return True
        if attempt < retries - 1:
            time.sleep(5)
    logger.error(f"Discord post failed after {retries} attempts")
    return False
