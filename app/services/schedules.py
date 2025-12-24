# app/services/schedules.py

from __future__ import annotations

import asyncio
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
IST_OFFSET = timedelta(hours=5, minutes=30)  # UTC+5:30
from typing import Any, Dict, List, Optional

from app.services.history import add_history
from tools import (
    CryptoAPIError,
    WeatherAPIError,
    get_crypto_price,
    get_weather,
)


@dataclass
class Schedule:
    id: str
    name: str
    enabled: bool
    time_of_day: str  # "HH:MM" in 24h format, UTC
    city: Optional[str] = None
    coin: Optional[str] = None
    last_run: Optional[str] = None   # ISO UTC string
    next_run: Optional[str] = None   # ISO UTC string
    last_status: Optional[str] = None


_schedules: Dict[str, Schedule] = {}
_scheduler_task: Optional[asyncio.Task] = None


def _compute_next_run(time_of_day: str, from_dt: Optional[datetime] = None) -> datetime:
    """
    Compute the next UTC datetime corresponding to a given local IST HH:MM.

    - time_of_day is interpreted as IST (UTC+5:30).
    - from_dt is in UTC (defaults to datetime.utcnow()).
    - We compute the next time in IST, then convert back to UTC.
    """
    if from_dt is None:
        from_dt = datetime.utcnow()

    try:
        hour_str, minute_str = time_of_day.split(":")
        hour = int(hour_str)
        minute = int(minute_str)
    except Exception:
        # Fallback: run in 1 minute if invalid format
        return from_dt + timedelta(minutes=1)

    # Convert current UTC time to IST
    now_ist = from_dt + IST_OFFSET

    # Candidate run time in IST
    candidate_ist = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If the time today has already passed in IST, schedule for tomorrow
    if candidate_ist <= now_ist:
        candidate_ist += timedelta(days=1)

    # Convert candidate back to UTC for storage/scheduler
    candidate_utc = candidate_ist - IST_OFFSET
    return candidate_utc


def create_schedule(
    name: str,
    time_of_day: str,
    city: Optional[str] = None,
    coin: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a daily schedule. At least one of city or coin must be provided.
    """
    if not city and not coin:
        raise ValueError("At least one of city or coin must be provided for a schedule.")

    schedule_id = uuid.uuid4().hex
    now = datetime.utcnow()
    next_run_dt = _compute_next_run(time_of_day, now)

    sched = Schedule(
        id=schedule_id,
        name=name or "Daily Check",
        enabled=True,
        time_of_day=time_of_day,
        city=city or None,
        coin=coin or None,
        last_run=None,
        next_run=next_run_dt.isoformat() + "Z",
        last_status=None,
    )
    _schedules[schedule_id] = sched
    return asdict(sched)


def list_schedules() -> List[Dict[str, Any]]:
    """
    Return all schedules as plain dicts.
    """
    return [asdict(s) for s in _schedules.values()]


def set_schedule_enabled(schedule_id: str, enabled: bool) -> Dict[str, Any]:
    """
    Enable or disable a schedule.
    """
    sched = _schedules.get(schedule_id)
    if not sched:
        raise KeyError(f"Schedule {schedule_id} not found")

    sched.enabled = enabled
    if enabled and not sched.next_run:
        sched.next_run = _compute_next_run(sched.time_of_day).isoformat() + "Z"
    return asdict(sched)


def delete_schedule(schedule_id: str) -> None:
    """
    Delete a schedule by id.
    """
    if schedule_id in _schedules:
        del _schedules[schedule_id]
    else:
        raise KeyError(f"Schedule {schedule_id} not found")


async def _run_due_schedules() -> None:
    """
    Check all schedules and run any that are due.
    """
    if not _schedules:
        return

    now = datetime.utcnow()
    for sched in list(_schedules.values()):
        if not sched.enabled or not sched.next_run:
            continue

        try:
            # Strip trailing 'Z' if present
            next_run_dt = datetime.fromisoformat(sched.next_run.rstrip("Z"))
        except Exception:
            next_run_dt = now

        if now >= next_run_dt:
            await _execute_schedule(sched, now)


async def _execute_schedule(sched: Schedule, run_time: datetime) -> None:
    """
    Execute a single schedule: call tools and record a summary and history entry.
    """
    parts: List[str] = []

    if sched.city:
        try:
            data = get_weather(sched.city)
            main = data.get("main", {})
            weather_list = data.get("weather", [])
            temp = main.get("temp")
            desc = weather_list[0].get("description", "N/A") if weather_list else "N/A"
            if temp is not None:
                parts.append(f"{sched.city}: {temp}°C, {desc}")
            else:
                parts.append(f"{sched.city}: weather data unavailable")
        except WeatherAPIError as e:
            parts.append(f"{sched.city}: weather error ({e})")

    if sched.coin:
        try:
            data = get_crypto_price(sched.coin)
            coin_data = data.get(sched.coin, {})
            price = coin_data.get("usd")
            change = coin_data.get("usd_24h_change")
            if price is not None:
                text = f"{sched.coin.upper()}: ${price:.2f}"
                if isinstance(change, (int, float)):
                    text += f" ({change:+.2f}% 24h)"
                parts.append(text)
            else:
                parts.append(f"{sched.coin.upper()}: price unavailable")
        except CryptoAPIError as e:
            parts.append(f"{sched.coin.upper()}: crypto error ({e})")

    if not parts:
        summary = "No tools configured for this schedule."
    else:
        summary = " | ".join(parts)

    sched.last_run = run_time.isoformat() + "Z"
    sched.last_status = summary
    # schedule next run for tomorrow at the same time
    sched.next_run = _compute_next_run(sched.time_of_day, run_time).isoformat() + "Z"

    # Add to history as an 'agent'-style entry
    add_history("agent", f"[Schedule] {sched.name}", {"answer": summary})


async def _scheduler_loop() -> None:
    """
    Background loop that periodically checks and runs due schedules.
    """
    while True:
        try:
            await _run_due_schedules()
        except Exception as e:
            # Best-effort: don't crash loop on unexpected error
            print(f"[scheduler] error while running schedules: {e}")
        await asyncio.sleep(60)  # check every 60 seconds


def start_scheduler_loop() -> None:
    """
    Starts the scheduler loop in the background.
    Should be called once on app startup.
    """
    global _scheduler_task
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Not in an event loop: nothing we can do
        return

    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = loop.create_task(_scheduler_loop())