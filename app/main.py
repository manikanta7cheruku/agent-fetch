# app/main.py
"""
FastAPI application entrypoint.

Run with:
  poetry run uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import crypto, weather

# Create FastAPI app instance
app = FastAPI(
    title="Agentic Weather & Crypto API",
    version="0.1.0",
    description="Backend for weather & crypto dashboard, future-ready for agentic AI.",
)

# CORS (Cross-Origin Resource Sharing) so the React frontend (different port) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers under /api prefix
app.include_router(weather.router, prefix="/api")
app.include_router(crypto.router, prefix="/api")


@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}









# 7.5. Run backend & test with Postman
# From project root, inside poetry shell:

# Bash

# poetry run uvicorn app.main:app --reload
# Backend is now at http://localhost:8000.

# Test in Postman or browser:

# GET http://localhost:8000/health
# GET http://localhost:8000/api/weather?city=Hyderabad
# GET http://localhost:8000/api/crypto?coin=bitcoin
# You should see JSON responses and files being written to data/.