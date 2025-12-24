# app/main.py
"""
FastAPI application entrypoint.

Run with:
  uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import crypto, weather, agent, history, schedules # <-- added agent import
from app.services.schedules import start_scheduler_loop 

# Create FastAPI app instance
app = FastAPI(
    title="Agentic Weather & Crypto API",
    version="0.1.0",
    description="Backend for weather & crypto dashboard, future-ready for agentic AI.",
)

# CORS so the React frontend (different port) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins for now (dev/demo)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers under /api prefix
app.include_router(weather.router, prefix="/api")
app.include_router(crypto.router, prefix="/api")
app.include_router(agent.router, prefix="/api")  # <-- include agent router
app.include_router(history.router, prefix="/api")  # <-- new
app.include_router(schedules.router, prefix="/api") 


@app.on_event("startup")
async def on_startup() -> None:
    # Start in-memory scheduler loop for Phase 3 schedules
    start_scheduler_loop()


@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}