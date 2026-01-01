# app/api/debug.py

from fastapi import APIRouter, HTTPException, Query
from notifications.telegram import send_telegram_message

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/telegram-test")
async def telegram_test(
    chat_id: str = Query(..., description="Numeric Telegram chat ID"),
) -> dict:
    """
    Send a simple test message via Telegram to verify bot token + chat id.
    """
    try:
      await send_telegram_message(chat_id, "Test message from your FastAPI backend.")
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Telegram send failed: {e}") from e

    return {"ok": True}