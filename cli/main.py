# cli/main.py
"""
Command-line interface (CLI) for developers / power users.

Usage examples (from project root, inside Poetry env):
  poetry run app weather --city Hyderabad
  poetry run app crypto --coin bitcoin


  This is for developers; normal users won’t use it.

This CLI:
- Calls the same tools as the web backend,
- Prints a human summary,
- Saves raw JSON into `data/` by default.
"""

from __future__ import annotations

from typing import Any, Dict

import typer

from app.services.storage import save_json
from tools import (
    CryptoAPIError,
    WeatherAPIError,
    get_crypto_price,
    get_weather,
)
from agent.simple_agent import run_agent # 

# Create Typer app instance
app = typer.Typer(help="Weather & crypto tools for the agentic dashboard.")


def _print_weather_summary(data: Dict[str, Any]) -> None:
    """Pretty-print a weather summary from the raw API data."""
    name = data.get("name", "Unknown")
    sys = data.get("sys", {})
    country = sys.get("country", "")
    main = data.get("main", {})
    weather_list = data.get("weather", [])
    description = (
        weather_list[0].get("description", "N/A") if weather_list else "N/A"
    )

    temp = main.get("temp", "N/A")
    feels_like = main.get("feels_like", "N/A")
    humidity = main.get("humidity", "N/A")

    typer.echo(f"\nWeather in {name}, {country}")
    typer.echo(f"  Temperature: {temp} °C (feels like {feels_like} °C)")
    typer.echo(f"  Conditions:  {description}")
    typer.echo(f"  Humidity:    {humidity}%\n")


def _print_crypto_summary(coin: str, data: Dict[str, Any]) -> None:
    """Pretty-print a crypto summary from the raw API data."""
    coin_data = data.get(coin, {})
    price = coin_data.get("usd", "N/A")
    change_24h = coin_data.get("usd_24h_change", None)

    typer.echo(f"\nCrypto: {coin}")
    typer.echo(f"  Price (USD): {price}")
    if isinstance(change_24h, (int, float)):
        typer.echo(f"  24h Change:  {change_24h:.2f}%")
    typer.echo("")


@app.command()
def weather(
    city: str = typer.Option(
        ...,
        "--city",
        "-c",
        help="City name, e.g. Hyderabad, London, New York.",
    ),
    raw: bool = typer.Option(
        False, "--raw", help="Print raw JSON response as well."
    ),
    no_save: bool = typer.Option(
        False,
        "--no-save",
        help="Do not save JSON to the data/ folder.",
    ),
) -> None:
    """
    Get current weather for a city.
    """
    try:
        data = get_weather(city)
    except WeatherAPIError as e:
        typer.echo(f"[Error] {e}")
        raise typer.Exit(code=1)

    _print_weather_summary(data)

    if raw:
        typer.echo("Raw JSON (OpenWeatherMap):")
        typer.echo(data)

    if not no_save:
        path = save_json("weather", city, data)
        typer.echo(f"Raw JSON saved to: {path}")


@app.command()
def crypto(
    coin: str = typer.Option(
        ...,
        "--coin",
        "-k",
        help="CoinGecko coin id (lowercase), e.g. bitcoin, ethereum, solana.",
    ),
    raw: bool = typer.Option(
        False, "--raw", help="Print raw JSON response as well."
    ),
    no_save: bool = typer.Option(
        False,
        "--no-save",
        help="Do not save JSON to the data/ folder.",
    ),
) -> None:
    """
    Get current crypto price for a coin.
    """
    coin = coin.strip().lower()
    if not coin:
        typer.echo("[Error] Coin id cannot be empty.")
        raise typer.Exit(code=1)

    try:
        data = get_crypto_price(coin)
    except CryptoAPIError as e:
        typer.echo(f"[Error] {e}")
        raise typer.Exit(code=1)

    _print_crypto_summary(coin, data)

    if raw:
        typer.echo("Raw JSON (CoinGecko):")
        typer.echo(data)

    if not no_save:
        path = save_json("crypto", coin, data)
        typer.echo(f"Raw JSON saved to: {path}")


@app.command()
def chat(
    message: str = typer.Option(
        None,
        "--message",
        "-m",
        help="Question for the AI agent about weather/crypto. If omitted, you'll be prompted.",
    )
) -> None:
    """
    Ask a natural language question to the AI agent.

    Examples:
      python -m cli.main chat -m "What's the weather in Hyderabad and BTC price?"
      python -m cli.main chat
    """
    # If --message is not provided, read from stdin
    if not message:
        message = input("You: ")

    answer = run_agent(message)
    typer.echo(f"Agent: {answer}")


if __name__ == "__main__":
    app()





# inside project root, in `poetry shell`
# poetry run app --help
# poetry run app weather --city Hyderabad
# poetry run app crypto --coin bitcoin