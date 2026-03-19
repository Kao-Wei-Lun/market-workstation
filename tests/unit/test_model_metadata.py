from services.db.base import Base
from services.models import (
    DailyBar,
    IngestJob,
    Instrument,
    SeriesPoint,
    TwDerivativesDaily,
    TwDerivativesFeature,
    import_models,
)


def test_model_metadata_contains_initial_tables() -> None:
    import_models()

    assert Instrument.__tablename__ == "instruments"
    assert DailyBar.__tablename__ == "daily_bars"
    assert IngestJob.__tablename__ == "ingest_jobs"
    assert SeriesPoint.__tablename__ == "series_points"
    assert TwDerivativesDaily.__tablename__ == "tw_derivatives_daily"
    assert TwDerivativesFeature.__tablename__ == "tw_derivatives_features"
    assert {
        "instruments",
        "daily_bars",
        "ingest_jobs",
        "series_points",
        "tw_derivatives_daily",
        "tw_derivatives_features",
    }.issubset(Base.metadata.tables.keys())
