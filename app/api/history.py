# app/api/history.py

from typing import Any, Dict, List

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.history import get_recent

router = APIRouter(tags=["history"])


class HistoryItem(BaseModel):
    timestamp: str
    kind: str
    query: str
    result: Dict[str, Any]


@router.get("/history", response_model=List[HistoryItem])
def list_history(limit: int = Query(20, ge=1, le=200)) -> List[HistoryItem]:
    """
    Return recent history entries (newest first).
    """
    items = get_recent(limit=limit)
    return [HistoryItem(**item) for item in items]