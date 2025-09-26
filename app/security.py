"""Security middleware and rate limiting."""

import os
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]


def setup_security(app: FastAPI) -> None:
    """Configure security middleware for the FastAPI app."""
    
    # CORS with restricted origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )


def get_rate_limits() -> dict:
    """Get rate limit configuration."""
    return {
        "correction": "10/minute",  # 10 corrections per minute per IP
        "export": "5/minute",       # 5 exports per minute per IP
        "stats": "30/minute",       # 30 stats requests per minute per IP
    }
