# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Event Around API"
    app_env: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    postgres_user: str = "event_user"
    postgres_password: str = "event_pass"
    postgres_db: str = "event_around_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    database_url: str = "postgresql+psycopg://event_user:event_pass@localhost:5432/event_around_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()