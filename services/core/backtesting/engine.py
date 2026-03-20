from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from math import sqrt

from services.core.backtesting.costs import (
    apply_entry_slippage,
    apply_exit_slippage,
    calculate_trade_costs,
)
from services.core.backtesting.dsl import evaluate_rule
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.schemas.backtesting import StrategyDefinition


@dataclass(frozen=True)
class ExecutedTrade:
    instrument_id: int
    entry_date: date
    exit_date: date
    entry_price: Decimal
    exit_price: Decimal
    quantity: int
    gross_pnl: Decimal
    net_pnl: Decimal
    fee_paid: Decimal
    tax_paid: Decimal
    slippage_paid: Decimal
    holding_period_days: int
    exit_reason: str


@dataclass(frozen=True)
class EquityPoint:
    trade_date: date
    equity: Decimal


@dataclass(frozen=True)
class BacktestMetrics:
    sharpe_ratio: Decimal
    cagr_pct: Decimal
    max_drawdown_pct: Decimal
    score: Decimal

    def as_dict(self) -> dict[str, str]:
        return {
            "sharpe_ratio": str(self.sharpe_ratio),
            "cagr_pct": str(self.cagr_pct),
            "max_drawdown_pct": str(self.max_drawdown_pct),
            "score": str(self.score),
        }


@dataclass(frozen=True)
class BacktestExecutionResult:
    initial_cash: Decimal
    final_cash: Decimal
    total_return: Decimal
    total_return_pct: Decimal
    total_trades: int
    win_rate: Decimal
    fee_paid: Decimal
    tax_paid: Decimal
    slippage_paid: Decimal
    started_at: datetime
    finished_at: datetime
    trades: list[ExecutedTrade]
    metrics: BacktestMetrics
    equity_curve: list[EquityPoint]
    notes: str | None = None


@dataclass
class _OpenPosition:
    instrument_id: int
    entry_date: date
    entry_price: Decimal
    quantity: int
    entry_fee: Decimal
    entry_slippage: Decimal


