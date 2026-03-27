"""Configurazione applicativa con Pydantic BaseSettings.

Carica da variabili d'ambiente e file .env.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Impostazioni globali TitoliEngine."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TE_",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://titoliengine:titoliengine_dev@localhost:5432/titoliengine"
    )
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── App ───────────────────────────────────────────────────
    app_name: str = "TitoliEngine"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # ── CORS ──────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000"]

    # ── Logging ───────────────────────────────────────────────
    log_level: str = "INFO"


settings = Settings()
