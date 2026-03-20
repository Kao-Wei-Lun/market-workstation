from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.classification.scanner import scan_tag_group, scan_watchlist_group
from services.core.classification.tags import add_tag_to_instrument
from services.core.classification.watchlists import add_instrument_to_watchlist, create_watchlist
from services.db.base import Base
from services.models import import_models
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.schemas.classification import GroupScannerFlagConditions


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_group_scanner_computes_volume_ratio_sma_and_flags() -> None:
    session = _build_session()
    trade_date = date(2024, 1, 5)
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
    ]
    session.add_all(instruments)
    session.flush()

    for instrument in instruments:
        add_tag_to_instrument(session, instrument_id=instrument.id, tag="semiconductor")
        for offset in range(1, 4):
            session.add(
                DailyBar(
                    instrument_id=instrument.id,
                    trade_date=trade_date - timedelta(days=offset),
                    open=Decimal("100"),
                    high=Decimal("101"),
                    low=Decimal("99"),
                    close=Decimal("100"),
                    volume=1_000,
                    change_percent=Decimal("0"),
                )
            )

    session.add_all(
        [
            DailyBar(
                instrument_id=instruments[0].id,
                trade_date=trade_date,
                open=Decimal("100"),
                high=Decimal("104"),
                low=Decimal("99"),
                close=Decimal("103"),
                volume=2_000,
                change_percent=Decimal("3"),
            ),
            DailyBar(
                instrument_id=instruments[1].id,
                trade_date=trade_date,
                open=Decimal("100"),
                high=Decimal("100"),
                low=Decimal("97"),
                close=Decimal("98"),
                volume=900,
                change_percent=Decimal("-2"),
            ),
            IndicatorValue(
                instrument_id=instruments[0].id,
                trade_date=trade_date,
                indicator_name="sma",
                component="value",
                parameter_signature="period=20",
                value=Decimal("101"),
            ),
            IndicatorValue(
                instrument_id=instruments[1].id,
                trade_date=trade_date,
                indicator_name="sma",
                component="value",
                parameter_signature="period=20",
                value=Decimal("100"),
            ),
        ]
    )
    watchlist = create_watchlist(session, name="chips")
    for instrument in instruments:
        add_instrument_to_watchlist(session, watchlist_id=watchlist.id, instrument_id=instrument.id)
    session.flush()

    scan_result = scan_tag_group(
        session,
        tag="semiconductor",
        trade_date=trade_date,
        volume_lookback_days=3,
        flag_conditions=GroupScannerFlagConditions(
            min_close_change_pct=Decimal("2"),
            min_volume_ratio=Decimal("1.5"),
            require_above_sma=True,
            match_mode="all",
        ),
    )
    watchlist_result = scan_watchlist_group(
        session,
        watchlist_id=watchlist.id,
        trade_date=trade_date,
        volume_lookback_days=3,
    )

    assert scan_result.member_count == 2
    assert scan_result.average_daily_return_pct == Decimal("0.500000")
    assert scan_result.average_volume_ratio == Decimal("1.450000")
    assert scan_result.percentage_above_sma == Decimal("50.000000")
    assert scan_result.top_gainers[0].symbol == "2330"
    assert scan_result.top_losers[0].symbol == "2317"
    assert [item.symbol for item in scan_result.flagged_instruments] == ["2330"]
    assert scan_result.flagged_instruments[0].reasons == [
        "close_change_pct>=2",
        "volume_ratio>=1.5",
        "above_sma",
    ]
    assert watchlist_result.member_count == 2
