from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OperandDefinition(BaseModel):
    kind: Literal["price", "indicator", "constant"]
    field: str | None = None
    indicator_name: str | None = None
    component: str | None = None
    parameter_signature: str | None = None
    value: Decimal | None = None

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


class CostModelDefinition(BaseModel):
    fee_rate: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")
    slippage_rate: Decimal = Decimal("0")


class StrategyDefinition(BaseModel):
    instrument_id: int
    initial_cash: Decimal = Decimal("100000")
    position_size: Decimal = Decimal("1")
    entry_rule: RuleDefinition
    exit_rule: RuleDefinition
    costs: CostModelDefinition = Field(default_factory=CostModelDefinition)

    @model_validator(mode="after")
    def validate_strategy(self) -> "StrategyDefinition":
        if self.position_size <= 0 or self.position_size > 1:
            raise ValueError("position_size must be within (0, 1]")
        if self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        return self


class StrategyCreate(BaseModel):
    instrument_id: int
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
    notes: str | None = None
    started_at: datetime
    finished_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BacktestCreateRequest(BaseModel):
    name: str
    description: str | None = None
    definition: StrategyDefinition


class BacktestCreateResponse(BaseModel):
    strategy: StrategyRead
    run: BacktestRunRead
    trades: list[BacktestTradeRead]
