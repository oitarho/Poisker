from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POISKER_", env_file=".env", extra="ignore")

    env: str = Field(default="local", description="Environment name: local/staging/prod")
    log_level: str = Field(default="INFO", description="Log level")

    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    # Keep as string so pydantic-settings doesn't JSON-decode it as a complex type.
    # Format: comma-separated origins.
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:8080,http://localhost:3000,http://127.0.0.1:8080",
        description="Allowed CORS origins (comma-separated)",
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

    # SMTP (email verification / password reset)
    smtp_enabled: bool = Field(default=False, description="If false, outbound email is skipped (log only)")
    smtp_host: str = Field(default="smtp.yandex.ru")
    smtp_port: int = Field(default=465)
    smtp_username: str = Field(default="")
    smtp_password: str = Field(default="")
    smtp_from_email: str = Field(default="noreply@example.com")
    smtp_from_name: str = Field(default="Poisker")
    smtp_use_tls: bool = Field(
        default=True,
        description="For port 587: use STARTTLS. For 465, implicit SSL is used regardless.",
    )

    # Email / reset codes (Redis-backed)
    code_pepper: str = Field(
        default="",
        description="Extra secret for hashing codes; defaults to jwt_secret if empty",
    )
    code_ttl_seconds: int = Field(default=600, description="Verification/reset code lifetime (10 min)")
    code_resend_cooldown_seconds: int = Field(default=60, description="Min seconds between sends per email")
    code_max_sends_per_hour: int = Field(default=5, description="Max verification/reset emails per hour per email")
    code_max_failed_attempts: int = Field(default=5, description="Invalidate code after this many wrong attempts")

    @field_validator("upload_allowed_image_types", mode="before")
    @classmethod
    def _parse_csv_list(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    @property
    def code_pepper_effective(self) -> str:
        return self.code_pepper or self.jwt_secret


settings = Settings()
