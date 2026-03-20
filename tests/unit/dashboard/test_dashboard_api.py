from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import cast

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from apps.api.main import app
from services.core.backtesting.service import create_and_run_backtest
from services.core.candidates.service import generate_and_persist_candidate_run
from services.core.reports.bundle import generate_daily_report_bundle
from services.core.reports.generators import generate_market_summary_report
from services.core.reports.service import persist_generated_report
from services.db.base import Base
from services.db.session import get_db_session
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


def _seed_dashboard_api_data(session: Session) -> dict[str, int | date]:
    trade_date = date(2024, 1, 5)
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
    for index, close in enumerate([100, 101, 102, 103, 104]):
        current_date = trade_date - timedelta(days=4 - index)
        session.add(
            DailyBar(
                instrument_id=instrument.id,
                trade_date=current_date,
                open=Decimal(str(close)),
                high=Decimal(str(close + 1)),
                low=Decimal(str(close - 1)),
                close=Decimal(str(close)),
                volume=1000 + (index * 100),
                change_percent=Decimal("1"),
            )
        )
        session.add(
            IndicatorValue(
                instrument_id=instrument.id,
                trade_date=current_date,
                indicator_name="sma",
                component="value",
                parameter_signature="period=20",
                value=Decimal(str(close - 1)),
            )
        )
        session.add(
            IndicatorValue(
                instrument_id=instrument.id,
                trade_date=current_date,
                indicator_name="rsi",
                component="value",
                parameter_signature="period=14",
                value=Decimal("60"),
            )
        )
        session.add(
            IndicatorValue(
                instrument_id=instrument.id,
                trade_date=current_date,
                indicator_name="macd",
                component="histogram",
                parameter_signature="fast_period=12,slow_period=26,signal_period=9",
                value=Decimal("1"),
            )
        )
    session.add(InstrumentTag(instrument_id=instrument.id, tag="semiconductor"))
    watchlist = Watchlist(name="focus", description="Core")
    session.add(watchlist)
    session.flush()
    session.add(WatchlistItem(watchlist_id=watchlist.id, instrument_id=instrument.id))
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
            delta_1d=Decimal("10"),
            delta_5d=Decimal("20"),
            delta_20d=Decimal("30"),
            zscore_20d=Decimal("1.1"),
            regime_label="bullish",
            bias_score=Decimal("1.2"),
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
                "name": "Dashboard backtest",
                "definition": {
                    "instrument_id": instrument.id,
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
    return {"trade_date": trade_date, "watchlist_id": watchlist.id}


@pytest.mark.asyncio
async def test_dashboard_api_routes_return_frontend_friendly_payloads() -> None:
    session = _build_session()
    seeded = _seed_dashboard_api_data(session)
    trade_date = cast(date, seeded["trade_date"])
    watchlist_id = cast(int, seeded["watchlist_id"])

    async def override_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        overview_response = await client.get(
            "/api/dashboard/overview",
            params={"trade_date": trade_date.isoformat(), "watchlist_id": watchlist_id, "tag": "semiconductor"},
        )
        watchlist_response = await client.get(f"/api/dashboard/watchlists/{watchlist_id}", params={"trade_date": trade_date.isoformat()})
        group_response = await client.get("/api/dashboard/groups/semiconductor", params={"trade_date": trade_date.isoformat()})
        candidates_response = await client.get("/api/dashboard/candidates/latest", params={"candidate_date": trade_date.isoformat(), "limit": 5})
        derivatives_response = await client.get("/api/dashboard/derivatives/latest", params={"trade_date": trade_date.isoformat()})
        backtests_response = await client.get("/api/dashboard/backtests/latest")
        reports_response = await client.get("/api/dashboard/reports/latest", params={"report_date": trade_date.isoformat(), "limit": 5})

    app.dependency_overrides.clear()

    assert overview_response.status_code == 200
    assert overview_response.json()["meta"]["is_empty"] is False
    assert "summary_cards" in overview_response.json()
    assert watchlist_response.status_code == 200
    assert group_response.status_code == 200
    assert candidates_response.status_code == 200
    assert candidates_response.json()["meta"]["returned_count"] >= 1
    assert derivatives_response.status_code == 200
    assert backtests_response.status_code == 200
    assert backtests_response.json()["meta"]["is_empty"] is False
    assert reports_response.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_api_empty_state_handling() -> None:
    session = _build_session()

    async def override_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        overview_response = await client.get("/api/dashboard/overview")
        candidates_response = await client.get("/api/dashboard/candidates/latest")
        derivatives_response = await client.get("/api/dashboard/derivatives/latest")
        backtests_response = await client.get("/api/dashboard/backtests/latest")
        reports_response = await client.get("/api/dashboard/reports/latest")
        missing_watchlist_response = await client.get("/api/dashboard/watchlists/999")

    app.dependency_overrides.clear()

    assert overview_response.status_code == 200
    assert overview_response.json()["meta"]["is_empty"] is True
    assert candidates_response.status_code == 200
    assert candidates_response.json()["meta"]["is_empty"] is True
    assert derivatives_response.status_code == 200
    assert derivatives_response.json()["meta"]["is_empty"] is True
    assert backtests_response.status_code == 200
    assert backtests_response.json()["meta"]["is_empty"] is True
    assert reports_response.status_code == 200
    assert reports_response.json()["meta"]["is_empty"] is True
    assert missing_watchlist_response.status_code == 404
