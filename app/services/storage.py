# app/services/storage.py
"""
Simple JSON storage utility.

Right now we store raw API responses in the `data/` folder as:
- data/weather_<city>.json
- data/crypto_<coin>.json

Later, this module can be replaced or extended to write to a real database.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

# BASE_DIR = project root, two levels up from this file: app/services/storage.py
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


def ensure_data_dir() -> None:
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_json(category: str, name: str, payload: Dict[str, Any]) -> Path:
    """
    Save JSON payload into a file like data/<category>_<name>.json.

    Example:
        category="weather", name="Hyderabad" -> data/weather_hyderabad.json

    Args:
        category: "weather" or "crypto" (or other in future).
        name: city or coin identifier.
        payload: dict to save as JSON.

    Returns:
        Path to the saved file.
    """
    ensure_data_dir()
    # sanitize name for filename: lowercase, spaces -> underscores
    safe_name = name.strip().replace(" ", "_").lower()
    filename = f"{category}_{safe_name}.json"
    path = DATA_DIR / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return path