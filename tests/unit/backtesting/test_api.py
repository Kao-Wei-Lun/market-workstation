from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from apps.api.main import app
from services.db.base import Base
from services.db.session import get_db_session
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


def _seed_backtest_data(session: Session) -> Instrument:
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
    closes = [10, 11, 12, 11, 10, 11, 12, 13, 14, 13, 12, 11]
    for index, close in enumerate(closes):
        session.add(
            DailyBar(
                instrument_id=instrument.id,
                trade_date=date(2024, 1, 1) + timedelta(days=index),
                open=Decimal(str(close)),
                high=Decimal(str(close)),
                low=Decimal(str(close)),
                close=Decimal(str(close)),
                volume=1000 + (index * 10),
            )
        )
        session.add(
            IndicatorValue(
                instrument_id=instrument.id,
                trade_date=date(2024, 1, 1) + timedelta(days=index),
                indicator_name="sma",
                component="value",
                parameter_signature="period=3",
                value=Decimal(str(max(close - 1, 1))),
            )
        )
    session.flush()
    return instrument


@pytest.mark.asyncio
async def test_backtest_api_supports_run_search_and_walk_forward_routes() -> None:
    session = _build_session()
    instrument = _seed_backtest_data(session)

    async def override_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/backtests/runs",
            json={
                "name": "SMA Cross",
                "definition": {
                    "instrument_id": instrument.id,
                    "initial_cash": "1000",
                    "position_size": "1",
                    "costs": {"fee_rate": "0", "tax_rate": "0", "slippage_rate": "0"},
                    "entry_rule": {
                        "left": {"kind": "price", "field": "close"},
                        "operator": "gt",
                        "right": {"kind": "constant", "value": "10"},
                    },
                    "exit_rule": {
                        "left": {"kind": "price", "field": "close"},
                        "operator": "lt",
                        "right": {"kind": "constant", "value": "11"},
                    },
                },
            },
        )
        run_id = create_response.json()["run"]["id"]
        run_response = await client.get(f"/backtests/runs/{run_id}")
        list_runs_response = await client.get("/backtests/runs")
        trades_response = await client.get(f"/backtests/runs/{run_id}/trades")
        filtered_trades_response = await client.get("/backtests/trades", params={"run_id": run_id, "instrument_id": instrument.id})
        export_response = await client.get(f"/backtests/runs/{run_id}/export", params={"export_format": "csv"})
        search_response = await client.post(
            "/backtests/searches",
            json={
                "name": "Search",
                "definition": {
                    "instrument_id": instrument.id,
                    "initial_cash": "1000",
                    "position_size": "1",
                    "entry_rule": {
                        "left": {"kind": "price", "field": "close"},
                        "operator": "gt",
                        "right": {"kind": "parameter", "parameter_name": "entry_threshold"},
                    },
                    "exit_rule": {
                        "left": {"kind": "price", "field": "close"},
                        "operator": "lt",
                        "right": {"kind": "parameter", "parameter_name": "exit_threshold"},
                    },
                },
                "parameter_space": {
                    "entry_threshold": ["10", "11"],
                    "exit_threshold": ["11", "12"],
                },
            },
        )
        search_run_id = search_response.json()["search_run"]["id"]
        search_results_response = await client.get(f"/backtests/searches/{search_run_id}/results")
        walk_forward_response = await client.post(
            "/backtests/walk-forward",
            json={
                "name": "Walk Forward",
                "definition": {
                    "instrument_id": instrument.id,
                    "initial_cash": "1000",
                    "position_size": "1",
                    "entry_rule": {
                        "left": {"kind": "price", "field": "close"},
                        "operator": "gt",
                        "right": {"kind": "parameter", "parameter_name": "entry_threshold"},
                    },
                    "exit_rule": {
                        "left": {"kind": "price", "field": "close"},
                        "operator": "lt",
                        "right": {"kind": "parameter", "parameter_name": "exit_threshold"},
                    },
                },
                "parameter_space": {
                    "entry_threshold": ["10", "11"],
                    "exit_threshold": ["11", "12"],
                },
                "train_window_days": 5,
                "test_window_days": 3,
            },
        )
        walk_forward_run_id = walk_forward_response.json()["walk_forward_run"]["id"]
        walk_forward_windows_response = await client.get(
            f"/backtests/walk-forward/{walk_forward_run_id}/windows"
        )

    app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert run_response.status_code == 200
    assert list_runs_response.status_code == 200
    assert trades_response.status_code == 200
    assert filtered_trades_response.status_code == 200
    assert export_response.status_code == 200
    assert search_response.status_code == 200
    assert search_results_response.status_code == 200
    assert walk_forward_response.status_code == 200
    assert walk_forward_windows_response.status_code == 200
    assert len(search_results_response.json()) == 4
    assert "entry_date" in export_response.text
