from pathlib import Path

from alembic import command
from alembic.config import Config


def test_initial_migration_renders_offline_sql(capsys) -> None:
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", "postgresql+psycopg://user:pass@localhost:5432/test_db")

    command.upgrade(config, "head", sql=True)

    rendered_sql = capsys.readouterr().out
    assert "CREATE TABLE instruments" in rendered_sql
    assert "CREATE TABLE daily_bars" in rendered_sql
    assert "CREATE TABLE ingest_jobs" in rendered_sql
