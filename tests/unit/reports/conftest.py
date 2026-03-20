from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.db.base import Base
from services.models import import_models
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.tw_derivatives_feature import TwDerivativesFeature
from services.models.watchlist import Watchlist
from services.models.watchlist_item import WatchlistItem


@pytest.fixture
def reporting_session() -> Generator[Session, None, None]:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def reporting_seed(reporting_session: Session) -> dict[str, object]:
    report_date = date(2024, 1, 5)
    instruments = [
        Instrument(
            symbol="2330",
            name="TSMC",
            market="TW",
            asset_type="stock",
            currency="TWD",
            timezone="Asia/Taipei",
            source_route="twse_openapi",
        ),
        Instrument(
            symbol="2317",
            name="Hon Hai",
            market="TW",
            asset_type="stock",
            currency="TWD",
            timezone="Asia/Taipei",
            source_route="twse_openapi",
        ),
        Instrument(
            symbol="2303",
            name="UMC",
            market="TW",
            asset_type="stock",
            currency="TWD",
            timezone="Asia/Taipei",
            source_route="twse_openapi",
        ),
    ]
    reporting_session.add_all(instruments)
    reporting_session.flush()

    bars = [
        DailyBar(
            instrument_id=instruments[0].id,
            trade_date=report_date,
            open=Decimal("100"),
            high=Decimal("104"),
            low=Decimal("99"),
            close=Decimal("103"),
            volume=1000,
            change_percent=Decimal("3"),
        ),
        DailyBar(
            instrument_id=instruments[1].id,
            trade_date=report_date,
            open=Decimal("200"),
            high=Decimal("202"),
            low=Decimal("196"),
            close=Decimal("197"),
            volume=800,
            change_percent=Decimal("-1.5"),
        ),
        DailyBar(
            instrument_id=instruments[2].id,
            trade_date=report_date,
            open=Decimal("50"),
            high=Decimal("51"),
            low=Decimal("49.5"),
            close=Decimal("50.5"),
            volume=1200,
            change_percent=Decimal("1"),
        ),
    ]
    reporting_session.add_all(bars)

    indicator_values = [
        IndicatorValue(
            instrument_id=instruments[0].id,
            trade_date=report_date,
            indicator_name="sma",
            component="value",
            parameter_signature="period=20",
            value=Decimal("101"),
        ),
        IndicatorValue(
            instrument_id=instruments[1].id,
            trade_date=report_date,
            indicator_name="sma",
            component="value",
            parameter_signature="period=20",
            value=Decimal("198"),
        ),
        IndicatorValue(
            instrument_id=instruments[2].id,
            trade_date=report_date,
            indicator_name="sma",
            component="value",
            parameter_signature="period=20",
            value=Decimal("49"),
        ),
        IndicatorValue(
            instrument_id=instruments[0].id,
            trade_date=report_date,
            indicator_name="rsi",
            component="value",
            parameter_signature="period=14",
            value=Decimal("60"),
        ),
        IndicatorValue(
            instrument_id=instruments[1].id,
            trade_date=report_date,
            indicator_name="rsi",
            component="value",
            parameter_signature="period=14",
            value=Decimal("45"),
        ),
        IndicatorValue(
            instrument_id=instruments[2].id,
            trade_date=report_date,
            indicator_name="rsi",
            component="value",
            parameter_signature="period=14",
            value=Decimal("55"),
        ),
    ]
    reporting_session.add_all(indicator_values)

    reporting_session.add_all(
        [
            InstrumentTag(instrument_id=instruments[0].id, tag="semiconductor"),
            InstrumentTag(instrument_id=instruments[2].id, tag="semiconductor"),
            InstrumentTag(instrument_id=instruments[1].id, tag="hardware"),
        ]
    )

    watchlist = Watchlist(name="focus", description="Core watchlist")
    laggard_watchlist = Watchlist(name="laggards", description="Weak watchlist")
    reporting_session.add_all([watchlist, laggard_watchlist])
    reporting_session.flush()
    reporting_session.add_all(
        [
            WatchlistItem(watchlist_id=watchlist.id, instrument_id=instruments[0].id),
            WatchlistItem(watchlist_id=watchlist.id, instrument_id=instruments[1].id),
            WatchlistItem(watchlist_id=laggard_watchlist.id, instrument_id=instruments[1].id),
        ]
    )

    futures_daily = TwDerivativesDaily(
        trade_date=report_date,
        market="TAIFEX",
        product_code="TX",
        product_name="TAIEX Futures",
        contract_period="202401",
        institution="foreign_investors",
        call_put=None,
        long_open_interest=1000,
        short_open_interest=800,
        net_open_interest=200,
        long_amount=Decimal("1000000"),
        short_amount=Decimal("800000"),
        net_amount=Decimal("200000"),
        source_route="taifex_open_data",
        is_options=False,
    )
    options_daily = TwDerivativesDaily(
        trade_date=report_date,
        market="TAIFEX",
        product_code="TXO",
        product_name="TAIEX Options",
        contract_period="202401",
        institution="dealers",
        call_put="call",
        long_open_interest=400,
        short_open_interest=450,
        net_open_interest=-50,
        long_amount=Decimal("200000"),
        short_amount=Decimal("240000"),
        net_amount=Decimal("-40000"),
        source_route="taifex_open_data",
        is_options=True,
    )
    reporting_session.add_all([futures_daily, options_daily])
    reporting_session.flush()

    reporting_session.add_all(
        [
            TwDerivativesFeature(
                daily_record_id=futures_daily.id,
                trade_date=report_date,
                market="TAIFEX",
                product_code="TX",
                contract_period="202401",
                institution="foreign_investors",
                call_put=None,
                delta_1d=Decimal("100"),
                delta_5d=Decimal("200"),
                delta_20d=Decimal("300"),
                zscore_20d=Decimal("1.2"),
                regime_label="bullish",
                bias_score=Decimal("1.5"),
                anomaly_flag=False,
            ),
            TwDerivativesFeature(
                daily_record_id=options_daily.id,
                trade_date=report_date,
                market="TAIFEX",
                product_code="TXO",
                contract_period="202401",
                institution="dealers",
                call_put="call",
                delta_1d=Decimal("-20"),
                delta_5d=Decimal("-50"),
                delta_20d=Decimal("-90"),
                zscore_20d=Decimal("-0.8"),
                regime_label="bearish",
                bias_score=Decimal("-0.5"),
                anomaly_flag=True,
            ),
        ]
    )

    reporting_session.commit()
    return {
        "report_date": report_date,
        "watchlist_id": watchlist.id,
        "watchlist_key": f"watchlist:{watchlist.id}",
        "laggard_watchlist_id": laggard_watchlist.id,
        "tag": "semiconductor",
    }
