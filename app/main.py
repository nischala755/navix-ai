"""
Navix-AI: HACOPSO-Powered Maritime Route Optimization

Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.middleware import setup_middleware
from app.api.routes import api_router
from app.schemas.common import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="""
## Navix-AI Maritime Route Optimization API

A production-grade backend for carbon-aware maritime routing using 
**Hybrid Adaptive Chaotic Opposition-Based Particle Swarm Optimization (HACOPSO)**.

### Features

- **Multi-Objective Optimization**: Balance fuel, time, risk, emissions, and comfort
- **HACOPSO Engine**: Research-grade swarm optimization with chaotic inertia and opposition-based learning
- **Digital Ocean Twin**: Time-varying wave, current, storm, and piracy data
- **Explainable AI**: Understand why specific routes were chosen
- **Warm-Start Optimization**: Learn from historical routes for faster convergence

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /optimize` | Submit route optimization job |
| `GET /jobs/{id}` | Check job status |
| `GET /routes/{id}` | Get Pareto-optimal routes |
| `GET /explain/{id}` | Get route explanation |
| `GET /benchmark` | Compare HACOPSO vs GA |
| `GET /map/layers` | Get ocean data layers |
""",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Setup middleware
setup_middleware(app)

# Include API routes
app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root():
    """Root redirect to docs."""
    return {"message": "Navix-AI API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.debug else None,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers,
    )
