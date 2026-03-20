from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from services.core.backtesting.dsl import parse_strategy_definition
from services.core.backtesting.engine import BacktestExecutionResult, execute_backtest
from services.core.exports import rows_to_csv
from services.core.backtesting.universe import resolve_universe_instrument_ids
from services.db.repositories.backtests import (
    BacktestRunRepository,
    BacktestTradeRepository,
    StrategyRepository,
)
from services.db.repositories.daily_bars import DailyBarRepository
from services.db.repositories.indicator_values import IndicatorValueRepository
from services.models.backtest_run import BacktestRun
from services.models.backtest_trade import BacktestTrade
from services.models.strategy import Strategy
from services.schemas.backtesting import BacktestCreateRequest, StrategyDefinition


def create_and_run_backtest(session: Session, request: BacktestCreateRequest) -> tuple[Strategy, BacktestRun]:
    strategy_definition = parse_strategy_definition(request.definition.model_dump())
    strategy = StrategyRepository(session).create(
        instrument_id=strategy_definition.instrument_id,
        name=request.name,
        description=request.description,
        definition_json=request.definition.model_dump(mode="json"),
    )
    run = execute_strategy(
        session,
        strategy=strategy,
        strategy_definition=strategy_definition,
        parameters=request.parameters,
    )
    return strategy, run


def execute_strategy(
    session: Session,
    *,
    strategy: Strategy,
    strategy_definition: StrategyDefinition,
    parameters: dict[str, Decimal] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> BacktestRun:
    instrument_ids = resolve_universe_instrument_ids(session, strategy_definition)
    bars = DailyBarRepository(session).list_for_instruments(
        instrument_ids,
        start_date=start_date,
        end_date=end_date,
    )
    indicator_values = IndicatorValueRepository(session).list_for_instruments(
        instrument_ids,
        start_date=start_date,
        end_date=end_date,
    )
    bars_by_instrument: dict[int, list[Any]] = {}
    for bar in bars:
        bars_by_instrument.setdefault(bar.instrument_id, []).append(bar)
    execution = execute_backtest(
        strategy_definition,
        bars=bars_by_instrument,
        indicator_values=indicator_values,
        parameters=parameters,
    )
    run = BacktestRunRepository(session).create(
        BacktestRun(
            strategy_id=strategy.id,
            status="completed",
            initial_cash=execution.initial_cash,
            final_cash=execution.final_cash,
            total_return=execution.total_return,
            total_return_pct=execution.total_return_pct,
            total_trades=execution.total_trades,
            win_rate=execution.win_rate,
            fee_paid=execution.fee_paid,
            tax_paid=execution.tax_paid,
            slippage_paid=execution.slippage_paid,
            resolved_parameters_json=_serialize_decimal_mapping(parameters or {}),
            metrics_json=execution.metrics.as_dict(),
            notes=execution.notes,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
        )
    )
    BacktestTradeRepository(session).create_many(
        [
            BacktestTrade(
                run_id=run.id,
                instrument_id=trade.instrument_id,
                entry_date=trade.entry_date,
                exit_date=trade.exit_date,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                quantity=trade.quantity,
                gross_pnl=trade.gross_pnl,
                net_pnl=trade.net_pnl,
                fee_paid=trade.fee_paid,
                tax_paid=trade.tax_paid,
                slippage_paid=trade.slippage_paid,
                holding_period_days=trade.holding_period_days,
                exit_reason=trade.exit_reason,
            )
            for trade in execution.trades
        ]
    )
    return run


def get_backtest_run(session: Session, run_id: int) -> BacktestRun | None:
    return BacktestRunRepository(session).get(run_id)


def list_backtest_trades(session: Session, run_id: int) -> list[BacktestTrade]:
    return BacktestTradeRepository(session).list_for_run(run_id)


def list_backtest_runs(
    session: Session,
    *,
    strategy_id: int | None = None,
    limit: int | None = None,
) -> list[BacktestRun]:
    return BacktestRunRepository(session).list_runs(strategy_id=strategy_id, limit=limit)


def query_backtest_trades(
    session: Session,
    *,
    run_id: int | None = None,
    instrument_id: int | None = None,
) -> list[BacktestTrade]:
    return BacktestTradeRepository(session).list_trades(run_id=run_id, instrument_id=instrument_id)


def export_backtest_run(
    session: Session,
    *,
    run_id: int,
    export_format: str,
) -> tuple[str, str]:
    run = get_backtest_run(session, run_id)
    if run is None:
        msg = "backtest run not found"
        raise ValueError(msg)
    trades = list_backtest_trades(session, run_id)
    rows = [
        {
            "run_id": trade.run_id,
            "instrument_id": trade.instrument_id,
            "entry_date": trade.entry_date.isoformat(),
            "exit_date": trade.exit_date.isoformat(),
            "entry_price": str(trade.entry_price),
            "exit_price": str(trade.exit_price),
            "quantity": trade.quantity,
            "gross_pnl": str(trade.gross_pnl),
            "net_pnl": str(trade.net_pnl),
            "exit_reason": trade.exit_reason,
        }
        for trade in trades
    ]
    if export_format == "json":
        import json

        return (
            f"backtest_run_{run_id}.json",
            json.dumps(
                {
                    "run_id": run.id,
                    "strategy_id": run.strategy_id,
                    "metrics": run.metrics_json,
                    "trades": rows,
                },
                indent=2,
            ),
        )
    return f"backtest_run_{run_id}.csv", rows_to_csv(rows)


def ranking_score_from_execution(execution: BacktestExecutionResult, ranking_metric: str) -> Decimal:
    if ranking_metric == "sharpe":
        return execution.metrics.sharpe_ratio
    if ranking_metric == "cagr":
        return execution.metrics.cagr_pct
    if ranking_metric == "max_drawdown":
        return Decimal("0") - execution.metrics.max_drawdown_pct
    return execution.metrics.score


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _serialize_decimal_mapping(values: dict[str, Decimal]) -> dict[str, str]:
    return {key: str(value) for key, value in values.items()}
