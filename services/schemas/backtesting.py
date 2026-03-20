from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OperandDefinition(BaseModel):
    kind: Literal["price", "indicator", "constant", "parameter"]
    field: str | None = None
    indicator_name: str | None = None
    component: str | None = None
    parameter_signature: str | None = None
    value: Decimal | None = None
    parameter_name: str | None = None

    @model_validator(mode="after")
    def validate_operand(self) -> "OperandDefinition":
        if self.kind == "price" and self.field is None:
            raise ValueError("price operand requires field")
        if self.kind == "indicator" and (
            self.indicator_name is None or self.component is None or self.parameter_signature is None
        ):
            raise ValueError("indicator operand requires indicator_name, component, and parameter_signature")
        if self.kind == "constant" and self.value is None:
            raise ValueError("constant operand requires value")
        if self.kind == "parameter" and self.parameter_name is None:
            raise ValueError("parameter operand requires parameter_name")
        return self


class RuleDefinition(BaseModel):
    all: list["RuleDefinition"] | None = None
    any: list["RuleDefinition"] | None = None
    left: OperandDefinition | None = None
    operator: Literal["gt", "gte", "lt", "lte", "eq", "neq"] | None = None
    right: OperandDefinition | None = None

    @model_validator(mode="after")
    def validate_rule(self) -> "RuleDefinition":
        composite_count = sum(value is not None for value in [self.all, self.any])
        leaf = self.left is not None or self.operator is not None or self.right is not None
        if composite_count > 1:
            raise ValueError("rule can only define one of all/any")
        if composite_count == 1 and leaf:
            raise ValueError("composite rule cannot also define leaf condition")
        if composite_count == 0:
            if self.left is None or self.operator is None or self.right is None:
                raise ValueError("leaf rule requires left, operator, and right")
        return self


RuleDefinition.model_rebuild()


class UniverseFilterDefinition(BaseModel):
    instrument_ids: list[int] = Field(default_factory=list)
    required_tags: list[str] = Field(default_factory=list)
    watchlist_id: int | None = None
    market: str | None = None
    asset_type: str | None = None

    @model_validator(mode="after")
    def normalize_filters(self) -> "UniverseFilterDefinition":
        self.required_tags = sorted({tag.strip().lower() for tag in self.required_tags if tag.strip()})
        return self


class CostModelDefinition(BaseModel):
    fee_rate: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")
    slippage_rate: Decimal = Decimal("0")


class StrategyDefinition(BaseModel):
    instrument_id: int | None = None
    initial_cash: Decimal = Decimal("100000")
    position_size: Decimal = Decimal("1")
    entry_rule: RuleDefinition
    exit_rule: RuleDefinition
    universe: UniverseFilterDefinition | None = None
    max_concurrent_positions: int = 1
    rebalance_interval_days: int | None = None
    stop_loss_pct: Decimal | None = None
    take_profit_pct: Decimal | None = None
    time_exit_days: int | None = None
    costs: CostModelDefinition = Field(default_factory=CostModelDefinition)

    @model_validator(mode="after")
    def validate_strategy(self) -> "StrategyDefinition":
        if self.position_size <= 0 or self.position_size > 1:
            raise ValueError("position_size must be within (0, 1]")
        if self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if self.instrument_id is None and self.universe is None:
            raise ValueError("strategy requires instrument_id or universe")
        if self.max_concurrent_positions <= 0:
            raise ValueError("max_concurrent_positions must be positive")
        if self.rebalance_interval_days is not None and self.rebalance_interval_days <= 0:
            raise ValueError("rebalance_interval_days must be positive")
        if self.stop_loss_pct is not None and self.stop_loss_pct <= 0:
            raise ValueError("stop_loss_pct must be positive")
        if self.take_profit_pct is not None and self.take_profit_pct <= 0:
            raise ValueError("take_profit_pct must be positive")
        if self.time_exit_days is not None and self.time_exit_days <= 0:
            raise ValueError("time_exit_days must be positive")
        return self


