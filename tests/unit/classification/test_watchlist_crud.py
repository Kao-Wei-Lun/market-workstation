from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.classification.watchlists import (
    add_instrument_to_watchlist,
    create_watchlist,
    list_watchlist_items,
    remove_instrument_from_watchlist,
)
from services.db.base import Base
from services.models import import_models
from services.models.instrument import Instrument


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_watchlist_crud_round_trip() -> None:
    session = _build_session()
    instrument = Instrument(
        symbol="AAPL",
        name="Apple",
        market="US",
        asset_type="stock",
        currency="USD",
        timezone="America/New_York",
        source_route="us_eod_provider",
    )
    session.add(instrument)
    session.flush()

    watchlist = create_watchlist(session, name="core", description="core holdings")
    add_instrument_to_watchlist(session, watchlist_id=watchlist.id, instrument_id=instrument.id)
    items = list_watchlist_items(session, watchlist_id=watchlist.id)
    removed = remove_instrument_from_watchlist(session, watchlist_id=watchlist.id, instrument_id=instrument.id)

    assert watchlist.name == "core"
    assert len(items) == 1
    assert items[0].instrument_id == instrument.id
    assert removed is True
