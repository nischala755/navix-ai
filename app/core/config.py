"""
Application Configuration

Centralized settings management using Pydantic Settings.
Supports environment variables and .env file configuration.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Navix-AI"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Database
    database_url: str = "sqlite+aiosqlite:///./navix.db"
    database_echo: bool = False

    # HACOPSO Hyperparameters
    hacopso_swarm_size: int = 50
    hacopso_max_iterations: int = 200
    hacopso_archive_size: int = 100
    hacopso_w_max: float = 0.9  # Max inertia weight
    hacopso_w_min: float = 0.4  # Min inertia weight
    hacopso_c1: float = 2.0  # Cognitive coefficient
    hacopso_c2: float = 2.0  # Social coefficient
    hacopso_chaos_type: Literal["logistic", "tent", "sinusoidal"] = "logistic"

    # Ocean Grid
    ocean_grid_resolution: float = 0.5  # Degrees
    ocean_grid_time_step: int = 6  # Hours

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # Seconds

    # Background Tasks
    max_concurrent_jobs: int = 5
    job_timeout_seconds: int = 300


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
