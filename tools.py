# tools.py
"""
Core tools for the application.

These are plain Python functions (no FastAPI or CLI logic here) that:
- Call external APIs (OpenWeatherMap, CoinGecko),
- Handle errors and return parsed JSON as Python dicts.

Later, these functions can be exposed directly to an LLM agent as tools.
"""

from __future__ import annotations

from typing import Any, Dict

import httpx

from app.core.config import settings


class WeatherAPIError(Exception):
    """Raised for weather API related errors."""


class CryptoAPIError(Exception):
    """Raised for crypto API related errors."""


def get_weather(city: str) -> Dict[str, Any]:
    """
    Get current weather for a city from OpenWeatherMap.

    Args:
        city: City name, e.g. "Hyderabad", "London", "New York".

    Returns:
        The raw JSON response as a Python dict.

    Raises:
        WeatherAPIError: on invalid city, network issues, or API errors.
    """
    base_url = "https://api.openweathermap.org/data/2.5/weather"

    try:
        response = httpx.get(
            base_url,
            params={
                "q": city,
                "appid": settings.openweather_api_key,  # API key from .env
                "units": "metric",                      # Celsius
            },
            timeout=10.0,  # seconds
        )
    except httpx.RequestError as exc:
        # Network-level error (DNS, connection refused, timeout, etc.)
        raise WeatherAPIError(f"Network error while calling weather API: {exc}") from exc

    if response.status_code == 404:
        # OpenWeatherMap often returns 404 if the city is not found
        raise WeatherAPIError(f"City '{city}' not found.")
    if response.status_code != 200:
        # Any other non-success status
        raise WeatherAPIError(
            f"Weather API error (status {response.status_code}): {response.text}"
        )

    return response.json()


def get_crypto_price(coin: str) -> Dict[str, Any]:
    """
    Get current crypto price for a coin from CoinGecko.

    Uses the 'simple price' endpoint, includes 24h change.

    Args:
        coin: CoinGecko coin id (lowercase), e.g. "bitcoin", "ethereum".

    Returns:
        Raw JSON as a dict. Example:
        {
          "bitcoin": {
            "usd": 12345.67,
            "usd_24h_change": 1.23
          }
        }

    Raises:
        CryptoAPIError: on unknown coin, network issues, or API errors.
    """
    base_url = "https://api.coingecko.com/api/v3/simple/price"

    try:
        response = httpx.get(
            base_url,
            params={
                "ids": coin,                     # coin id(s)
                "vs_currencies": "usd",          # we want USD price
                "include_24hr_change": "true",   # include 24h percentage change
            },
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        # Network-level error (DNS, timeout, etc.)
        raise CryptoAPIError(f"Network error while calling crypto API: {exc}") from exc

    # Special case: rate limit / 429 from CoinGecko
    if response.status_code == 429:
        raise CryptoAPIError(
            "Crypto data provider is temporarily rate-limited. "
            "Please try again in a few minutes."
        )

    # Any other non-success status
    if response.status_code != 200:
        raise CryptoAPIError(
            f"Crypto API error (status {response.status_code}). Please try again later."
        )

    data = response.json()

    # CoinGecko returns {} or missing key if coin is unknown
    if coin not in data or "usd" not in data[coin]:
        raise CryptoAPIError(
            f"Coin '{coin}' not found or has no USD price in CoinGecko."
        )

    return data