# agent/simple_agent.py

from typing import Any, Dict, List

from .llm_client import call_llm
from .tools_definitions import TOOLS_SCHEMA, dispatch_tool_call, parse_tool_arguments


SYSTEM_PROMPT = """
You are Agent Fetch, an AI assistant that specializes in:
- Current weather in cities
- Current cryptocurrency prices and their short-term behavior

You are connected to two tools:
- get_weather(city): returns current conditions (temperature in °C, feels_like, humidity, description, rain status, etc.).
- get_crypto_price(coin): returns the latest USD price and 24h percentage change.

GENERAL BEHAVIOR
- Your domain is only: weather and cryptocurrency markets.
- If a user asks for something outside that domain, politely say you are currently limited to weather and crypto data.
- Be clear, accurate, and concise, but still helpful and slightly explanatory.
- Do not invent numbers or current conditions. For real-time data, rely on the tools, not your own guesses.
- You can answer basic conceptual questions about weather or crypto (e.g., “what is Bitcoin?”) from general knowledge without tools.

TOOL USAGE
- Use get_weather for any question about current weather, temperature, feels-like, rain, clouds, humidity, or “is it a good day to go out” right now in a specific city.
- Use get_crypto_price for any question about current crypto price, “how is X doing today”, “is BTC calm or volatile”, or “compare BTC and ETH right now”.
- If the user mentions multiple cities, you may call get_weather once per city.
- If the user mentions multiple coins, you may call get_crypto_price once per coin.
- It is allowed to call both tools in a single answer if the question mixes weather and crypto.
- If the user’s question clearly does not require live data, you may answer without tools.

INTERPRETING USER INPUT
- Interpret common crypto tickers and names:
  - “BTC” → “bitcoin”
  - “ETH” → “ethereum”
  - “DOGE” → “dogecoin”
- For cities, use the city name the user provides.
- If the user asks about “today” or “right now”, assume they mean the current conditions returned by the tools.

COMBINING WEATHER + CRYPTO
- For “good day to go out”, use simple heuristics based on temperature, rain, extreme conditions.
- For crypto calm vs volatile, use the absolute value of 24h % change:
  - < 2% → “calm / relatively stable”
  - 2–5% → “moderate movement”
  - > 5% → “volatile / strong move”.
- If the user wants a combined recommendation (e.g., “Is it a good day to go out and does BTC seem calm?”), explicitly answer both parts.

ANSWER STYLE
- Start with a 1–2 sentence summary that directly answers the user’s main question.
- Then optionally give a short, structured breakdown (Weather: …, Crypto: …).
- Keep total length compact unless the user explicitly asks for detail.
- Do not mention internal tool names. Just refer to “the latest data”.

ERROR HANDLING
- If a tool call fails or returns an error, do not fabricate data.
- Briefly explain what went wrong and, if possible, suggest a correction.

LIMITATIONS AND SAFETY
- Do not claim certainty about future prices or weather.
- For crypto investment questions, add a short disclaimer like:
  “This is not financial advice. Please do your own research or consult a professional.”
""".strip()


def json_dumps_safe(obj: Any) -> str:
    """
    Safe JSON dumping for tool message content.
    """
    import json

    try:
        return json.dumps(obj, default=str)
    except TypeError:
        return json.dumps(str(obj))


def run_agent(user_message: str) -> str:
    """
    Stateless agent:
    - Sends system + user messages to LLM with tool definitions.
    - If tools are requested, executes them and sends results back.
    - Returns the final assistant answer text.
    """
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    # 1) First call: let the model decide whether to call tools
    first_response = call_llm(
        messages=messages,
        tools=TOOLS_SCHEMA,
        tool_choice="auto",
    )

    first_msg = first_response.choices[0].message

    # If the model responds directly without tool calls
    if not getattr(first_msg, "tool_calls", None):
        return first_msg.content or ""

    # 2) We have tool calls to execute
    messages.append(
        {
            "role": "assistant",
            "content": first_msg.content or "",
            "tool_calls": [tc.model_dump() for tc in first_msg.tool_calls],
        }
    )

    tool_messages: List[Dict[str, Any]] = []

    for tool_call in first_msg.tool_calls:
        tool_name = tool_call.function.name
        raw_args = tool_call.function.arguments or "{}"
        args = parse_tool_arguments(raw_args)
        tool_result = dispatch_tool_call(tool_name, args)

        tool_messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json_dumps_safe(tool_result),
            }
        )

    messages.extend(tool_messages)

    # 3) Second call: ask for final answer (no more tools)
    second_response = call_llm(
        messages=messages,
        tools=None,
        tool_choice=None,
    )

    second_msg = second_response.choices[0].message
    return second_msg.content or ""