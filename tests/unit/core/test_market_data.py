from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.bootstrap import seed_sample_reference_data
from services.core.market_data import has_any_daily_bars, run_real_twse_backfill
from services.connectors.twse import TwseDailyMarketDataConnector
from services.db.base import Base
from services.models import import_models
from services.models.daily_bar import DailyBar
from services.models.instrument import Instrument
from services.schemas.etl import NormalizedDataBatch, NormalizedDailyBarRecord


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


class _FakeTwseConnector(TwseDailyMarketDataConnector):

    def fetch(self, request):
        return type("FetchResult", (), {"payload": {"data": [{"trade_date": request.trade_date.isoformat()}]}})

    def normalize(self, payload, request):
        trade_date = request.trade_date
        assert trade_date is not None
        assert request.symbol is not None
        return NormalizedDataBatch(
            daily_bars=[
                NormalizedDailyBarRecord(
                    instrument_id=request.instrument_id,
                    symbol=request.symbol,
                    market="TW",
                    currency="TWD",
                    source_route=request.source_route or self.source_route,
                    trade_date=trade_date,
                    open=Decimal("100"),
                    high=Decimal("102"),
                    low=Decimal("99"),
                    close=Decimal("101"),
                    volume=1000,
                    change=Decimal("1"),
                    change_percent=Decimal("1.0"),
                )
            ]
        )


def test_run_real_twse_backfill_loads_weekdays_only() -> None:
    session = _build_session()
    seed_sample_reference_data(session)

    result = run_real_twse_backfill(
        session,
        symbols=("2330",),
        start_date=date(2026, 3, 13),
        end_date=date(2026, 3, 17),
        connector=_FakeTwseConnector(),
    )

    instrument = session.query(Instrument).filter(Instrument.symbol == "2330").one()
    assert result.instruments_processed == 1
    assert result.trading_days_processed == 3
    assert result.daily_bars_loaded == 3
    assert session.query(DailyBar).filter(DailyBar.instrument_id == instrument.id).count() == 3


def test_has_any_daily_bars_detects_existing_range() -> None:
    session = _build_session()
    seed_sample_reference_data(session)
    instrument = session.query(Instrument).filter(Instrument.symbol == "2330").one()
    session.add(
        DailyBar(
            instrument_id=instrument.id,
            trade_date=date(2026, 3, 20),
            open=Decimal("100"),
            high=Decimal("102"),
            low=Decimal("99"),
            close=Decimal("101"),
            volume=1000,
        )
    )
    session.commit()

    assert has_any_daily_bars(
        session,
        instrument_id=instrument.id,
        start_date=date(2026, 3, 19),
        end_date=date(2026, 3, 20),
    )
