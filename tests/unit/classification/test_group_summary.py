from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.classification.summary import summarize_tag_group, summarize_watchlist_group
from services.core.classification.tags import add_tag_to_instrument
from services.core.classification.watchlists import add_instrument_to_watchlist, create_watchlist
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


def test_group_summary_uses_tags_watchlists_bars_and_indicators() -> None:
    session = _build_session()
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
    session.add_all(instruments)
    session.flush()
    for instrument, change_pct, close, sma in [
        (instruments[0], Decimal("2.5"), Decimal("102"), Decimal("100")),
        (instruments[1], Decimal("-1.0"), Decimal("99"), Decimal("100")),
        (instruments[2], Decimal("5.0"), Decimal("105"), Decimal("100")),
    ]:
        add_tag_to_instrument(session, instrument_id=instrument.id, tag="semiconductor")
        session.add(
            DailyBar(
                instrument_id=instrument.id,
                trade_date=date(2024, 1, 5),
                open=Decimal("100"),
                high=close,
                low=Decimal("99"),
                close=close,
                volume=1000,
                change_percent=change_pct,
            )
        )
        session.add(
            IndicatorValue(
                instrument_id=instrument.id,
                trade_date=date(2024, 1, 5),
                indicator_name="sma",
                component="value",
                parameter_signature="period=20",
                value=sma,
            )
        )
    watchlist = create_watchlist(session, name="chips")
    add_instrument_to_watchlist(session, watchlist_id=watchlist.id, instrument_id=instruments[0].id)
    add_instrument_to_watchlist(session, watchlist_id=watchlist.id, instrument_id=instruments[1].id)
    add_instrument_to_watchlist(session, watchlist_id=watchlist.id, instrument_id=instruments[2].id)
    session.flush()

    tag_summary = summarize_tag_group(session, tag="semiconductor", trade_date=date(2024, 1, 5))
    watchlist_summary = summarize_watchlist_group(session, watchlist_id=watchlist.id, trade_date=date(2024, 1, 5))

    assert tag_summary.member_count == 3
    assert tag_summary.average_close_change_pct == Decimal("2.166667")
    assert tag_summary.top_gainers[0].symbol == "2303"
    assert tag_summary.top_losers[0].symbol == "2317"
    assert tag_summary.percentage_above_sma == Decimal("66.666667")
    assert watchlist_summary.member_count == 3
