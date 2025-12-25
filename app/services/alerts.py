# app/services/alerts.py

from __future__ import annotations

import asyncio
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from app.services.history import add_history
from tools import (
    CryptoAPIError,
    WeatherAPIError,
    get_crypto_price,
    get_weather,
)

AlertType = Literal["crypto_change", "weather_temp"]
Operator = Literal[">", "<"]


@dataclass
class Alert:
    id: str
    name: str
    enabled: bool
    type: AlertType        # "crypto_change" or "weather_temp"
    operator: Operator     # ">" or "<"
    threshold: float       # % for crypto_change, °C for weather_temp
    coin: Optional[str] = None   # for crypto_change
    city: Optional[str] = None   # for weather_temp
    last_trigger: Optional[str] = None  # ISO time last triggered
    last_status: Optional[str] = None   # last trigger message


_alerts: Dict[str, Alert] = {}
_alerts_task: Optional[asyncio.Task] = None

# how often to evaluate alerts (seconds)
ALERT_INTERVAL_SECONDS = 300  # 5 minutes


def create_alert(
    name: str,
    type: AlertType,
    operator: Operator,
    threshold: float,
    coin: Optional[str] = None,
    city: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an alert. For now we support:
    - crypto_change: coin required, threshold is 24h % change.
    - weather_temp: city required, threshold is temperature in °C.
    """
    if type == "crypto_change" and not coin:
        raise ValueError("coin is required for crypto_change alerts")
    if type == "weather_temp" and not city:
        raise ValueError("city is required for weather_temp alerts")

    alert_id = uuid.uuid4().hex
    alert = Alert(
        id=alert_id,
        name=name or "Alert",
        enabled=True,
        type=type,
        operator=operator,
        threshold=float(threshold),
        coin=coin or None,
        city=city or None,
        last_trigger=None,
        last_status=None,
    )
    _alerts[alert_id] = alert
    return asdict(alert)


def list_alerts() -> List[Dict[str, Any]]:
    return [asdict(a) for a in _alerts.values()]


def set_alert_enabled(alert_id: str, enabled: bool) -> Dict[str, Any]:
    alert = _alerts.get(alert_id)
    if not alert:
        raise KeyError(f"Alert {alert_id} not found")
    alert.enabled = enabled
    return asdict(alert)


def delete_alert(alert_id: str) -> None:
    if alert_id in _alerts:
        del _alerts[alert_id]
    else:
        raise KeyError(f"Alert {alert_id} not found")


async def _run_alerts() -> None:
    """
    Evaluate all alerts and trigger any that meet conditions.
    """
    if not _alerts:
        return

    now = datetime.utcnow()
    for alert in list(_alerts.values()):
        if not alert.enabled:
            continue
        await _execute_alert(alert, now)


async def _execute_alert(alert: Alert, run_time: datetime) -> None:
    """
    Evaluate a single alert and, if condition is met, log to history.
    For demo simplicity, if the condition is true, we log on every check.
    """
    parts: List[str] = []

    if alert.type == "crypto_change" and alert.coin:
        try:
            data = get_crypto_price(alert.coin)
            coin_data = data.get(alert.coin, {})
            change = coin_data.get("usd_24h_change")
            if isinstance(change, (int, float, float)):
                val = float(change)
                condition = (
                    val > alert.threshold if alert.operator == ">" else val < alert.threshold
                )
                direction = ">" if alert.operator == ">" else "<"
                parts.append(
                    f"{alert.coin.upper()} 24h change is {val:+.2f}% ({direction} {alert.threshold:.2f}%)"
                )
                if not condition:
                    # condition not met → just update last_status, no alert
                    alert.last_status = parts[-1]
                    return
            else:
                alert.last_status = f"{alert.coin.upper()}: 24h change unavailable"
                return
        except CryptoAPIError as e:
            alert.last_status = f"{alert.coin.upper()}: crypto alert error ({e})"
            return

    elif alert.type == "weather_temp" and alert.city:
        try:
            data = get_weather(alert.city)
            main = data.get("main", {})
            temp = main.get("temp")
            if temp is not None:
                val = float(temp)
                condition = (
                    val > alert.threshold if alert.operator == ">" else val < alert.threshold
                )
                direction = ">" if alert.operator == ">" else "<"
                parts.append(
                    f"{alert.city}: {val:.1f}°C ({direction} {alert.threshold:.1f}°C)"
                )
                if not condition:
                    alert.last_status = parts[-1]
                    return
            else:
                alert.last_status = f"{alert.city}: temperature unavailable"
                return
        except WeatherAPIError as e:
            alert.last_status = f"{alert.city}: weather alert error ({e})"
            return

    else:
        # unsupported type or missing data
        alert.last_status = "Alert misconfigured (missing city/coin or unsupported type)."
        return

    # If we reach here, the condition is met → trigger alert
    message = " | ".join(parts) if parts else "Alert condition met."
    alert.last_trigger = run_time.isoformat() + "Z"
    alert.last_status = message

    # Log into history like schedules, but with [Alert] prefix
    add_history("agent", f"[Alert] {alert.name}", {"answer": message})


async def _alerts_loop() -> None:
    """
    Background loop to periodically check alerts.
    """
    while True:
        try:
            await _run_alerts()
        except Exception as e:
            print(f"[alerts] error while evaluating alerts: {e}")
        await asyncio.sleep(ALERT_INTERVAL_SECONDS)


def start_alerts_loop() -> None:
    """
    Starts the alerts evaluation loop in the background.
    Called from FastAPI on startup.
    """
    global _alerts_task
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    if _alerts_task is None or _alerts_task.done():
        _alerts_task = loop.create_task(_alerts_loop())