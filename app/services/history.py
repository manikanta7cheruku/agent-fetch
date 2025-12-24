# app/services/history.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Tuple

HistoryKind = Literal["weather", "crypto", "agent"]

# Simple in-memory ring buffer
_MAX_ITEMS = 200
_items: List[Dict[str, Any]] = []


def add_history(kind: HistoryKind, query: str, result: Dict[str, Any]) -> None:
    """
    Record a history entry in memory.

    kind: "weather" | "crypto" | "agent"
    query: what the user asked (city, coin, or message)
    result: a small dict with the response data
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "kind": kind,
        "query": query,
        "result": result,
    }
    _items.append(entry)
    if len(_items) > _MAX_ITEMS:
        # keep a fixed-size buffer
        del _items[0 : len(_items) - _MAX_ITEMS]


def get_recent(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Return the most recent history entries (newest first).
    """
    if limit <= 0:
        return []
    return list(reversed(_items[-limit:]))