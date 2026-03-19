from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class NormalizedDailyBarRecord(BaseModel):
    instrument_id: int | None = None
    symbol: str
    market: str
    currency: str
    source_route: str
    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    turnover_value: Decimal | None = None
    transactions_count: int | None = None
    change: Decimal | None = None
    change_percent: Decimal | None = None

    model_config = ConfigDict(frozen=True)


class NormalizedSeriesPointRecord(BaseModel):
    instrument_id: int | None = None
    series_key: str
    source_route: str
    trade_date: date
    value: Decimal

    model_config = ConfigDict(frozen=True)


class NormalizedDataBatch(BaseModel):
    daily_bars: list[NormalizedDailyBarRecord] = Field(default_factory=list)
    series_points: list[NormalizedSeriesPointRecord] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class LoadResult(BaseModel):
    daily_bars_loaded: int = 0
    series_points_loaded: int = 0


class ValidationIssue(BaseModel):
    message: str


class ValidationResult(BaseModel):
    issues: list[ValidationIssue] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues
