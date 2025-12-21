# app/api/crypto.py
"""
Crypto-related API routes.

Endpoint:
  GET /api/crypto?coin=<coin_id>
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import CryptoResponse
from app.services.storage import save_json
from tools import CryptoAPIError, get_crypto_price

router = APIRouter(tags=["crypto"])


@router.get("/crypto", response_model=CryptoResponse)
def crypto_endpoint(coin: str) -> CryptoResponse:
    """
    Get current crypto price for a coin id.

    Query parameters:
      coin: CoinGecko coin id, e.g. "bitcoin"
    """
    coin = coin.strip().lower()
    if not coin:
        raise HTTPException(status_code=400, detail="coin query parameter is required.")

    try:
        data = get_crypto_price(coin)
    except CryptoAPIError as e:
        # Unknown coin or API/network issue
        raise HTTPException(status_code=400, detail=str(e)) from e

    coin_data = data.get(coin, {})
    try:
        price = float(coin_data.get("usd"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=500, detail="Unexpected crypto data format from API."
        )

    change_24h = coin_data.get("usd_24h_change")
    if change_24h is not None:
        try:
            change_24h = float(change_24h)
        except (TypeError, ValueError):
            change_24h = None

    # Save raw JSON to data/crypto_<coin>.json
    save_json("crypto", coin, data)

    return CryptoResponse(
        coin_id=coin,
        price_usd=price,
        change_24h=change_24h,
        raw=data,
    )