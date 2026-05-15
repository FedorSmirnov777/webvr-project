from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", BASE_DIR / "api" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="dev", alias="APP_ENV")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60 * 8, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    database_url: str = Field(
        default=f"sqlite:///{(BASE_DIR / 'data' / 'autovr_fastapi.sqlite3').as_posix()}",
        alias="DATABASE_URL",
    )

    cors_origins: list[str] = Field(default=["http://localhost", "http://127.0.0.1:8000"], alias="CORS_ORIGINS")

    uploads_dir: str = Field(default=str(BASE_DIR / "assets" / "uploads"), alias="UPLOADS_DIR")
    public_assets_prefix: str = Field(default="/assets/uploads", alias="PUBLIC_ASSETS_PREFIX")

    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    sentry_traces_sample_rate: float = Field(default=0.2, alias="SENTRY_TRACES_SAMPLE_RATE")

    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")

    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: str | None = Field(default=None, alias="SMTP_FROM_EMAIL")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")


settings = Settings()
