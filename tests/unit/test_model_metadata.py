from services.db.base import Base
from services.models import (
    BacktestRun,
    BacktestTrade,
    DailyBar,
    IndicatorValue,
    IngestJob,
    Instrument,
    InstrumentTag,
    ReportDaily,
    SeriesPoint,
    Strategy,
    TwDerivativesDaily,
    TwDerivativesFeature,
    Watchlist,
    WatchlistItem,
    import_models,
)


def test_model_metadata_contains_initial_tables() -> None:
    import_models()

    assert Instrument.__tablename__ == "instruments"
    assert Strategy.__tablename__ == "strategies"
    assert BacktestRun.__tablename__ == "backtest_runs"
    assert BacktestTrade.__tablename__ == "backtest_trades"
    assert DailyBar.__tablename__ == "daily_bars"
    assert IndicatorValue.__tablename__ == "indicator_values"
    assert IngestJob.__tablename__ == "ingest_jobs"
    assert InstrumentTag.__tablename__ == "instrument_tags"
    assert ReportDaily.__tablename__ == "reports_daily"
    assert SeriesPoint.__tablename__ == "series_points"
    assert TwDerivativesDaily.__tablename__ == "tw_derivatives_daily"
    assert TwDerivativesFeature.__tablename__ == "tw_derivatives_features"
    assert Watchlist.__tablename__ == "watchlists"
    assert WatchlistItem.__tablename__ == "watchlist_items"
    assert {
        "instruments",
        "strategies",
        "backtest_runs",
        "backtest_trades",
        "daily_bars",
        "indicator_values",
        "ingest_jobs",
        "instrument_tags",
        "reports_daily",
        "series_points",
        "tw_derivatives_daily",
        "tw_derivatives_features",
        "watchlists",
        "watchlist_items",
    }.issubset(Base.metadata.tables.keys())
