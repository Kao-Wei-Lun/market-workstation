from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import cast

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.backtesting.service import create_and_run_backtest
from services.core.candidates.service import generate_and_persist_candidate_run
from services.core.dashboard import (
    build_backtests_dashboard,
    build_candidates_dashboard,
    build_dashboard_overview,
    build_derivatives_dashboard,
    build_group_dashboard,
    build_reports_dashboard,
    build_watchlist_dashboard,
)
from services.core.reports.bundle import generate_daily_report_bundle
from services.core.reports.generators import generate_market_summary_report
from services.core.reports.service import persist_generated_report
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
from services.schemas.backtesting import BacktestCreateRequest


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def _seed_dashboard_data(session: Session) -> dict[str, int | date]:
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

    closes = {
        instruments[0].id: [100, 101, 102, 103, 104],
        instruments[1].id: [90, 89, 88, 87, 86],
    }
    for instrument_id, values in closes.items():
        for index, close in enumerate(values):
            session.add(
                DailyBar(
                    instrument_id=instrument_id,
                    trade_date=trade_date - timedelta(days=4 - index),
                    open=Decimal(str(close)),
                    high=Decimal(str(close + 1)),
                    low=Decimal(str(close - 1)),
                    close=Decimal(str(close)),
                    volume=1000 + (index * 100),
                    change_percent=Decimal("1") if instrument_id == instruments[0].id else Decimal("-1"),
                )
            )
            session.add(
                IndicatorValue(
                    instrument_id=instrument_id,
                    trade_date=trade_date - timedelta(days=4 - index),
                    indicator_name="sma",
                    component="value",
                    parameter_signature="period=20",
                    value=Decimal(str(close - 1)),
                )
            )
            session.add(
                IndicatorValue(
                    instrument_id=instrument_id,
                    trade_date=trade_date - timedelta(days=4 - index),
                    indicator_name="rsi",
                    component="value",
                    parameter_signature="period=14",
                    value=Decimal("60") if instrument_id == instruments[0].id else Decimal("40"),
                )
            )
            session.add(
                IndicatorValue(
                    instrument_id=instrument_id,
                    trade_date=trade_date - timedelta(days=4 - index),
                    indicator_name="macd",
                    component="histogram",
                    parameter_signature="fast_period=12,slow_period=26,signal_period=9",
                    value=Decimal("1") if instrument_id == instruments[0].id else Decimal("-1"),
                )
            )

    session.add_all(
        [
            InstrumentTag(instrument_id=instruments[0].id, tag="semiconductor"),
            InstrumentTag(instrument_id=instruments[1].id, tag="hardware"),
        ]
    )

    watchlist = Watchlist(name="focus", description="Core watchlist")
    session.add(watchlist)
    session.flush()
    session.add_all(
        [
            WatchlistItem(watchlist_id=watchlist.id, instrument_id=instruments[0].id),
            WatchlistItem(watchlist_id=watchlist.id, instrument_id=instruments[1].id),
        ]
    )

    daily_record = TwDerivativesDaily(
        trade_date=trade_date,
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
    session.add(daily_record)
    session.flush()
    session.add(
        TwDerivativesFeature(
            daily_record_id=daily_record.id,
            trade_date=trade_date,
            market="TAIFEX",
            product_code="TX",
            contract_period="202401",
            institution="foreign_investors",
            call_put=None,
            delta_1d=Decimal("100"),
            delta_5d=Decimal("150"),
            delta_20d=Decimal("200"),
            zscore_20d=Decimal("1.2"),
            regime_label="bullish",
            bias_score=Decimal("1.5"),
            anomaly_flag=False,
        )
    )
    session.commit()

    generate_and_persist_candidate_run(session, candidate_date=trade_date, top_n=10)
    persist_generated_report(session, generate_market_summary_report(session, report_date=trade_date))
    persist_generated_report(session, generate_daily_report_bundle(session, report_date=trade_date))
    create_and_run_backtest(
        session,
        BacktestCreateRequest.model_validate(
            {
                "name": "Simple backtest",
                "definition": {
                    "instrument_id": instruments[0].id,
                    "initial_cash": "1000",
                    "position_size": "1",
                    "entry_rule": {
                        "left": {"kind": "price", "field": "close"},
                        "operator": "gt",
                        "right": {"kind": "constant", "value": "101"},
                    },
                    "exit_rule": {
                        "left": {"kind": "price", "field": "close"},
                        "operator": "lt",
                        "right": {"kind": "constant", "value": "104"},
                    },
                },
            }
        ),
    )
    session.commit()

    return {"trade_date": trade_date, "watchlist_id": watchlist.id, "instrument_id": instruments[0].id}


def test_dashboard_services_build_populated_aggregates() -> None:
    session = _build_session()
    seeded = _seed_dashboard_data(session)
    trade_date = cast(date, seeded["trade_date"])
    watchlist_id = cast(int, seeded["watchlist_id"])

    overview = build_dashboard_overview(session, trade_date=trade_date, watchlist_id=watchlist_id, tag="semiconductor")
    watchlist_dashboard = build_watchlist_dashboard(session, watchlist_id=watchlist_id, trade_date=trade_date)
    group_dashboard = build_group_dashboard(session, tag="semiconductor", trade_date=trade_date)
    candidates_dashboard = build_candidates_dashboard(session, candidate_date=trade_date, limit=5)
    derivatives_dashboard = build_derivatives_dashboard(session, trade_date=trade_date)
    backtests_dashboard = build_backtests_dashboard(session, limit=5)
    reports_dashboard = build_reports_dashboard(session, report_date=trade_date, limit=5)

    assert overview.meta.is_empty is False
    assert overview.data.market_snapshot is not None
    assert watchlist_dashboard.data is not None
    assert group_dashboard.data is not None
    assert candidates_dashboard.data is not None
    assert derivatives_dashboard.data is not None
    assert backtests_dashboard.data is not None
    assert reports_dashboard.data is not None
    assert any(card.key == "candidates" for card in overview.summary_cards)


def test_dashboard_services_handle_empty_state() -> None:
    session = _build_session()

    overview = build_dashboard_overview(session)
    candidates_dashboard = build_candidates_dashboard(session)
    derivatives_dashboard = build_derivatives_dashboard(session)
    backtests_dashboard = build_backtests_dashboard(session)
    reports_dashboard = build_reports_dashboard(session)

    assert overview.meta.is_empty is True
    assert overview.data.market_snapshot is None
    assert candidates_dashboard.meta.is_empty is True
    assert derivatives_dashboard.meta.is_empty is True
    assert backtests_dashboard.meta.is_empty is True
    assert reports_dashboard.meta.is_empty is True
