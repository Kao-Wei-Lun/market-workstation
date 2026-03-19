from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

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
    notes: str | None = None


def execute_backtest(
    strategy: StrategyDefinition,
    *,
    bars: list[DailyBar],
    indicator_values: list[IndicatorValue],
) -> BacktestExecutionResult:
    started_at = datetime.now(tz=timezone.utc)
    cash = strategy.initial_cash
    open_position: dict | None = None
    trades: list[ExecutedTrade] = []
    total_fees = Decimal("0")
    total_taxes = Decimal("0")
    total_slippage = Decimal("0")
    indicator_map = {
        (item.trade_date, item.indicator_name, item.component, item.parameter_signature): item.value
        for item in indicator_values
    }

    for bar in bars:
        price_values = {
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": Decimal(bar.volume),
        }

        if open_position is None:
            should_enter = evaluate_rule(
                strategy.entry_rule,
                trade_date=bar.trade_date,
                price_values=price_values,
                indicator_values=indicator_map,
            )
            if should_enter:
                entry_fill = apply_entry_slippage(bar.close, strategy.costs.slippage_rate)
                quantity = int((cash * strategy.position_size) // entry_fill)
                if quantity > 0:
                    entry_costs = calculate_trade_costs(
                        price=entry_fill,
                        quantity=quantity,
                        costs=strategy.costs,
                        is_exit=False,
                    )
                    cash -= (entry_fill * quantity) + entry_costs.fee
                    total_fees += entry_costs.fee
                    total_slippage += entry_costs.slippage
                    open_position = {
                        "entry_date": bar.trade_date,
                        "entry_price": entry_fill,
                        "quantity": quantity,
                        "entry_fee": entry_costs.fee,
                        "entry_slippage": entry_costs.slippage,
                    }
            continue

        should_exit = evaluate_rule(
            strategy.exit_rule,
            trade_date=bar.trade_date,
            price_values=price_values,
            indicator_values=indicator_map,
        )
        is_last_bar = bar.trade_date == bars[-1].trade_date
        if should_exit or is_last_bar:
            exit_fill = apply_exit_slippage(bar.close, strategy.costs.slippage_rate)
            exit_costs = calculate_trade_costs(
                price=exit_fill,
                quantity=open_position["quantity"],
                costs=strategy.costs,
                is_exit=True,
            )
            gross_pnl = (exit_fill - open_position["entry_price"]) * open_position["quantity"]
            net_pnl = gross_pnl - open_position["entry_fee"] - exit_costs.fee - exit_costs.tax
            cash += (exit_fill * open_position["quantity"]) - exit_costs.fee - exit_costs.tax
            total_fees += exit_costs.fee
            total_taxes += exit_costs.tax
            total_slippage += exit_costs.slippage
            trades.append(
                ExecutedTrade(
                    instrument_id=strategy.instrument_id,
                    entry_date=open_position["entry_date"],
                    exit_date=bar.trade_date,
                    entry_price=open_position["entry_price"],
                    exit_price=exit_fill,
                    quantity=open_position["quantity"],
                    gross_pnl=_q(gross_pnl),
                    net_pnl=_q(net_pnl),
                    fee_paid=_q(open_position["entry_fee"] + exit_costs.fee),
                    tax_paid=exit_costs.tax,
                    slippage_paid=_q(open_position["entry_slippage"] + exit_costs.slippage),
                    holding_period_days=(bar.trade_date - open_position["entry_date"]).days,
                    exit_reason="forced_exit" if is_last_bar and not should_exit else "rule_exit",
                )
            )
            open_position = None

    finished_at = datetime.now(tz=timezone.utc)
    total_return = _q(cash - strategy.initial_cash)
    total_return_pct = (
        _q((total_return / strategy.initial_cash) * Decimal("100"))
        if strategy.initial_cash != 0
        else Decimal("0")
    )
    wins = sum(1 for trade in trades if trade.net_pnl > 0)
    win_rate = _q((Decimal(wins) / Decimal(len(trades))) * Decimal("100")) if trades else Decimal("0")
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
        trades=trades,
    )


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"))
