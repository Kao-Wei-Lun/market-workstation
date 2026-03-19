from __future__ import annotations

from pathlib import Path

from config.settings import Settings


def test_settings_can_load_from_env_example_file(tmp_path: Path) -> None:
    env_example = tmp_path / ".env.example"
    env_example.write_text(
        "\n".join(
            [
                "APP_NAME=from-example",
                "POSTGRES_HOST=localhost",
                "POSTGRES_PORT=5432",
                "POSTGRES_DB=example_db",
                "POSTGRES_USER=example_user",
                "POSTGRES_PASSWORD=example_pass",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(**{"_env_file": (tmp_path / ".env", env_example)})  # type: ignore[arg-type]

    assert settings.app_name == "from-example"
    assert settings.sqlalchemy_database_uri == "postgresql+psycopg://example_user:example_pass@localhost:5432/example_db"
