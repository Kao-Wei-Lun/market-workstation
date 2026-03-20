from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.indicators.adx import ADXIndicator
from services.core.indicators.donchian import DonchianChannelIndicator
from services.core.indicators.ichimoku import IchimokuIndicator
from services.core.indicators.keltner import KeltnerChannelIndicator
from services.core.indicators.parabolic_sar import ParabolicSARIndicator
from services.core.indicators.service import compute_and_persist_indicators, query_indicator_values
from services.core.indicators.stochastic import StochasticIndicator
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


def test_batch_two_indicator_persistence_supports_multi_output_queries() -> None:
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
    for index in range(90):
        close = Decimal("100") + Decimal(index) + (Decimal(index % 4) / Decimal("4"))
        session.add(
            DailyBar(
                instrument_id=instrument.id,
                trade_date=date(2024, 1, 1) + timedelta(days=index),
                open=close - Decimal("1"),
                high=close + Decimal("2"),
                low=close - Decimal("2"),
                close=close,
                volume=1_000 + (index * 20),
            )
        )
    session.flush()

    persisted_count = compute_and_persist_indicators(
        session,
        instrument_id=instrument.id,
        calculators=[
            ADXIndicator(14),
            StochasticIndicator(14, 3),
            IchimokuIndicator(),
            KeltnerChannelIndicator(),
            DonchianChannelIndicator(20),
            ParabolicSARIndicator(),
        ],
    )

    assert persisted_count == session.query(IndicatorValue).count()
    stochastic_values = query_indicator_values(
        session,
        instrument_id=instrument.id,
        indicator_name="stochastic",
        component="percent_d",
        parameter_signature="k_period=14,d_period=3",
    )
    ichimoku_values = query_indicator_values(
        session,
        instrument_id=instrument.id,
        indicator_name="ichimoku",
        component="leading_span_a",
        parameter_signature="conversion_period=9,base_period=26,span_b_period=52",
    )

    assert stochastic_values
    assert ichimoku_values
    assert any(row.indicator_name == "adx" and row.component == "adx" for row in session.query(IndicatorValue).all())
