# app/core/config.py
"""
Simple configuration loader.

- Loads .env from the project root using python-dotenv.
- Exposes a Settings object with openweather_api_key.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Compute project root: app/core/config.py -> core -> app -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load .env from the project root
env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=env_path)


@dataclass
class Settings:
    openweather_api_key: str


# Build a global settings instance
settings = Settings(
    openweather_api_key=os.getenv("OPENWEATHER_API_KEY", "").strip(),
)

# Fail fast with a clear error if the key is missing
if not settings.openweather_api_key:
    raise RuntimeError(
        f"OPENWEATHER_API_KEY is not set. Expected it in {env_path}"
    )