# agent/tools_definitions.py

import json
from typing import Any, Dict, List

from tools import get_weather, get_crypto_price, WeatherAPIError, CryptoAPIError


# --- Tool JSON Schemas for LLM ---

TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather conditions for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city (e.g. 'Hyderabad', 'London').",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_crypto_price",
            "description": "Get the latest price and 24h change for a cryptocurrency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coin": {
                        "type": "string",
                        "description": (
                            "Coin id as used by your API backend, e.g. 'bitcoin', 'ethereum', 'dogecoin'."
                        ),
                    }
                },
                "required": ["coin"],
            },
        },
    },
]


# --- Python dispatcher ---

def dispatch_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map LLM tool name + arguments to the real Python function.

    Returns a dict that is JSON-serializable, suitable to feed back into the LLM.
    """
    try:
        if name == "get_weather":
            city = arguments.get("city")
            if not city:
                raise ValueError("Missing required argument: city")
            result = get_weather(city=city)
            return {"ok": True, "tool": name, "args": {"city": city}, "result": result}

        elif name == "get_crypto_price":
            coin = arguments.get("coin")
            if not coin:
                raise ValueError("Missing required argument: coin")
            result = get_crypto_price(coin=coin)
            return {"ok": True, "tool": name, "args": {"coin": coin}, "result": result}

        else:
            # Unknown tool name (shouldn't happen if schema and LLM are aligned)
            return {
                "ok": False,
                "tool": name,
                "error": f"Unknown tool: {name}",
            }

    except WeatherAPIError as e:
        return {
            "ok": False,
            "tool": name,
            "error_type": "WeatherAPIError",
            "error": str(e),
        }
    except CryptoAPIError as e:
        return {
            "ok": False,
            "tool": name,
            "error_type": "CryptoAPIError",
            "error": str(e),
        }
    except Exception as e:
        # Catch-all so LLM can explain failures gracefully
        return {
            "ok": False,
            "tool": name,
            "error_type": "InternalError",
            "error": str(e),
        }


def parse_tool_arguments(raw_args: str) -> Dict[str, Any]:
    """
    OpenAI sends tool.function.arguments as a JSON string; parse safely.
    """
    try:
        return json.loads(raw_args) if raw_args else {}
    except json.JSONDecodeError:
        return {}