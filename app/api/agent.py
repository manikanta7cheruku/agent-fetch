# app/api/agent.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent.simple_agent import run_agent

# This will become /api/agent/... because we include it with prefix="/api" in main.py
router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """
    Stateless chat endpoint:
    - Takes a natural language message,
    - Runs the LLM + tools agent,
    - Returns the final answer.
    """
    try:
        answer = run_agent(payload.message)
        return ChatResponse(answer=answer)
    except RuntimeError as e:
        # LLM / tools errors (quota, API issues, etc.) → 502 Bad Gateway with clear detail
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        # Any unexpected internal error
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")