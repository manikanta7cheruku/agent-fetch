# app/api/schedules.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.schedules import (
    create_schedule,
    list_schedules,
    set_schedule_enabled,
    delete_schedule, 
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


class ScheduleCreate(BaseModel):
    name: str = Field(..., description="Friendly name for the schedule")
    time_of_day: str = Field(
        "08:00",
        pattern=r"^\d{2}:\d{2}$",
        description="IST time in HH:MM 24h format (UTC+5:30), e.g. 08:00 or 20:30",
    )
    city: Optional[str] = Field(None, description="City for weather (optional)")
    coin: Optional[str] = Field(None, description="Coin id for crypto (optional)")


class ScheduleOut(BaseModel):
    id: str
    name: str
    enabled: bool
    time_of_day: str
    city: Optional[str] = None
    coin: Optional[str] = None
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    last_status: Optional[str] = None


class ScheduleToggle(BaseModel):
    enabled: bool


@router.get("", response_model=List[ScheduleOut])
def get_schedules() -> List[ScheduleOut]:
    """
    List all schedules.
    """
    items = list_schedules()
    return [ScheduleOut(**item) for item in items]


@router.post("", response_model=ScheduleOut)
def create_schedule_endpoint(body: ScheduleCreate) -> ScheduleOut:
    """
    Create a daily schedule. At least one of city or coin must be provided.
    """
    if not body.city and not body.coin:
        raise HTTPException(
            status_code=400,
            detail="At least one of city or coin must be provided for a schedule.",
        )

    try:
        data: Dict[str, Any] = create_schedule(
            name=body.name.strip() or "Daily Check",
            time_of_day=body.time_of_day,
            city=body.city.strip() if body.city else None,
            coin=body.coin.strip().lower() if body.coin else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return ScheduleOut(**data)


@router.patch("/{schedule_id}", response_model=ScheduleOut)
def toggle_schedule(schedule_id: str, body: ScheduleToggle) -> ScheduleOut:
    """
    Enable or disable a schedule.
    """
    try:
        data = set_schedule_enabled(schedule_id, body.enabled)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return ScheduleOut(**data)




@router.delete("/{schedule_id}", status_code=204)
def delete_schedule_endpoint(schedule_id: str) -> None:
    """
    Delete a schedule.
    """
    try:
        delete_schedule(schedule_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e