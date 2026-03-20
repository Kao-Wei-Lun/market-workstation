from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InstrumentTagCreate(BaseModel):
    tag: str


class InstrumentTagRead(BaseModel):
    id: int
    instrument_id: int
    tag: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistCreate(BaseModel):
    name: str
    description: str | None = None


class WatchlistRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistItemRead(BaseModel):
    id: int
    watchlist_id: int
    instrument_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AutoClassificationCondition(BaseModel):
    field: Literal["market", "asset_type", "symbol", "name", "tag"]
    operator: Literal["equals", "starts_with", "ends_with", "contains", "has"]
    value: str

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be empty")
        return normalized

    @model_validator(mode="after")
    def validate_operator_for_field(self) -> Self:
        allowed_operators = {
            "market": {"equals"},
            "asset_type": {"equals"},
            "symbol": {"equals", "starts_with", "ends_with", "contains"},
            "name": {"equals", "contains"},
            "tag": {"has"},
        }
        if self.operator not in allowed_operators[self.field]:
            raise ValueError(f"operator '{self.operator}' is not supported for field '{self.field}'")
        return self


class AutoClassificationExpression(BaseModel):
    all: list["AutoClassificationExpression"] | None = None
    any: list["AutoClassificationExpression"] | None = None
    condition: AutoClassificationCondition | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> Self:
        branch_count = sum(
            [
                int(self.all is not None),
                int(self.any is not None),
                int(self.condition is not None),
            ]
        )
        if branch_count != 1:
            raise ValueError("exactly one of 'all', 'any', or 'condition' must be provided")
        if self.all is not None and not self.all:
            raise ValueError("'all' must contain at least one expression")
        if self.any is not None and not self.any:
            raise ValueError("'any' must contain at least one expression")
        return self


AutoClassificationExpression.model_rebuild()


class AutoClassificationRuleCreate(BaseModel):
    name: str
    description: str | None = None
    target_tag: str
    definition: AutoClassificationExpression
    is_active: bool = True

    @field_validator("name", "target_tag")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be empty")
        return normalized


class AutoClassificationRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    target_tag: str | None = None
    definition: AutoClassificationExpression | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_update_payload(self) -> Self:
        if (
            self.name is None
            and self.description is None
            and self.target_tag is None
            and self.definition is None
            and self.is_active is None
        ):
            raise ValueError("at least one field must be provided")
        return self


class AutoClassificationRuleRead(BaseModel):
    id: int
    name: str
    description: str | None
    target_tag: str
    definition: AutoClassificationExpression
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AutoClassificationRuleEvaluationRequest(BaseModel):
    rule_id: int | None = None


class AutoClassificationRuleEvaluationRead(BaseModel):
    rules_evaluated: int
    instruments_evaluated: int
    matches_found: int
    tags_added: int


class GroupMemberChange(BaseModel):
    instrument_id: int
    symbol: str
    close_change_pct: Decimal


class GroupScannerFlagConditions(BaseModel):
    min_close_change_pct: Decimal | None = Decimal("2")
    min_volume_ratio: Decimal | None = Decimal("1.5")
    require_above_sma: bool = False
    match_mode: Literal["all", "any"] = "any"


class GroupScannerFlaggedInstrument(BaseModel):
    instrument_id: int
    symbol: str
    close_change_pct: Decimal
    volume_ratio: Decimal | None = None
    above_sma: bool | None = None
    reasons: list[str] = Field(default_factory=list)


class GroupScannerRequest(BaseModel):
    trade_date: date
    tag: str | None = None
    watchlist_id: int | None = None
    sma_parameter_signature: str = "period=20"
    volume_lookback_days: int = 20
    flag_conditions: GroupScannerFlagConditions = Field(default_factory=GroupScannerFlagConditions)

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        if (self.tag is None) == (self.watchlist_id is None):
            raise ValueError("exactly one of 'tag' or 'watchlist_id' must be provided")
        if self.volume_lookback_days < 1:
            raise ValueError("volume_lookback_days must be at least 1")
        return self


class GroupScannerRead(BaseModel):
    member_count: int
    average_daily_return_pct: Decimal
    top_gainers: list[GroupMemberChange]
    top_losers: list[GroupMemberChange]
    average_volume_ratio: Decimal | None = None
    percentage_above_sma: Decimal | None = None
    flagged_instruments: list[GroupScannerFlaggedInstrument]


class GroupSummaryRead(BaseModel):
    member_count: int
    average_close_change_pct: Decimal
    top_gainers: list[GroupMemberChange]
    top_losers: list[GroupMemberChange]
    percentage_above_sma: Decimal
