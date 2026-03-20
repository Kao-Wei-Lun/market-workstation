from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import product

from sqlalchemy.orm import Session

from services.core.backtesting.dsl import parse_strategy_definition
from services.core.backtesting.engine import execute_backtest
from services.core.backtesting.service import now_utc, ranking_score_from_execution
from services.core.backtesting.universe import resolve_universe_instrument_ids
from services.db.repositories.backtests import (
    BacktestRunRepository,
    BacktestSearchResultRepository,
    BacktestSearchRunRepository,
    BacktestTradeRepository,
    StrategyRepository,
)
from services.db.repositories.daily_bars import DailyBarRepository
from services.db.repositories.indicator_values import IndicatorValueRepository
from services.models.backtest_run import BacktestRun
from services.models.backtest_search_result import BacktestSearchResult
from services.models.backtest_search_run import BacktestSearchRun
from services.models.backtest_trade import BacktestTrade
from services.models.strategy import Strategy
from services.schemas.backtesting import BacktestParameterSearchRequest, StrategyDefinition


@dataclass(frozen=True)
class ParameterCombinationResult:
    parameters: dict[str, Decimal]
    run: BacktestRun
    score: Decimal


def create_and_run_parameter_search(
    session: Session,
    request: BacktestParameterSearchRequest,
) -> tuple[Strategy, BacktestSearchRun, list[BacktestSearchResult]]:
    strategy_definition = parse_strategy_definition(request.definition.model_dump())
    strategy = StrategyRepository(session).create(
        instrument_id=strategy_definition.instrument_id,
        name=request.name,
        description=request.description,
        definition_json=request.definition.model_dump(mode="json"),
    )
    bars_by_instrument, indicator_values = _load_strategy_inputs(session, strategy_definition)
    search_run = BacktestSearchRunRepository(session).create(
        BacktestSearchRun(
            strategy_id=strategy.id,
            status="completed",
            ranking_metric=request.ranking_metric,
            parameter_space_json={key: [str(value) for value in values] for key, values in request.parameter_space.items()},
            best_parameters_json={},
            summary_json={},
            started_at=now_utc(),
            finished_at=now_utc(),
        )
    )
    combinations = _build_parameter_combinations(request.parameter_space)
    run_results: list[ParameterCombinationResult] = []
    for parameters in combinations:
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
                resolved_parameters_json={key: str(value) for key, value in parameters.items()},
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
        run_results.append(
            ParameterCombinationResult(
                parameters=parameters,
                run=run,
                score=ranking_score_from_execution(execution, request.ranking_metric),
            )
        )
    ranked_results = sorted(run_results, key=lambda item: item.score, reverse=True)
    search_results = [
        BacktestSearchResult(
            search_run_id=search_run.id,
            backtest_run_id=result.run.id,
            parameter_set_json={key: str(value) for key, value in result.parameters.items()},
            metrics_json=result.run.metrics_json,
            ranking_score=result.score,
            rank=index + 1,
        )
        for index, result in enumerate(ranked_results)
    ]
    BacktestSearchResultRepository(session).create_many(search_results)
    search_run.best_parameters_json = search_results[0].parameter_set_json if search_results else {}
    search_run.summary_json = {
        "combination_count": len(search_results),
        "best_score": str(search_results[0].ranking_score) if search_results else "0",
    }
    session.flush()
    return strategy, search_run, BacktestSearchResultRepository(session).list_for_search_run(search_run.id)


def get_parameter_search_run(session: Session, run_id: int) -> BacktestSearchRun | None:
    return BacktestSearchRunRepository(session).get(run_id)


def list_parameter_search_results(session: Session, run_id: int) -> list[BacktestSearchResult]:
    return BacktestSearchResultRepository(session).list_for_search_run(run_id)


def _build_parameter_combinations(parameter_space: dict[str, list[Decimal]]) -> list[dict[str, Decimal]]:
    names = list(parameter_space.keys())
    return [
        {name: combination[index] for index, name in enumerate(names)}
        for combination in product(*(parameter_space[name] for name in names))
    ]


def _load_strategy_inputs(
    session: Session,
    strategy_definition: StrategyDefinition,
) -> tuple[dict[int, list], list]:
    instrument_ids = resolve_universe_instrument_ids(session, strategy_definition)
    bars = DailyBarRepository(session).list_for_instruments(instrument_ids)
    indicator_values = IndicatorValueRepository(session).list_for_instruments(instrument_ids)
    bars_by_instrument: dict[int, list] = {}
    for bar in bars:
        bars_by_instrument.setdefault(bar.instrument_id, []).append(bar)
    return bars_by_instrument, indicator_values
