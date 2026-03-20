from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.backtesting.service import create_and_run_backtest, get_backtest_run, list_backtest_trades
from services.db.base import Base
from services.models import import_models
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.schemas.backtesting import BacktestCreateRequest


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_backtest_run_and_trade_persistence() -> None:
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

    request = BacktestCreateRequest.model_validate(
        {
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
        }
    )

    _, run = create_and_run_backtest(session, request)
    persisted_run = get_backtest_run(session, run.id)
    trades = list_backtest_trades(session, run.id)

    assert persisted_run is not None
    assert persisted_run.total_trades == 1
    assert persisted_run.resolved_parameters_json == {}
    assert "score" in persisted_run.metrics_json
    assert len(trades) == 1
    assert trades[0].run_id == run.id
