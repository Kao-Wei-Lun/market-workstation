from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class BarDataPoint:
    trade_date: date
    close: Decimal
    high: Decimal
    low: Decimal
    volume: int


@dataclass(frozen=True)
class IndicatorOutput:
    trade_date: date
    indicator_name: str
    component: str
    parameter_signature: str
    value: Decimal


@dataclass(frozen=True)
class PersistedIndicatorValue(IndicatorOutput):
    instrument_id: int


class IndicatorCalculator(Protocol):
    name: str

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        ...
