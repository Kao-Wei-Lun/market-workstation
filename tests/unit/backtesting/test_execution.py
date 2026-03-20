from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from services.core.backtesting.engine import execute_backtest
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.schemas.backtesting import StrategyDefinition


def test_backtest_executes_multiple_positions_with_time_exit() -> None:
    bars_by_instrument: dict[int, list[DailyBar]] = {}
    for instrument_id, closes in {
        1: [10, 11, 12, 13, 12, 11],
        2: [20, 21, 22, 23, 22, 21],
    }.items():
        bars_by_instrument[instrument_id] = [
            DailyBar(
                instrument_id=instrument_id,
                trade_date=date(2024, 1, 1) + timedelta(days=index),
                open=Decimal(str(close)),
                high=Decimal(str(close)),
                low=Decimal(str(close)),
                close=Decimal(str(close)),
                volume=1000 + (instrument_id * 100),
            )
            for index, close in enumerate(closes)
        ]

    indicator_values = [
        IndicatorValue(
            instrument_id=instrument_id,
            trade_date=date(2024, 1, 2),
            indicator_name="sma",
            component="value",
            parameter_signature="period=2",
            value=Decimal("10"),
        )
        for instrument_id in [1, 2]
    ]
    indicator_values.extend(
        [
            IndicatorValue(
                instrument_id=instrument_id,
                trade_date=date(2024, 1, 3),
                indicator_name="sma",
                component="value",
                parameter_signature="period=2",
                value=Decimal("11"),
            )
            for instrument_id in [1, 2]
        ]
    )

    strategy = StrategyDefinition.model_validate(
        {
            "universe": {"instrument_ids": [1, 2]},
            "initial_cash": "10000",
            "position_size": "0.4",
            "max_concurrent_positions": 2,
            "time_exit_days": 2,
            "costs": {"fee_rate": "0", "tax_rate": "0", "slippage_rate": "0"},
            "entry_rule": {
                "left": {"kind": "price", "field": "close"},
                "operator": "gt",
                "right": {
                    "kind": "indicator",
                    "indicator_name": "sma",
                    "component": "value",
                    "parameter_signature": "period=2",
                },
            },
            "exit_rule": {
                "left": {"kind": "price", "field": "close"},
                "operator": "lt",
                "right": {"kind": "constant", "value": "0"},
            },
        }
    )

    result = execute_backtest(strategy, bars=bars_by_instrument, indicator_values=indicator_values)

    assert result.total_trades >= 2
    assert len(result.trades) == result.total_trades
    assert {trade.instrument_id for trade in result.trades} == {1, 2}
    assert all(trade.exit_reason in {"time_exit", "forced_exit"} for trade in result.trades)
    assert result.metrics.max_drawdown_pct >= 0


def test_backtest_applies_stop_loss_exit() -> None:
    bars = [
        DailyBar(
            instrument_id=1,
            trade_date=date(2024, 1, 1) + timedelta(days=index),
            open=Decimal(str(close)),
            high=Decimal(str(close)),
            low=Decimal(str(close)),
            close=Decimal(str(close)),
            volume=1000,
        )
        for index, close in enumerate([10, 11, 9, 8])
    ]
    strategy = StrategyDefinition.model_validate(
        {
            "instrument_id": 1,
            "initial_cash": "1000",
            "position_size": "1",
            "stop_loss_pct": "10",
            "costs": {"fee_rate": "0", "tax_rate": "0", "slippage_rate": "0"},
            "entry_rule": {
                "left": {"kind": "price", "field": "close"},
                "operator": "gt",
                "right": {"kind": "constant", "value": "10"},
            },
            "exit_rule": {
                "left": {"kind": "price", "field": "close"},
                "operator": "lt",
                "right": {"kind": "constant", "value": "0"},
            },
        }
    )

    result = execute_backtest(strategy, bars=bars, indicator_values=[])

    assert result.total_trades == 1
    assert result.trades[0].exit_reason == "stop_loss"
