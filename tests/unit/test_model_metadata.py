from services.db.base import Base
from services.models import (
    AutoClassificationRule,
    BacktestRun,
    BacktestSearchResult,
    BacktestSearchRun,
    BacktestTrade,
    BacktestWalkForwardRun,
    BacktestWalkForwardWindow,
    CandidateItem,
    CandidateRun,
    ChartAnnotation,
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
    TwInstitutionalSpotDaily,
    Watchlist,
    WatchlistItem,
    WorkerHealth,
    import_models,
)


def test_model_metadata_contains_initial_tables() -> None:
    import_models()

    assert Instrument.__tablename__ == "instruments"
    assert AutoClassificationRule.__tablename__ == "auto_classification_rules"
    assert CandidateRun.__tablename__ == "candidate_runs"
    assert CandidateItem.__tablename__ == "candidate_items"
    assert ChartAnnotation.__tablename__ == "chart_annotations"
    assert Strategy.__tablename__ == "strategies"
    assert BacktestRun.__tablename__ == "backtest_runs"
    assert BacktestSearchRun.__tablename__ == "backtest_search_runs"
    assert BacktestSearchResult.__tablename__ == "backtest_search_results"
    assert BacktestTrade.__tablename__ == "backtest_trades"
    assert BacktestWalkForwardRun.__tablename__ == "backtest_walk_forward_runs"
    assert BacktestWalkForwardWindow.__tablename__ == "backtest_walk_forward_windows"
    assert DailyBar.__tablename__ == "daily_bars"
    assert IndicatorValue.__tablename__ == "indicator_values"
    assert IngestJob.__tablename__ == "ingest_jobs"
    assert InstrumentTag.__tablename__ == "instrument_tags"
    assert ReportDaily.__tablename__ == "reports_daily"
    assert SeriesPoint.__tablename__ == "series_points"
    assert TwDerivativesDaily.__tablename__ == "tw_derivatives_daily"
    assert TwDerivativesFeature.__tablename__ == "tw_derivatives_features"
    assert TwInstitutionalSpotDaily.__tablename__ == "tw_institutional_spot_daily"
    assert Watchlist.__tablename__ == "watchlists"
    assert WatchlistItem.__tablename__ == "watchlist_items"
    assert WorkerHealth.__tablename__ == "worker_health"
    assert {
        "instruments",
        "auto_classification_rules",
        "candidate_runs",
        "candidate_items",
        "chart_annotations",
        "strategies",
        "backtest_runs",
        "backtest_search_runs",
        "backtest_search_results",
        "backtest_trades",
        "backtest_walk_forward_runs",
        "backtest_walk_forward_windows",
        "daily_bars",
        "indicator_values",
        "ingest_jobs",
        "instrument_tags",
        "reports_daily",
        "series_points",
        "tw_derivatives_daily",
        "tw_derivatives_features",
        "tw_institutional_spot_daily",
        "watchlists",
        "watchlist_items",
        "worker_health",
    }.issubset(Base.metadata.tables.keys())
