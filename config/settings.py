from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "market-workstation"
    app_env: str = "development"
    app_version: str = "0.1.0"
    debug: bool = False

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "market_workstation"
    postgres_user: str = "market_user"
    postgres_password: str = "change_me"
    database_url: str | None = None

    us_eod_provider: str = "demo"
    us_eod_base_url: str | None = None
    us_eod_api_key: str | None = None

    macro_provider: str = "demo"
    macro_base_url: str | None = None
    macro_api_key: str | None = None

    scheduler_timezone: str = "Asia/Taipei"
    scheduler_daily_market_etl_cron: str = "0 18 * * 1-5"
    scheduler_indicator_update_cron: str = "30 18 * * 1-5"
    scheduler_taiwan_derivatives_pipeline_cron: str = "40 18 * * 1-5"
    scheduler_daily_report_generation_cron: str = "0 19 * * 1-5"
    worker_heartbeat_interval_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.example"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
