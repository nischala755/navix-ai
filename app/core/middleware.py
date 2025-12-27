"""
Application Middleware

Rate limiting, CORS, and request processing middleware.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings


def get_limiter() -> Limiter:
    """Create rate limiter instance."""
    return Limiter(key_func=get_remote_address)


limiter = get_limiter()


def setup_middleware(app: FastAPI) -> None:
    """
    Configure application middleware.
    
    Args:
        app: FastAPI application instance.
    """
    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["https://navix-ai.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next) -> Response:
        """Add processing time to response headers."""
        import time

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        return response
