from __future__ import annotations

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_TELEGRAM_ENABLED = bool(BOT_TOKEN)
_BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None


async def send_telegram_message(chat_id: str, text: str) -> None:
    """
    Send a Telegram message using the bot token.
    If TELEGRAM_BOT_TOKEN is not set, this is a no-op.
    """
    if not _TELEGRAM_ENABLED or not _BASE_URL:
        print("[telegram] not enabled (missing TELEGRAM_BOT_TOKEN)")
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_BASE_URL}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
            if resp.status_code != 200:
                print(f"[telegram] send failed: {resp.status_code} {resp.text}")
            else:
                print("[telegram] message sent")
    except Exception as e:
        print(f"[telegram] failed to send message: {e}")