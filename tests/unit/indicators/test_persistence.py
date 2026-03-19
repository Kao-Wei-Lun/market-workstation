from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.indicators.ema import EMAIndicator
from services.core.indicators.service import compute_and_persist_indicators, query_indicator_values
from services.core.indicators.sma import SMAIndicator
from services.db.base import Base
from services.models import import_models
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_indicator_persistence_flow_stores_indicator_values() -> None:
    session = _build_session()
    instrument = Instrument(
        symbol="2330",
        name="TSMC",
        market="TW",
        asset_type="stock",
        currency="TWD",
        timezone="Asia/Taipei",
        source_route="twse_openapi",
    )
    session.add(instrument)
    session.flush()
    for index, close in enumerate([10, 11, 12, 13, 14, 15]):
        session.add(
            DailyBar(
                instrument_id=instrument.id,
                trade_date=date(2024, 1, 1) + timedelta(days=index),
                open=Decimal(str(close)),
                high=Decimal(str(close)),
                low=Decimal(str(close)),
                close=Decimal(str(close)),
                volume=1000,
            )
        )
    session.flush()

    persisted_count = compute_and_persist_indicators(
        session,
        instrument_id=instrument.id,
        calculators=[SMAIndicator(period=3), EMAIndicator(period=3)],
    )

    stored_rows = session.query(IndicatorValue).all()
    queried = query_indicator_values(session, instrument_id=instrument.id, indicator_name="sma")

    assert persisted_count == len(stored_rows)
    assert len(stored_rows) == 8
    assert len(queried) == 4
