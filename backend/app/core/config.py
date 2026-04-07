from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POISKER_", env_file=".env", extra="ignore")

    env: str = Field(default="local", description="Environment name: local/staging/prod")
    log_level: str = Field(default="INFO", description="Log level")

    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:8080",
            "http://localhost:3000",
            "http://127.0.0.1:8080",
        ],
        description="Allowed CORS origins",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://poisker:poisker@localhost:5432/poisker",
        description="Async SQLAlchemy database URL",
    )
    db_echo: bool = Field(default=False, description="SQLAlchemy echo")

    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    typesense_host: str = Field(default="localhost")
    typesense_port: int = Field(default=8108)
    typesense_protocol: str = Field(default="http")
    typesense_api_key: str = Field(default="xyz")
    typesense_listings_collection: str = Field(default="poisker_listings")

    jwt_issuer: str = Field(default="poisker")
    jwt_audience: str = Field(default="poisker")
    jwt_secret: str = Field(default="dev-change-me")
    jwt_access_ttl_seconds: int = Field(default=900)
    jwt_refresh_ttl_seconds: int = Field(default=60 * 60 * 24 * 14)  # 14 days

    # Media (local dev)
    media_dir: str = Field(default="var/media", description="Local media directory")
    media_public_base: str = Field(default="/media", description="Public media base path")
    upload_max_bytes: int = Field(default=5 * 1024 * 1024, description="Max upload size in bytes")
    upload_allowed_image_types: list[str] = Field(
        default_factory=lambda: ["image/jpeg", "image/png", "image/webp"],
        description="Allowed image MIME types",
    )

    # Admin/moderation foundation (token-based for now)
    admin_token: str | None = Field(
        default=None,
        description="If set, required in X-Admin-Token header for admin endpoints",
    )

    @field_validator("upload_allowed_image_types", mode="before")
    @classmethod
    def _parse_csv_list(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


settings = Settings()
