from pathlib import Path

from alembic import command
from alembic.config import Config


def test_initial_migration_renders_offline_sql(capsys) -> None:
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", "postgresql+psycopg://user:pass@localhost:5432/test_db")

    command.upgrade(config, "head", sql=True)

    rendered_sql = capsys.readouterr().out
    assert "CREATE TABLE instruments" in rendered_sql
    assert "CREATE TABLE auto_classification_rules" in rendered_sql
    assert "CREATE TABLE candidate_runs" in rendered_sql
    assert "CREATE TABLE candidate_items" in rendered_sql
    assert "CREATE TABLE chart_annotations" in rendered_sql
    assert "CREATE TABLE strategies" in rendered_sql
    assert "CREATE TABLE backtest_runs" in rendered_sql
    assert "CREATE TABLE backtest_search_runs" in rendered_sql
    assert "CREATE TABLE backtest_search_results" in rendered_sql
    assert "CREATE TABLE backtest_trades" in rendered_sql
    assert "CREATE TABLE backtest_walk_forward_runs" in rendered_sql
    assert "CREATE TABLE backtest_walk_forward_windows" in rendered_sql
    assert "CREATE TABLE daily_bars" in rendered_sql
    assert "CREATE TABLE instrument_tags" in rendered_sql
    assert "CREATE TABLE ingest_jobs" in rendered_sql
    assert "CREATE TABLE indicator_values" in rendered_sql
    assert "CREATE TABLE series_points" in rendered_sql
    assert "CREATE TABLE reports_daily" in rendered_sql
    assert "CREATE TABLE tw_derivatives_daily" in rendered_sql
    assert "CREATE TABLE tw_derivatives_features" in rendered_sql
    assert "CREATE TABLE tw_institutional_spot_daily" in rendered_sql
    assert "CREATE TABLE watchlists" in rendered_sql
    assert "CREATE TABLE watchlist_items" in rendered_sql
    assert "CREATE TABLE worker_health" in rendered_sql
