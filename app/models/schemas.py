# app/models/schemas.py
"""
Pydantic models (schemas) for API responses.

These define the shape of the JSON that the frontend / Postman receives.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class WeatherResponse(BaseModel):
    city: str
    country: str
    temperature_c: float
    feels_like_c: float
    description: str
    humidity: int
    raw: Dict[str, Any]  # full raw JSON from OpenWeatherMap


class CryptoResponse(BaseModel):
    coin_id: str
    price_usd: float
    change_24h: Optional[float] = None
    raw: Dict[str, Any]  # full raw JSON from CoinGecko