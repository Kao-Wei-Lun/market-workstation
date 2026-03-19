from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from services.core.backtesting.engine import execute_backtest
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.schemas.backtesting import StrategyDefinition


def test_backtest_executes_single_long_trade() -> None:
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
        for index, close in enumerate([10, 11, 12, 11, 10])
    ]
    indicator_values = [
        IndicatorValue(
            instrument_id=1,
            trade_date=date(2024, 1, 3),
            indicator_name="sma",
            component="value",
            parameter_signature="period=3",
            value=Decimal("11"),
        ),
        IndicatorValue(
            instrument_id=1,
            trade_date=date(2024, 1, 4),
            indicator_name="sma",
            component="value",
            parameter_signature="period=3",
            value=Decimal("11.333333"),
        ),
        IndicatorValue(
            instrument_id=1,
            trade_date=date(2024, 1, 5),
            indicator_name="sma",
            component="value",
            parameter_signature="period=3",
            value=Decimal("11"),
        ),
    ]
    strategy = StrategyDefinition.model_validate(
        {
            "instrument_id": 1,
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
        }
    )

    result = execute_backtest(strategy, bars=bars, indicator_values=indicator_values)

    assert result.total_trades == 1
    assert len(result.trades) == 1
    assert result.trades[0].entry_date == date(2024, 1, 3)
    assert result.trades[0].exit_date == date(2024, 1, 4)
