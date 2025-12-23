# agent/llm_client.py

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError

# Load env so OPENAI_API_KEY and LLM_MODE are available
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODE = os.getenv("LLM_MODE", "real").lower()  # "real" or "mock"

if not OPENAI_API_KEY and LLM_MODE == "real":
  # Only require a key in real mode
  raise RuntimeError("OPENAI_API_KEY not set in environment or .env")

_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """
    Return a singleton OpenAI client (only used when LLM_MODE == 'real').
    """
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def call_llm(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = "auto",
    model: str = "gpt-4o-mini",
) -> Any:
    """
    Main entrypoint for the agent to talk to the LLM.

    - In real mode: calls OpenAI chat.completions.
    - In mock mode: returns a fake response object with a simple text answer.
    """
    # --- Mock mode: no real LLM call, just a fake reply so the flow works ---
    if LLM_MODE == "mock":
        # very small fake response object that looks like OpenAI's shape
        class FakeMessage:
            def __init__(self, content: str):
                self.content = content
                self.tool_calls = None  # no tool calls in mock mode

        class FakeChoice:
            def __init__(self, content: str):
                self.message = FakeMessage(content)

        class FakeResponse:
            def __init__(self, content: str):
                self.choices = [FakeChoice(content)]

        mock_text = (
            "Mock agent answer: in real mode I would call the weather and crypto "
            "tools and summarize the results. (LLM_MODE=mock)"
        )
        return FakeResponse(mock_text)

    # --- Real mode: call OpenAI as usual ---
    client = get_client()

    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    if tools is not None:
        kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

    try:
        return client.chat.completions.create(**kwargs)
    except RateLimitError as e:
        raise RuntimeError(
            "LLM rate limit / quota error from OpenAI: "
            "you may need to add billing or use a key with credits."
        ) from e
    except APIError as e:
        raise RuntimeError(f"LLM API error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected LLM error: {e}") from e