def execute_backtest(
    strategy: StrategyDefinition,
    *,
    bars: list[DailyBar] | dict[int, list[DailyBar]],
    indicator_values: list[IndicatorValue],
    parameters: dict[str, Decimal] | None = None,
) -> BacktestExecutionResult:
    started_at = datetime.now(tz=timezone.utc)
    bars_by_instrument = _normalize_bars(bars)
    indicator_map = {
        (item.trade_date, item.indicator_name, item.component, item.parameter_signature, item.instrument_id): item.value
        for item in indicator_values
    }
    trade_dates = sorted(
        {
            bar.trade_date
            for instrument_bars in bars_by_instrument.values()
            for bar in instrument_bars
        }
    )
    bars_by_date: dict[date, dict[int, DailyBar]] = {}
    last_bar_by_instrument: dict[int, DailyBar] = {}
    for instrument_id, instrument_bars in bars_by_instrument.items():
        if instrument_bars:
            last_bar_by_instrument[instrument_id] = instrument_bars[-1]
        for bar in instrument_bars:
            bars_by_date.setdefault(bar.trade_date, {})[instrument_id] = bar

    cash = strategy.initial_cash
    positions: dict[int, _OpenPosition] = {}
    trades: list[ExecutedTrade] = []
    equity_curve: list[EquityPoint] = []
    total_fees = Decimal("0")
    total_taxes = Decimal("0")
    total_slippage = Decimal("0")
    latest_prices: dict[int, Decimal] = {}

    for date_index, trade_date_value in enumerate(trade_dates):
        current_bars = bars_by_date.get(trade_date_value, {})
        for instrument_id, bar in current_bars.items():
            latest_prices[instrument_id] = bar.close

        for instrument_id in list(positions.keys()):
            position_bar = current_bars.get(instrument_id)
            if position_bar is None:
                continue
            position = positions[instrument_id]
            exit_reason = _resolve_exit_reason(
                strategy,
                position=position,
                bar=position_bar,
                indicator_map=indicator_map,
                parameters=parameters or {},
            )
            if exit_reason is None:
                continue
            trade, cash_delta, fee_delta, tax_delta, slippage_delta = _close_position(
                strategy,
                position=position,
                bar=position_bar,
                exit_reason=exit_reason,
            )
            trades.append(trade)
            cash += cash_delta
            total_fees += fee_delta
            total_taxes += tax_delta
            total_slippage += slippage_delta
            del positions[instrument_id]

        can_rebalance = strategy.rebalance_interval_days is None or (
            date_index % strategy.rebalance_interval_days == 0
        )
        if can_rebalance and len(positions) < strategy.max_concurrent_positions:
            capacity = strategy.max_concurrent_positions - len(positions)
            entry_candidates: list[tuple[int, DailyBar]] = []
            for instrument_id, bar in sorted(current_bars.items()):
                if instrument_id in positions:
                    continue
                if _should_enter(
                    strategy,
                    instrument_id=instrument_id,
                    bar=bar,
                    indicator_map=indicator_map,
                    parameters=parameters or {},
                ):
                    entry_candidates.append((instrument_id, bar))
            for instrument_id, bar in entry_candidates[:capacity]:
                entry_fill = apply_entry_slippage(bar.close, strategy.costs.slippage_rate)
                quantity = int((cash * strategy.position_size) // entry_fill)
                if quantity <= 0:
                    continue
                entry_costs = calculate_trade_costs(
                    price=entry_fill,
                    quantity=quantity,
                    costs=strategy.costs,
                    is_exit=False,
                )
                cash -= (entry_fill * quantity) + entry_costs.fee
                total_fees += entry_costs.fee
                total_slippage += entry_costs.slippage
                positions[instrument_id] = _OpenPosition(
                    instrument_id=instrument_id,
                    entry_date=bar.trade_date,
                    entry_price=entry_fill,
                    quantity=quantity,
                    entry_fee=entry_costs.fee,
                    entry_slippage=entry_costs.slippage,
                )

        equity_curve.append(
            EquityPoint(
                trade_date=trade_date_value,
                equity=_q(
                    cash
                    + sum(
                        latest_prices.get(instrument_id, position.entry_price) * position.quantity
                        for instrument_id, position in positions.items()
                    )
                ),
            )
        )

    for instrument_id, position in list(positions.items()):
        last_bar = last_bar_by_instrument[instrument_id]
        trade, cash_delta, fee_delta, tax_delta, slippage_delta = _close_position(
            strategy,
            position=position,
            bar=last_bar,
            exit_reason="forced_exit",
        )
        trades.append(trade)
        cash += cash_delta
        total_fees += fee_delta
        total_taxes += tax_delta
        total_slippage += slippage_delta

    finished_at = datetime.now(tz=timezone.utc)
    total_return = _q(cash - strategy.initial_cash)
    total_return_pct = (
        _q((total_return / strategy.initial_cash) * Decimal("100"))
        if strategy.initial_cash != 0
        else Decimal("0")
    )
    wins = sum(1 for trade in trades if trade.net_pnl > 0)
    win_rate = _q((Decimal(wins) / Decimal(len(trades))) * Decimal("100")) if trades else Decimal("0")
    metrics = _calculate_metrics(
        initial_cash=strategy.initial_cash,
        final_cash=cash,
        equity_curve=equity_curve,
    )
    return BacktestExecutionResult(
        initial_cash=_q(strategy.initial_cash),
        final_cash=_q(cash),
        total_return=total_return,
        total_return_pct=total_return_pct,
        total_trades=len(trades),
        win_rate=win_rate,
        fee_paid=_q(total_fees),
        tax_paid=_q(total_taxes),
        slippage_paid=_q(total_slippage),
        started_at=started_at,
        finished_at=finished_at,
        trades=sorted(trades, key=lambda trade: (trade.entry_date, trade.instrument_id)),
        metrics=metrics,
        equity_curve=equity_curve,
        notes=f"universe_size={len(bars_by_instrument)}",
    )


def _normalize_bars(bars: list[DailyBar] | dict[int, list[DailyBar]]) -> dict[int, list[DailyBar]]:
    if isinstance(bars, dict):
        return {
            instrument_id: sorted(instrument_bars, key=lambda item: item.trade_date)
            for instrument_id, instrument_bars in bars.items()
        }
    if not bars:
        return {}
    bars_by_instrument: dict[int, list[DailyBar]] = {}
    for bar in sorted(bars, key=lambda item: (item.instrument_id, item.trade_date)):
        bars_by_instrument.setdefault(bar.instrument_id, []).append(bar)
    return bars_by_instrument


def _should_enter(
    strategy: StrategyDefinition,
    *,
    instrument_id: int,
    bar: DailyBar,
    indicator_map: dict[tuple[date, str, str, str, int], Decimal],
    parameters: dict[str, Decimal],
) -> bool:
    return evaluate_rule(
        strategy.entry_rule,
        trade_date=bar.trade_date,
        price_values=_price_values_for_bar(bar),
        indicator_values=_indicator_values_for_instrument(indicator_map, instrument_id),
        parameters=parameters,
    )


def _resolve_exit_reason(
    strategy: StrategyDefinition,
    *,
    position: _OpenPosition,
    bar: DailyBar,
    indicator_map: dict[tuple[date, str, str, str, int], Decimal],
    parameters: dict[str, Decimal],
) -> str | None:
    holding_days = (bar.trade_date - position.entry_date).days
    if strategy.stop_loss_pct is not None:
        stop_price = position.entry_price * (Decimal("1") - (strategy.stop_loss_pct / Decimal("100")))
        if bar.close <= stop_price:
            return "stop_loss"
    if strategy.take_profit_pct is not None:
        take_profit_price = position.entry_price * (Decimal("1") + (strategy.take_profit_pct / Decimal("100")))
        if bar.close >= take_profit_price:
            return "take_profit"
    if strategy.time_exit_days is not None and holding_days >= strategy.time_exit_days:
        return "time_exit"
    should_exit = evaluate_rule(
        strategy.exit_rule,
        trade_date=bar.trade_date,
        price_values=_price_values_for_bar(bar),
        indicator_values=_indicator_values_for_instrument(indicator_map, position.instrument_id),
        parameters=parameters,
    )
    if should_exit:
        return "rule_exit"
    return None


def _close_position(
    strategy: StrategyDefinition,
    *,
    position: _OpenPosition,
    bar: DailyBar,
    exit_reason: str,
) -> tuple[ExecutedTrade, Decimal, Decimal, Decimal, Decimal]:
    exit_fill = apply_exit_slippage(bar.close, strategy.costs.slippage_rate)
    exit_costs = calculate_trade_costs(
        price=exit_fill,
        quantity=position.quantity,
        costs=strategy.costs,
        is_exit=True,
    )
    gross_pnl = (exit_fill - position.entry_price) * position.quantity
    net_pnl = gross_pnl - position.entry_fee - exit_costs.fee - exit_costs.tax
    cash_delta = (exit_fill * position.quantity) - exit_costs.fee - exit_costs.tax
    trade = ExecutedTrade(
        instrument_id=position.instrument_id,
        entry_date=position.entry_date,
        exit_date=bar.trade_date,
        entry_price=position.entry_price,
        exit_price=exit_fill,
        quantity=position.quantity,
        gross_pnl=_q(gross_pnl),
        net_pnl=_q(net_pnl),
        fee_paid=_q(position.entry_fee + exit_costs.fee),
        tax_paid=exit_costs.tax,
        slippage_paid=_q(position.entry_slippage + exit_costs.slippage),
        holding_period_days=(bar.trade_date - position.entry_date).days,
        exit_reason=exit_reason,
    )
    return trade, cash_delta, exit_costs.fee, exit_costs.tax, exit_costs.slippage


def _indicator_values_for_instrument(
    indicator_map: dict[tuple[date, str, str, str, int], Decimal],
    instrument_id: int,
) -> dict[tuple[date, str, str, str], Decimal]:
    values: dict[tuple[date, str, str, str], Decimal] = {}
    for (trade_date_value, indicator_name, component, parameter_signature, value_instrument_id), value in indicator_map.items():
        if value_instrument_id != instrument_id:
            continue
        values[(trade_date_value, indicator_name, component, parameter_signature)] = value
    return values


def _price_values_for_bar(bar: DailyBar) -> dict[str, Decimal]:
    return {
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": Decimal(bar.volume),
    }


def _calculate_metrics(
    *,
    initial_cash: Decimal,
    final_cash: Decimal,
    equity_curve: list[EquityPoint],
) -> BacktestMetrics:
    if not equity_curve or initial_cash <= 0:
        return BacktestMetrics(
            sharpe_ratio=Decimal("0"),
            cagr_pct=Decimal("0"),
            max_drawdown_pct=Decimal("0"),
            score=Decimal("0"),
        )

    returns: list[Decimal] = []
    previous_equity: Decimal | None = None
    peak = equity_curve[0].equity
    max_drawdown_pct = Decimal("0")
    for point in equity_curve:
        if point.equity > peak:
            peak = point.equity
        if peak != 0:
            drawdown = ((peak - point.equity) / peak) * Decimal("100")
            if drawdown > max_drawdown_pct:
                max_drawdown_pct = drawdown
        if previous_equity is not None and previous_equity != 0:
            returns.append((point.equity - previous_equity) / previous_equity)
        previous_equity = point.equity

    if returns:
        mean_return = sum(returns, Decimal("0")) / Decimal(len(returns))
        variance = sum((value - mean_return) ** 2 for value in returns) / Decimal(len(returns))
        std_dev = variance.sqrt() if variance > 0 else Decimal("0")
        sharpe_ratio = _q(
            Decimal(str(sqrt(252))) * (mean_return / std_dev)
        ) if std_dev > 0 else Decimal("0")
    else:
        sharpe_ratio = Decimal("0")

    total_days = max((equity_curve[-1].trade_date - equity_curve[0].trade_date).days, 1)
    if final_cash > 0:
        cagr_float = ((float(final_cash / initial_cash) ** (365 / total_days)) - 1) * 100
        cagr_pct = _q(Decimal(str(cagr_float)))
    else:
        cagr_pct = Decimal("-100")
    max_drawdown_pct = _q(max_drawdown_pct)
    score = _q(sharpe_ratio + (cagr_pct / Decimal("100")) - (max_drawdown_pct / Decimal("100")))
    return BacktestMetrics(
        sharpe_ratio=sharpe_ratio,
        cagr_pct=cagr_pct,
        max_drawdown_pct=max_drawdown_pct,
        score=score,
    )


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"))
