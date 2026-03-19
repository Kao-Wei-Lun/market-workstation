from config.settings import Settings, get_settings


def test_settings_build_database_uri_from_environment_fields() -> None:
    get_settings.cache_clear()

    settings = Settings(
        postgres_host="postgres.internal",
        postgres_port=5433,
        postgres_db="market_data",
        postgres_user="tester",
        postgres_password="secret",
    )

    assert settings.sqlalchemy_database_uri == (
        "postgresql+psycopg://tester:secret@postgres.internal:5433/market_data"
    )


def test_settings_prefer_explicit_database_url() -> None:
    get_settings.cache_clear()

    settings = Settings(database_url="postgresql+psycopg://user:pass@db:5432/custom")

    assert settings.sqlalchemy_database_uri == "postgresql+psycopg://user:pass@db:5432/custom"
