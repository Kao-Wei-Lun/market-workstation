from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from services.core.backtesting.dsl import parse_strategy_definition
from services.core.backtesting.search import _build_parameter_combinations, _load_strategy_inputs
from services.core.backtesting.service import ranking_score_from_execution
from services.db.repositories.backtests import (
    BacktestRunRepository,
    BacktestTradeRepository,
    BacktestWalkForwardRunRepository,
    BacktestWalkForwardWindowRepository,
    StrategyRepository,
)
from services.models.backtest_run import BacktestRun
from services.models.backtest_trade import BacktestTrade
from services.models.backtest_walk_forward_run import BacktestWalkForwardRun
from services.models.backtest_walk_forward_window import BacktestWalkForwardWindow
from services.models.strategy import Strategy
from services.schemas.backtesting import BacktestWalkForwardRequest
from services.core.backtesting.engine import execute_backtest


def create_and_run_walk_forward(
    session: Session,
    request: BacktestWalkForwardRequest,
) -> tuple[Strategy, BacktestWalkForwardRun, list[BacktestWalkForwardWindow]]:
    strategy_definition = parse_strategy_definition(request.definition.model_dump())
    strategy = StrategyRepository(session).create(
        instrument_id=strategy_definition.instrument_id,
        name=request.name,
        description=request.description,
        definition_json=request.definition.model_dump(mode="json"),
    )
    bars_by_instrument, indicator_values = _load_strategy_inputs(session, strategy_definition)
    all_dates = sorted(
        {
            bar.trade_date
            for instrument_bars in bars_by_instrument.values()
            for bar in instrument_bars
        }
    )
    if not all_dates:
        walk_forward_run = BacktestWalkForwardRunRepository(session).create(
            BacktestWalkForwardRun(
                strategy_id=strategy.id,
                status="completed",
                ranking_metric=request.ranking_metric,
                parameter_space_json={key: [str(value) for value in values] for key, values in request.parameter_space.items()},
                summary_json={"window_count": 0},
                train_window_days=request.train_window_days,
                test_window_days=request.test_window_days,
                step_days=request.step_days or request.test_window_days,
                started_at=datetime.now(tz=timezone.utc),
                finished_at=datetime.now(tz=timezone.utc),
            )
        )
        return strategy, walk_forward_run, []

    windows: list[BacktestWalkForwardWindow] = []
    step_days = request.step_days or request.test_window_days
    started_at = datetime.now(tz=timezone.utc)
    combinations = _build_parameter_combinations(request.parameter_space)
    window_index = 0
    cursor = 0
    while True:
        train_start_idx = cursor
        train_end_idx = train_start_idx + request.train_window_days - 1
        test_start_idx = train_end_idx + 1
        test_end_idx = test_start_idx + request.test_window_days - 1
        if test_end_idx >= len(all_dates):
            break
        train_start = all_dates[train_start_idx]
        train_end = all_dates[train_end_idx]
        test_start = all_dates[test_start_idx]
        test_end = all_dates[test_end_idx]

        best_parameters: dict[str, Decimal] | None = None
        best_execution = None
        best_score: Decimal | None = None
        for parameters in combinations:
            train_execution = execute_backtest(
                strategy_definition,
                bars=_filter_bars_by_range(bars_by_instrument, train_start, train_end),
                indicator_values=_filter_indicators_by_range(indicator_values, train_start, train_end),
                parameters=parameters,
            )
            score = ranking_score_from_execution(train_execution, request.ranking_metric)
            if best_score is None or score > best_score:
                best_score = score
                best_parameters = parameters
                best_execution = train_execution

        assert best_parameters is not None
        assert best_execution is not None
        test_execution = execute_backtest(
            strategy_definition,
            bars=_filter_bars_by_range(bars_by_instrument, test_start, test_end),
            indicator_values=_filter_indicators_by_range(indicator_values, test_start, test_end),
            parameters=best_parameters,
        )
        test_run = BacktestRunRepository(session).create(
            BacktestRun(
                strategy_id=strategy.id,
                status="completed",
                initial_cash=test_execution.initial_cash,
                final_cash=test_execution.final_cash,
                total_return=test_execution.total_return,
                total_return_pct=test_execution.total_return_pct,
                total_trades=test_execution.total_trades,
                win_rate=test_execution.win_rate,
                fee_paid=test_execution.fee_paid,
                tax_paid=test_execution.tax_paid,
                slippage_paid=test_execution.slippage_paid,
                resolved_parameters_json={key: str(value) for key, value in best_parameters.items()},
                metrics_json=test_execution.metrics.as_dict(),
                notes=f"walk_forward_window={window_index}",
                started_at=test_execution.started_at,
                finished_at=test_execution.finished_at,
            )
        )
        BacktestTradeRepository(session).create_many(
            [
                BacktestTrade(
                    run_id=test_run.id,
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
                for trade in test_execution.trades
            ]
        )
        windows.append(
            BacktestWalkForwardWindow(
                walk_forward_run_id=0,
                backtest_run_id=test_run.id,
                window_index=window_index,
                train_start_date=train_start,
                train_end_date=train_end,
                test_start_date=test_start,
                test_end_date=test_end,
                selected_parameters_json={key: str(value) for key, value in best_parameters.items()},
                train_metrics_json=best_execution.metrics.as_dict(),
                test_metrics_json=test_execution.metrics.as_dict(),
                ranking_score=best_score,
            )
        )
        window_index += 1
        cursor += step_days

    finished_at = datetime.now(tz=timezone.utc)
    walk_forward_run = BacktestWalkForwardRunRepository(session).create(
        BacktestWalkForwardRun(
            strategy_id=strategy.id,
            status="completed",
            ranking_metric=request.ranking_metric,
            parameter_space_json={key: [str(value) for value in values] for key, values in request.parameter_space.items()},
            summary_json={
                "window_count": len(windows),
                "average_test_score": str(
                    (
                        sum((window.ranking_score for window in windows), Decimal("0")) / Decimal(len(windows))
                    ).quantize(Decimal("0.000001"))
                    if windows
                    else Decimal("0")
                ),
            },
            train_window_days=request.train_window_days,
            test_window_days=request.test_window_days,
            step_days=step_days,
            started_at=started_at,
            finished_at=finished_at,
        )
    )
    for window in windows:
        window.walk_forward_run_id = walk_forward_run.id
    BacktestWalkForwardWindowRepository(session).create_many(windows)
    return strategy, walk_forward_run, BacktestWalkForwardWindowRepository(session).list_for_walk_forward_run(walk_forward_run.id)


def get_walk_forward_run(session: Session, run_id: int) -> BacktestWalkForwardRun | None:
    return BacktestWalkForwardRunRepository(session).get(run_id)


def list_walk_forward_windows(session: Session, run_id: int) -> list[BacktestWalkForwardWindow]:
    return BacktestWalkForwardWindowRepository(session).list_for_walk_forward_run(run_id)


def _filter_bars_by_range(bars_by_instrument: dict[int, list], start_date, end_date) -> dict[int, list]:
    return {
        instrument_id: [bar for bar in bars if start_date <= bar.trade_date <= end_date]
        for instrument_id, bars in bars_by_instrument.items()
    }


def _filter_indicators_by_range(indicator_values: list, start_date, end_date) -> list:
    return [row for row in indicator_values if start_date <= row.trade_date <= end_date]
