# app/api/weather.py
"""
Weather-related API routes.

Endpoint:
  GET /api/weather?city=<city>
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import WeatherResponse
from app.services.storage import save_json
from app.services.history import add_history  # <-- NEW
from tools import WeatherAPIError, get_weather

router = APIRouter(tags=["weather"])


@router.get("/weather", response_model=WeatherResponse)
def weather_endpoint(city: str) -> WeatherResponse:
    """
    Get current weather for a city.

    Query parameters:
      city: city name, e.g. "Hyderabad"
    """
    try:
        data = get_weather(city)
    except WeatherAPIError as e:
        # Return 400 Bad Request with the error message
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Extract important fields from raw data
    name = data.get("name", city)
    sys = data.get("sys", {})
    country = sys.get("country", "")
    main = data.get("main", {})
    weather_list = data.get("weather", [])
    description = (
        weather_list[0].get("description", "N/A") if weather_list else "N/A"
    )

    try:
        temp = float(main.get("temp"))
        feels_like = float(main.get("feels_like"))
        humidity = int(main.get("humidity"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="Weather data format unexpected from API.",
        )

    # Build response model
    response_model = WeatherResponse(
        city=name,
        country=country,
        temperature_c=temp,
        feels_like_c=feels_like,
        description=description,
        humidity=humidity,
        raw=data,
    )

    # Save raw JSON to data/weather_<city>.json
    save_json("weather", city, data)

    # Record in Phase 3 history
    add_history("weather", city, response_model.model_dump())

    return response_model