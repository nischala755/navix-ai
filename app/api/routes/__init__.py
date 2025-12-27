"""API routes package."""

from fastapi import APIRouter

from app.api.routes import optimize, jobs, routes, explain, benchmark, maps

api_router = APIRouter()

api_router.include_router(optimize.router, tags=["Optimization"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(routes.router, prefix="/routes", tags=["Routes"])
api_router.include_router(explain.router, prefix="/explain", tags=["Explainability"])
api_router.include_router(benchmark.router, prefix="/benchmark", tags=["Benchmark"])
api_router.include_router(maps.router, prefix="/map", tags=["Map Layers"])
