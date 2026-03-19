from __future__ import annotations

from sqlalchemy.orm import Session

from services.core.backtesting.dsl import parse_strategy_definition
from services.core.backtesting.engine import execute_backtest
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
from services.schemas.backtesting import BacktestCreateRequest


def create_and_run_backtest(session: Session, request: BacktestCreateRequest) -> tuple[Strategy, BacktestRun]:
    strategy_definition = parse_strategy_definition(request.definition.model_dump())
    strategy = StrategyRepository(session).create(
        instrument_id=strategy_definition.instrument_id,
        name=request.name,
        description=request.description,
        definition_json=request.definition.model_dump(mode="json"),
    )

    bars = DailyBarRepository(session).list_for_instrument(strategy_definition.instrument_id)
    indicator_values = IndicatorValueRepository(session).list_for_instrument(strategy_definition.instrument_id)
    execution = execute_backtest(strategy_definition, bars=bars, indicator_values=indicator_values)

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
    return strategy, run


def get_backtest_run(session: Session, run_id: int) -> BacktestRun | None:
    return BacktestRunRepository(session).get(run_id)


def list_backtest_trades(session: Session, run_id: int) -> list[BacktestTrade]:
    return BacktestTradeRepository(session).list_for_run(run_id)
