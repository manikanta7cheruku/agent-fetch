# app/api/alerts.py

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.alerts import (
    create_alert,
    delete_alert,
    list_alerts,
    set_alert_enabled,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    name: str = Field(..., description="Friendly name for the alert")
    type: Literal["crypto_change", "weather_temp"] = Field(
        "crypto_change", description="Type of alert: crypto_change or weather_temp"
    )
    operator: Literal[">", "<"] = Field(
        ">", description="Use '>' or '<' for threshold comparison"
    )
    threshold: float = Field(
        ..., description="24h % change for crypto_change, temperature °C for weather_temp"
    )
    coin: Optional[str] = Field(
        None, description="Coin id (e.g. bitcoin) for crypto_change alerts"
    )
    city: Optional[str] = Field(
        None, description="City name for weather_temp alerts"
    )


class AlertOut(BaseModel):
    id: str
    name: str
    enabled: bool
    type: str
    operator: str
    threshold: float
    coin: Optional[str] = None
    city: Optional[str] = None
    last_trigger: Optional[str] = None
    last_status: Optional[str] = None


class AlertToggle(BaseModel):
    enabled: bool


@router.get("", response_model=List[AlertOut])
def get_alerts() -> List[AlertOut]:
    items = list_alerts()
    return [AlertOut(**item) for item in items]


@router.post("", response_model=AlertOut)
def create_alert_endpoint(body: AlertCreate) -> AlertOut:
    try:
        data: Dict[str, Any] = create_alert(
            name=body.name.strip() or "Alert",
            type=body.type,
            operator=body.operator,
            threshold=body.threshold,
            coin=body.coin.strip().lower() if body.coin else None,
            city=body.city.strip() if body.city else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return AlertOut(**data)


@router.patch("/{alert_id}", response_model=AlertOut)
def toggle_alert(alert_id: str, body: AlertToggle) -> AlertOut:
    try:
        data = set_alert_enabled(alert_id, body.enabled)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return AlertOut(**data)


@router.delete("/{alert_id}", status_code=204)
def delete_alert_endpoint(alert_id: str) -> None:
    try:
        delete_alert(alert_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e