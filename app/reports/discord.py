import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def post_to_discord(message, embeds=None):
    if not WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL is not set. Skipping Discord post.")
        return

    payload = {
        "content": message[:1900],
    }

    if embeds:
        payload["embeds"] = embeds[:10]

    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        timeout=15
    )

    response.raise_for_status()