class StrategyCreate(BaseModel):
    instrument_id: int | None = None
    name: str
    description: str | None = None
    definition_json: dict[str, Any]


class StrategyRead(StrategyCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BacktestTradeRead(BaseModel):
    id: int
    run_id: int
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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BacktestRunRead(BaseModel):
    id: int
    strategy_id: int
    status: str
    initial_cash: Decimal
    final_cash: Decimal
    total_return: Decimal
    total_return_pct: Decimal
    total_trades: int
    win_rate: Decimal
    fee_paid: Decimal
    tax_paid: Decimal
    slippage_paid: Decimal
    resolved_parameters_json: dict[str, Any]
    metrics_json: dict[str, Any]
    notes: str | None = None
    started_at: datetime
    finished_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BacktestCreateRequest(BaseModel):
    name: str
    description: str | None = None
    definition: StrategyDefinition
    parameters: dict[str, Decimal] = Field(default_factory=dict)


class BacktestCreateResponse(BaseModel):
    strategy: StrategyRead
    run: BacktestRunRead
    trades: list[BacktestTradeRead]


class BacktestParameterSearchRequest(BaseModel):
    name: str
    description: str | None = None
    definition: StrategyDefinition
    parameter_space: dict[str, list[Decimal]]
    ranking_metric: Literal["score", "sharpe", "cagr", "max_drawdown"] = "score"

    @model_validator(mode="after")
    def validate_parameter_space(self) -> "BacktestParameterSearchRequest":
        if not self.parameter_space:
            raise ValueError("parameter_space is required")
        for values in self.parameter_space.values():
            if not values:
                raise ValueError("parameter_space values must not be empty")
        return self


class BacktestSearchResultRead(BaseModel):
    id: int
    search_run_id: int
    backtest_run_id: int
    parameter_set_json: dict[str, Any]
    metrics_json: dict[str, Any]
    ranking_score: Decimal
    rank: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BacktestSearchRunRead(BaseModel):
    id: int
    strategy_id: int
    status: str
    ranking_metric: str
    parameter_space_json: dict[str, Any]
    best_parameters_json: dict[str, Any]
    summary_json: dict[str, Any]
    started_at: datetime
    finished_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BacktestSearchResponse(BaseModel):
    strategy: StrategyRead
    search_run: BacktestSearchRunRead
    results: list[BacktestSearchResultRead]


class BacktestWalkForwardRequest(BaseModel):
    name: str
    description: str | None = None
    definition: StrategyDefinition
    parameter_space: dict[str, list[Decimal]]
    ranking_metric: Literal["score", "sharpe", "cagr", "max_drawdown"] = "score"
    train_window_days: int
    test_window_days: int
    step_days: int | None = None

    @model_validator(mode="after")
    def validate_walk_forward(self) -> "BacktestWalkForwardRequest":
        if not self.parameter_space:
            raise ValueError("parameter_space is required")
        if self.train_window_days <= 0 or self.test_window_days <= 0:
            raise ValueError("train_window_days and test_window_days must be positive")
        if self.step_days is not None and self.step_days <= 0:
            raise ValueError("step_days must be positive")
        return self


class BacktestWalkForwardWindowRead(BaseModel):
    id: int
    walk_forward_run_id: int
    backtest_run_id: int
    window_index: int
    train_start_date: date
    train_end_date: date
    test_start_date: date
    test_end_date: date
    selected_parameters_json: dict[str, Any]
    train_metrics_json: dict[str, Any]
    test_metrics_json: dict[str, Any]
    ranking_score: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BacktestWalkForwardRunRead(BaseModel):
    id: int
    strategy_id: int
    status: str
    ranking_metric: str
    parameter_space_json: dict[str, Any]
    summary_json: dict[str, Any]
    train_window_days: int
    test_window_days: int
    step_days: int
    started_at: datetime
    finished_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BacktestWalkForwardResponse(BaseModel):
    strategy: StrategyRead
    walk_forward_run: BacktestWalkForwardRunRead
    windows: list[BacktestWalkForwardWindowRead]
