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


@pytest.mark.asyncio
async def test_backtest_api_create_and_query_routes() -> None:
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
    closes = [10, 11, 12, 11, 10]
    for index, close in enumerate(closes):
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
    for trade_date_value, sma_value in [
        (date(2024, 1, 3), Decimal("11")),
        (date(2024, 1, 4), Decimal("11.333333")),
        (date(2024, 1, 5), Decimal("11")),
    ]:
        session.add(
            IndicatorValue(
                instrument_id=instrument.id,
                trade_date=trade_date_value,
                indicator_name="sma",
                component="value",
                parameter_signature="period=3",
                value=sma_value,
            )
        )
    session.flush()

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
                        "right": {
                            "kind": "indicator",
                            "indicator_name": "sma",
                            "component": "value",
                            "parameter_signature": "period=3",
                        },
                    },
                    "exit_rule": {
                        "left": {"kind": "price", "field": "close"},
                        "operator": "lt",
                        "right": {
                            "kind": "indicator",
                            "indicator_name": "sma",
                            "component": "value",
                            "parameter_signature": "period=3",
                        },
                    },
                },
            },
        )
        run_id = create_response.json()["run"]["id"]
        run_response = await client.get(f"/backtests/runs/{run_id}")
        trades_response = await client.get(f"/backtests/runs/{run_id}/trades")

    app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert run_response.status_code == 200
    assert trades_response.status_code == 200
    assert len(trades_response.json()) == 1
