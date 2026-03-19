from __future__ import annotations

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.bootstrap import run_sample_daily_market_etl, seed_sample_reference_data
from services.db.base import Base
from services.models import import_models
from services.models.daily_bar import DailyBar
from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.models.watchlist import Watchlist
from services.models.watchlist_item import WatchlistItem


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_seed_sample_reference_data_is_idempotent() -> None:
    session = _build_session()

    first = seed_sample_reference_data(session)
    second = seed_sample_reference_data(session)

    assert first.instruments_created == 3
    assert second.instruments_created == 0
    assert session.query(Instrument).count() == 3
    assert session.query(Watchlist).count() == 1
    assert session.query(WatchlistItem).count() == 2
    assert session.query(InstrumentTag).count() == 5


def test_sample_etl_loads_seeded_daily_bars() -> None:
    session = _build_session()

    result = run_sample_daily_market_etl(session, trade_date=date(2024, 1, 31))

    assert result.instruments_processed == 2
    assert result.daily_bars_loaded == 60
    assert session.query(DailyBar).count() == 60
