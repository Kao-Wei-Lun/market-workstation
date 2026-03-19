from services.db.base import Base
from services.models import DailyBar, IngestJob, Instrument, SeriesPoint, import_models


def test_model_metadata_contains_initial_tables() -> None:
    import_models()

    assert Instrument.__tablename__ == "instruments"
    assert DailyBar.__tablename__ == "daily_bars"
    assert IngestJob.__tablename__ == "ingest_jobs"
    assert SeriesPoint.__tablename__ == "series_points"
    assert {"instruments", "daily_bars", "ingest_jobs", "series_points"}.issubset(
        Base.metadata.tables.keys()
    )
