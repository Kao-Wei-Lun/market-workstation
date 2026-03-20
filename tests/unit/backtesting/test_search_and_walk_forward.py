from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.backtesting.search import create_and_run_parameter_search, list_parameter_search_results
from services.core.backtesting.walk_forward import create_and_run_walk_forward, list_walk_forward_windows
from services.db.base import Base
from services.models import import_models
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.schemas.backtesting import BacktestParameterSearchRequest, BacktestWalkForwardRequest


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
    closes = [10, 10.5, 11, 12, 13, 14, 15, 16, 15, 14, 15, 16]
    for index, close in enumerate(closes):
        session.add(
            DailyBar(
                instrument_id=instrument.id,
                trade_date=date(2024, 1, 1) + timedelta(days=index),
                open=Decimal(str(close)),
                high=Decimal(str(close)),
                low=Decimal(str(close)),
                close=Decimal(str(close)),
                volume=1_000 + (index * 100),
            )
        )
    for index, sma_value in enumerate([10, 10.5, 11, 11.5, 12, 13, 14, 15, 15, 15, 15, 15]):
        session.add(
            IndicatorValue(
                instrument_id=instrument.id,
                trade_date=date(2024, 1, 1) + timedelta(days=index),
                indicator_name="sma",
                component="value",
                parameter_signature="period=3",
                value=Decimal(str(sma_value)),
            )
        )
    session.flush()
    return instrument


def test_parameter_search_flow_persists_ranked_results() -> None:
    session = _build_session()
    instrument = _seed_backtest_data(session)
    request = BacktestParameterSearchRequest.model_validate(
        {
            "name": "Parameterized SMA",
            "definition": {
                "instrument_id": instrument.id,
                "initial_cash": "1000",
                "position_size": "1",
                "costs": {"fee_rate": "0", "tax_rate": "0", "slippage_rate": "0"},
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
                "entry_threshold": ["10", "12"],
                "exit_threshold": ["12", "14"],
            },
            "ranking_metric": "score",
        }
    )

    _, search_run, results = create_and_run_parameter_search(session, request)
    persisted_results = list_parameter_search_results(session, search_run.id)

    assert len(results) == 4
    assert len(persisted_results) == 4
    assert persisted_results[0].rank == 1
    assert search_run.best_parameters_json


def test_walk_forward_flow_persists_windows() -> None:
    session = _build_session()
    instrument = _seed_backtest_data(session)
    request = BacktestWalkForwardRequest.model_validate(
        {
            "name": "Walk Forward SMA",
            "definition": {
                "instrument_id": instrument.id,
                "initial_cash": "1000",
                "position_size": "1",
                "costs": {"fee_rate": "0", "tax_rate": "0", "slippage_rate": "0"},
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
                "entry_threshold": ["10", "12"],
                "exit_threshold": ["12", "14"],
            },
            "ranking_metric": "score",
            "train_window_days": 5,
            "test_window_days": 3,
        }
    )

    _, walk_forward_run, windows = create_and_run_walk_forward(session, request)
    persisted_windows = list_walk_forward_windows(session, walk_forward_run.id)

    assert walk_forward_run.summary_json["window_count"] == len(windows)
    assert windows
    assert persisted_windows[0].selected_parameters_json
